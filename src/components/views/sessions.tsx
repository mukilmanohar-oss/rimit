'use client';

import { useEffect, useState } from 'react';
import { rules, type IntakeSession, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';

export function SessionsView({ profile }: { profile: UserProfile }) {
  const [sessions, setSessions] = useState<IntakeSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await rules.listIntakeSessions();
        setSessions(data.results);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load sessions');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <PageHeader
        title="Intake Sessions"
        subtitle="Enrollment windows with Session Enforcement Matrix"
      />

      {/* Session Enforcement Matrix callout */}
      <div className="bg-amber-50 border border-amber-200 rounded-md p-4 mb-6">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
            <span className="text-amber-700 text-sm">⚠</span>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-amber-900">Active Rule: block_fresh_july</h3>
            <p className="text-xs text-amber-800 mt-1">
              Fresh candidates (no prior enrollments) cannot enroll in July session. They are automatically
              routed to the October intake. This rule is enforced programmatically via the
              <code className="bg-amber-100 px-1 mx-1 rounded">rules_configurations</code> table.
            </p>
          </div>
        </div>
      </div>

      {sessions.length === 0 ? <EmptyState message="No intake sessions configured" /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map(s => (
            <div key={s.id} className="bg-card border border-border rounded-lg p-5">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-foreground">{s.session_name}</h3>
                <StatusBadge status={s.is_active ? 'active' : 'suspended'} />
              </div>
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-xs text-muted-foreground">Start date</dt>
                  <dd className="font-medium text-foreground">{new Date(s.start_date).toLocaleDateString('en-IN')}</dd>
                </div>
                {s.end_date && (
                  <div>
                    <dt className="text-xs text-muted-foreground">End date</dt>
                    <dd className="font-medium text-foreground">{new Date(s.end_date).toLocaleDateString('en-IN')}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-xs text-muted-foreground">Fresh candidates</dt>
                  <dd>
                    {s.is_fresh_allowed ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-emerald-50 text-emerald-700 border-emerald-200">
                        Allowed
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-amber-50 text-amber-700 border-amber-200">
                        Blocked
                      </span>
                    )}
                  </dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
