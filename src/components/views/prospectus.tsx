'use client';

import { useEffect, useState } from 'react';
import { aggregator, DEFAULT_PAGE_SIZE, withPaging, hasNextPage, hasPrevPage, type University, type UniversityDoc, type UserProfile, type Course } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState } from '../rimit-shell';
import { toast } from 'sonner';

export function ProspectusView({ profile }: { profile: UserProfile }) {
  const [docs, setDocs] = useState<UniversityDoc[]>([]);
  const [universities, setUniversities] = useState<University[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [canNext, setCanNext] = useState(false);
  const [canPrev, setCanPrev] = useState(false);
  
  // Filters
  const [uniFilter, setUniFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');

  // Modals / Form
  const [showForm, setShowForm] = useState(false);
  const [editingDoc, setEditingDoc] = useState<UniversityDoc | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [form, setForm] = useState({
    university: '',
    course: '',
    doc_type: 'prospectus',
    title: '',
    s3_object_uri: '',
    file_size_bytes: 1048576, // Default 1MB
    mime_type: 'application/pdf',
    is_public: true,
  });

  const isSuperAdmin = profile.role === 'super_admin';

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (uniFilter) params.university = uniFilter;
      if (typeFilter) params.doc_type = typeFilter;
      if (search) params.search = search;

      const [docsData, unisData] = await Promise.all([
        aggregator.listProspectus(withPaging(params, { page, pageSize: DEFAULT_PAGE_SIZE })),
        aggregator.listUniversities({ is_active: 'true', page_size: '200' }),
      ]);

      setDocs(docsData.results);
      setTotalCount(docsData.count || 0);
      setCanNext(hasNextPage(docsData));
      setCanPrev(hasPrevPage(docsData));
      setUniversities(unisData.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [uniFilter, typeFilter, search, page]);

  // Load courses for selected university when editing/uploading
  useEffect(() => {
    if (!showForm || !form.university) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCourses([]);
      return;
    }
    (async () => {
      try {
        const results: Course[] = [];
        let nextPage = 1;
        for (let i = 0; i < 5; i++) {
          const data = await aggregator.listCourses({ university: form.university, page: String(nextPage), page_size: '200' });
          results.push(...(data.results || []));
          if (!data.next) break;
          nextPage += 1;
        }
        setCourses(results);
      } catch {
        setCourses([]);
      }
    })();
  }, [showForm, form.university]);

  const handleDownload = async (doc: UniversityDoc) => {
    try {
      const data = await aggregator.downloadDoc(doc.id);
      window.open(data.url, '_blank');
      toast.success(`Downloading ${doc.title}`);
    } catch (err) {
      toast.error('Failed to get download link');
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        course: form.course || null,
      };
      if (editingDoc) {
        await aggregator.updateProspectus(editingDoc.id, payload);
        toast.success('Document updated successfully');
      } else {
        await aggregator.createProspectus(payload);
        toast.success('Document uploaded successfully');
      }
      setShowForm(false);
      setEditingDoc(null);
      setForm({
        university: '',
        course: '',
        doc_type: 'prospectus',
        title: '',
        s3_object_uri: '',
        file_size_bytes: 1048576,
        mime_type: 'application/pdf',
        is_public: true,
      });
      load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save document');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (doc: UniversityDoc) => {
    setEditingDoc(doc);
    setForm({
      university: doc.university,
      course: doc.course || '',
      doc_type: doc.doc_type,
      title: doc.title,
      s3_object_uri: doc.s3_object_uri,
      file_size_bytes: doc.file_size_bytes || 1048576,
      mime_type: doc.mime_type,
      is_public: doc.is_public,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await aggregator.deleteProspectus(id);
      toast.success('Document deleted');
      load();
    } catch (err) {
      toast.error('Failed to delete document');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const mockUri = `s3://rimit-prospectus-vault/${Date.now()}_${file.name}`;
      setForm(prev => ({
        ...prev,
        title: prev.title || file.name.replace(/\.[^/.]+$/, ""),
        s3_object_uri: mockUri,
        file_size_bytes: file.size,
        mime_type: file.type || 'application/pdf',
      }));
    }
  };

  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getDocTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      prospectus: 'Prospectus',
      calendar: 'Academic Calendar',
      syllabus: 'Syllabus',
      notification: 'Official Notification',
    };
    return labels[type] || type;
  };

  if (loading && docs.length === 0) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Digital Prospectus Library"
        subtitle="Access and manage academic calendars, syllabi, and official prospectuses"
        action={
          isSuperAdmin && (
            <button
              onClick={() => {
                setEditingDoc(null);
                setForm({
                  university: '',
                  course: '',
                  doc_type: 'prospectus',
                  title: '',
                  s3_object_uri: '',
                  file_size_bytes: 1048576,
                  mime_type: 'application/pdf',
                  is_public: true,
                });
                setShowForm(true);
              }}
              className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90 transition"
            >
              + Upload Document
            </button>
          )
        }
      />

      {/* Filter Bar */}
      <div className="bg-card border border-border rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-sm">
        <div className="flex flex-wrap gap-3 w-full md:w-auto">
          <input
            type="text"
            placeholder="Search documents..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-md border border-input bg-background text-sm min-w-[200px]"
          />
          <select
            value={uniFilter}
            onChange={e => { setUniFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-md border border-input bg-background text-sm min-w-[180px]"
          >
            <option value="">All Universities</option>
            {universities.map(u => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
          <select
            value={typeFilter}
            onChange={e => { setTypeFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-md border border-input bg-background text-sm"
          >
            <option value="">All Document Types</option>
            <option value="prospectus">Prospectus</option>
            <option value="calendar">Academic Calendar</option>
            <option value="syllabus">Syllabus</option>
            <option value="notification">Official Notification</option>
          </select>
        </div>
      </div>

      {error && <ErrorState message={error} />}

      {docs.length === 0 ? (
        <EmptyState message="No documents found matching filters" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {docs.map(doc => (
            <div
              key={doc.id}
              className="bg-card border border-border rounded-xl p-5 hover:shadow-md transition flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <span className="bg-primary/10 text-primary px-2.5 py-0.5 rounded-full text-xs font-semibold">
                    {getDocTypeLabel(doc.doc_type)}
                  </span>
                  {!doc.is_public && (
                    <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-[10px] font-medium">
                      Private
                    </span>
                  )}
                </div>

                <div>
                  <h4 className="font-bold text-foreground text-base line-clamp-1">{doc.title}</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {doc.university_name || 'Partner University'}
                    {doc.course_name ? ` • ${doc.course_name}` : ''}
                  </p>
                </div>

                <div className="text-xs text-muted-foreground space-y-1 bg-muted/30 p-2.5 rounded-md">
                  <div>Size: <span className="font-medium text-foreground">{formatBytes(doc.file_size_bytes || 0)}</span></div>
                  <div className="truncate">URI: <span className="font-mono text-[10px] text-foreground">{doc.s3_object_uri}</span></div>
                </div>
              </div>

              <div className="flex justify-between items-center mt-5 pt-4 border-t border-border">
                <button
                  onClick={() => handleDownload(doc)}
                  className="text-primary hover:underline text-sm font-semibold flex items-center gap-1.5"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Download
                </button>

                {isSuperAdmin && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(doc)}
                      className="text-muted-foreground hover:text-foreground text-xs font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-destructive hover:text-destructive/90 text-xs font-medium"
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {docs.length > 0 && (
        <div className="flex items-center justify-between py-2">
          <span className="text-xs text-muted-foreground">
            Page {page} of {Math.max(1, Math.ceil(totalCount / DEFAULT_PAGE_SIZE))} (Total {totalCount} records)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={!canPrev || page === 1}
              className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={!canNext}
              className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Upload/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card w-full max-w-md rounded-xl shadow-lg border border-border overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex justify-between items-center">
              <h3 className="font-semibold text-lg">{editingDoc ? 'Edit Document Details' : 'Upload Document to Vault'}</h3>
              <button
                onClick={() => {
                  setShowForm(false);
                  setEditingDoc(null);
                }}
                className="text-muted-foreground hover:text-foreground"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
            </div>

            <form onSubmit={handleSave} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">University *</label>
                <select
                  value={form.university}
                  onChange={e => setForm(prev => ({ ...prev, university: e.target.value }))}
                  required
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                >
                  <option value="">Select University</option>
                  {universities.map(u => (
                    <option key={u.id} value={u.id}>{u.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Course (Optional)</label>
                <select
                  value={form.course}
                  onChange={e => setForm(prev => ({ ...prev, course: e.target.value }))}
                  disabled={!form.university}
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm disabled:opacity-60"
                >
                  <option value="">— No course mapping —</option>
                  {courses.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                <p className="text-[11px] text-muted-foreground mt-1">
                  If set, this document will show up as a course-specific prospectus.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Doc Type *</label>
                  <select
                    value={form.doc_type}
                    onChange={e => setForm(prev => ({ ...prev, doc_type: e.target.value }))}
                    required
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  >
                    <option value="prospectus">Prospectus</option>
                    <option value="calendar">Academic Calendar</option>
                    <option value="syllabus">Syllabus</option>
                    <option value="notification">Notification</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Visibility</label>
                  <select
                    value={form.is_public ? 'true' : 'false'}
                    onChange={e => setForm(prev => ({ ...prev, is_public: e.target.value === 'true' }))}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  >
                    <option value="true">Public</option>
                    <option value="false">Private</option>
                  </select>
                </div>
              </div>

              {!editingDoc && (
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">File Upload *</label>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileChange}
                    required={!editingDoc}
                    className="w-full text-xs text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Title *</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={e => setForm(prev => ({ ...prev, title: e.target.value }))}
                  required
                  placeholder="E.g., Syllabus 2026"
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">S3 Object URI *</label>
                <input
                  type="text"
                  value={form.s3_object_uri}
                  onChange={e => setForm(prev => ({ ...prev, s3_object_uri: e.target.value }))}
                  required
                  placeholder="Auto-generated or enter manually"
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-xs font-mono"
                />
              </div>

              <div className="pt-4 flex justify-end gap-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingDoc(null);
                  }}
                  className="px-4 py-2 text-sm font-medium rounded-md hover:bg-muted text-foreground"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !form.university || !form.title || !form.s3_object_uri}
                  className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : editingDoc ? 'Update Details' : 'Upload Document'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
