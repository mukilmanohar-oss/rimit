'use client';

import { useEffect, useState } from 'react';
import { aggregator, type University, type Course } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState } from '../rimit-shell';

export function UniversitiesView() {
  const [universities, setUniversities] = useState<University[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<University | null>(null);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (stateFilter) params.state = stateFilter;
      const data = await aggregator.listUniversities(params);
      setUniversities(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load universities');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  if (selected) {
    return <UniversityDetail university={selected} onBack={() => setSelected(null)} />;
  }

  return (
    <div>
      <PageHeader
        title="University Directory"
        subtitle="Browse partner universities across India"
      />

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search by name, accreditation…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load()}
          className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <input
          type="text"
          placeholder="State"
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load()}
          className="w-40 px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          onClick={load}
          className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          Search
        </button>
      </div>

      {universities.length === 0 ? (
        <EmptyState message="No universities found" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {universities.map(u => (
            <button
              key={u.id}
              onClick={() => setSelected(u)}
              className="text-left bg-card border border-border rounded-lg p-5 hover:border-primary hover:shadow-sm transition"
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-foreground">{u.name}</h3>
                {u.accreditation && (
                  <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded">
                    {u.accreditation}
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground mb-3">{u.state}</p>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  {u.course_count ?? 0} courses
                </span>
                <span className="text-primary font-medium">View →</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function UniversityDetail({ university, onBack }: { university: University; onBack: () => void }) {
  const [detail, setDetail] = useState<University | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const d = await aggregator.getUniversity(university.id);
        setDetail(d);
      } catch (e) {
        setDetail(university);
      } finally {
        setLoading(false);
      }
    })();
  }, [university.id]);

  if (loading || !detail) return <LoadingState />;

  return (
    <div>
      <button onClick={onBack} className="text-sm text-primary mb-4 hover:underline">
        ← Back to universities
      </button>
      <PageHeader title={detail.name} subtitle={`${detail.state} · ${detail.accreditation || 'Not accredited'}`} />

      {detail.description && <p className="text-sm text-muted-foreground mb-6">{detail.description}</p>}

      <h2 className="text-lg font-semibold mb-3">Courses ({detail.courses?.length ?? 0})</h2>
      {detail.courses && detail.courses.length > 0 ? (
        <div className="space-y-3 mb-8">
          {detail.courses.map(c => (
            <div key={c.id} className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-foreground">{c.name}</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    {c.stream} · {c.duration_months} months
                  </p>
                  {c.eligibility_text && (
                    <p className="text-xs text-muted-foreground mt-1">Eligibility: {c.eligibility_text}</p>
                  )}
                </div>
                {c.fees && c.fees.length > 0 && (
                  <div className="text-right">
                    {c.fees.map(f => (
                      <p key={f.id} className="text-sm">
                        <span className="text-muted-foreground">{f.fee_type}:</span>{' '}
                        <span className="font-medium">₹{parseFloat(f.amount).toLocaleString('en-IN')}</span>
                      </p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState message="No courses available" />
      )}

      {detail.documents && detail.documents.length > 0 && (
        <>
          <h2 className="text-lg font-semibold mb-3">Documents ({detail.documents.length})</h2>
          <div className="space-y-2">
            {detail.documents.map(d => (
              <div key={d.id} className="bg-card border border-border rounded-lg p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground text-sm">{d.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{d.doc_type} · {d.mime_type}</p>
                </div>
                <button
                  onClick={async () => {
                    const r = await aggregator.downloadDoc(d.id);
                    window.open(r.url, '_blank');
                  }}
                  className="text-sm text-primary hover:underline"
                >
                  Download
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
