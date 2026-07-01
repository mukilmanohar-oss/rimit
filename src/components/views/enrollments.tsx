'use client';

import { useEffect, useState } from 'react';
import { admissions, aggregator, rules, type Enrollment, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';

export function EnrollmentsView({ profile }: { profile: UserProfile }) {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [selected, setSelected] = useState<Enrollment | null>(null);

  const canCreate = profile.role === 'counselor' || profile.role === 'academic_head' || profile.role === 'super_admin';

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      const data = await admissions.listEnrollments(params);
      setEnrollments(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load enrollments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  if (showForm) {
    return <EnrollmentCreateForm onBack={() => { setShowForm(false); load(); }} onCancel={() => setShowForm(false)} />;
  }

  if (selected) {
    return <EnrollmentDetail enrollment={selected} onBack={() => { setSelected(null); load(); }} />;
  }

  return (
    <div>
      <PageHeader
        title="Enrollments"
        subtitle="Student enrollment tracking with status workflow"
        action={canCreate && (
          <button
            onClick={() => setShowForm(true)}
            className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
          >
            + New Enrollment
          </button>
        )}
      />

      <div className="flex gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 rounded-md border border-input bg-background text-sm"
        >
          <option value="">All statuses</option>
          <option value="Applied">Applied</option>
          <option value="Document Verified">Document Verified</option>
          <option value="Fee Pending">Fee Pending</option>
          <option value="Fee Paid">Fee Paid</option>
          <option value="Enrolled">Enrolled</option>
          <option value="Enrollment Generated">Enrollment Generated</option>
          <option value="Cancelled">Cancelled</option>
        </select>
        <button
          onClick={load}
          className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          Apply
        </button>
      </div>

      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> :
        enrollments.length === 0 ? <EmptyState message="No enrollments found" /> : (
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 border-b border-border">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Student</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Course</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Session</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Created</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {enrollments.map(e => (
                  <tr
                    key={e.id}
                    className="hover:bg-muted/20 cursor-pointer"
                    onClick={() => setSelected(e)}
                  >
                    <td className="px-4 py-3 font-medium text-foreground">{e.student_name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{e.course_name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{e.session_name}</td>
                    <td className="px-4 py-3"><StatusBadge status={e.status} /></td>
                    <td className="px-4 py-3 text-muted-foreground">{new Date(e.created_at).toLocaleDateString('en-IN')}</td>
                    <td className="px-4 py-3 text-primary text-xs">View →</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    </div>
  );
}

function EnrollmentDetail({ enrollment, onBack }: { enrollment: Enrollment; onBack: () => void }) {
  const [detail, setDetail] = useState<Enrollment>(enrollment);
  const [transitioning, setTransitioning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const transition = async (newStatus: string) => {
    setTransitioning(true);
    setError(null);
    try {
      const updated = await admissions.transitionStatus(detail.id, newStatus);
      setDetail(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transition failed');
    } finally {
      setTransitioning(false);
    }
  };

  return (
    <div>
      <button onClick={onBack} className="text-sm text-primary mb-4 hover:underline">
        ← Back to enrollments
      </button>
      <PageHeader title="Enrollment Detail" subtitle={detail.enrollment_number || `ID: ${detail.id.slice(0, 8)}`} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Enrollment Info</h3>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-xs text-muted-foreground">Student</dt>
                <dd className="font-medium text-foreground">{detail.student_name}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Course</dt>
                <dd className="font-medium text-foreground">{detail.course_name}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">University</dt>
                <dd className="font-medium text-foreground">{detail.university_name || '—'}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Intake Session</dt>
                <dd className="font-medium text-foreground">{detail.session_name}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Current Status</dt>
                <dd><StatusBadge status={detail.status} /></dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Created</dt>
                <dd className="font-medium text-foreground">{new Date(detail.created_at).toLocaleString('en-IN')}</dd>
              </div>
            </dl>
            {detail.notes && (
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-xs text-muted-foreground mb-1">Notes</p>
                <p className="text-sm text-foreground whitespace-pre-wrap">{detail.notes}</p>
              </div>
            )}
          </div>

          {error && <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive">{error}</div>}
        </div>

        <div className="space-y-4">
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Status Workflow</h3>
            <div className="space-y-2">
              {/* Status flow visualization */}
              {['Applied', 'Document Verified', 'Fee Pending', 'Fee Paid', 'Enrolled', 'Enrollment Generated'].map(s => {
                const isCurrent = detail.status === s;
                const isPast = ['Applied', 'Document Verified', 'Fee Pending', 'Fee Paid', 'Enrolled', 'Enrollment Generated'].indexOf(s) <
                  ['Applied', 'Document Verified', 'Fee Pending', 'Fee Paid', 'Enrolled', 'Enrollment Generated'].indexOf(detail.status);
                return (
                  <div
                    key={s}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm ${
                      isCurrent ? 'bg-primary/10 border border-primary/30 font-medium' :
                      isPast ? 'text-muted-foreground' : 'text-muted-foreground/60'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${isCurrent ? 'bg-primary' : isPast ? 'bg-emerald-500' : 'bg-muted-foreground/30'}`} />
                    {s}
                  </div>
                );
              })}
            </div>

            {detail.next_valid_statuses && detail.next_valid_statuses.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border space-y-2">
                <p className="text-xs text-muted-foreground">Available transitions:</p>
                {detail.next_valid_statuses.map(s => (
                  <button
                    key={s}
                    onClick={() => transition(s)}
                    disabled={transitioning}
                    className="w-full text-left bg-primary text-primary-foreground rounded-md px-3 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                  >
                    → {s}
                  </button>
                ))}
                {detail.next_valid_statuses.includes('Cancelled') && (
                  <button
                    onClick={() => transition('Cancelled')}
                    disabled={transitioning}
                    className="w-full text-left bg-destructive text-white rounded-md px-3 py-2 text-sm font-medium hover:bg-destructive/90 disabled:opacity-50"
                  >
                    × Cancel Enrollment
                  </button>
                )}
              </div>
            )}
            {detail.status === 'Cancelled' && (
              <p className="mt-3 text-xs text-destructive">Enrollment is cancelled (terminal state).</p>
            )}
            {detail.status === 'Enrollment Generated' && (
              <p className="mt-3 text-xs text-emerald-600">Enrollment completed (terminal state).</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function EnrollmentCreateForm({ onBack, onCancel }: { onBack: () => void; onCancel: () => void }) {
  const [students, setStudents] = useState<Array<{ id: string; full_name: string; primary_phone: string }>>([]);
  const [courses, setCourses] = useState<Array<{ id: string; name: string; university_name?: string }>>([]);
  const [sessions, setSessions] = useState<Array<{ id: string; session_name: string; is_fresh_allowed: boolean }>>([]);
  const [form, setForm] = useState({ student: '', course: '', session: '' });
  const [validation, setValidation] = useState<{ valid: boolean; reason?: string; suggested?: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [s, c, sess] = await Promise.all([
          admissions.listStudents(),
          aggregator.listCourses(),
          rules.listIntakeSessions({ is_active: 'True' }),
        ]);
        setStudents(s.results);
        setCourses(c.results);
        setSessions(sess.results);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load form data');
      }
    })();
  }, []);

  const preflight = async () => {
    if (!form.student || !form.course || !form.session) return;
    try {
      const r = await rules.validateEnrollment(form.student, form.course, form.session);
      setValidation({ valid: r.valid, reason: r.reason, suggested: r.suggested_session_id || undefined });
    } catch (e) {
      // ignore pre-flight errors
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await admissions.createEnrollment(form);
      setTimeout(() => onBack(), 800);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Enrollment creation failed';
      // DRF returns field errors as JSON: {"session":["reason..."],"suggested_session":["uuid"]}
      try {
        const parsed = JSON.parse(msg);
        if (parsed.session) {
          setError(parsed.session[0] || parsed.session);
        } else if (parsed.detail) {
          setError(parsed.detail);
        } else {
          setError(msg);
        }
      } catch {
        setError(msg);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <button onClick={onCancel} className="text-sm text-primary mb-4 hover:underline">← Back to enrollments</button>
      <PageHeader title="Create New Enrollment" subtitle="Session Enforcement Matrix will validate eligibility" />

      {error && <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-lg p-6 space-y-4 max-w-2xl">
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Student *</label>
          <select
            value={form.student}
            onChange={(e) => { setForm(p => ({ ...p, student: e.target.value })); setValidation(null); }}
            onBlur={preflight}
            required
            className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
          >
            <option value="">Select student…</option>
            {students.map(s => (
              <option key={s.id} value={s.id}>{s.full_name} ({s.primary_phone})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Course *</label>
          <select
            value={form.course}
            onChange={(e) => { setForm(p => ({ ...p, course: e.target.value })); setValidation(null); }}
            onBlur={preflight}
            required
            className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
          >
            <option value="">Select course…</option>
            {courses.map(c => (
              <option key={c.id} value={c.id}>{c.name} — {c.university_name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Intake Session *</label>
          <select
            value={form.session}
            onChange={(e) => { setForm(p => ({ ...p, session: e.target.value })); setValidation(null); }}
            onBlur={preflight}
            required
            className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
          >
            <option value="">Select session…</option>
            {sessions.map(s => (
              <option key={s.id} value={s.id}>
                {s.session_name} {s.is_fresh_allowed ? '(fresh allowed)' : '(continuing only)'}
              </option>
            ))}
          </select>
        </div>

        {validation && (
          <div className={`rounded-md p-3 text-sm border ${
            validation.valid
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
              : 'bg-amber-50 border-amber-200 text-amber-700'
          }`}>
            {validation.valid ? (
              <span>✓ Pre-flight check passed. This enrollment is allowed.</span>
            ) : (
              <div>
                <p className="font-medium">⚠ Rule violation</p>
                <p className="mt-1">{validation.reason}</p>
                {validation.suggested && <p className="mt-1 text-xs">Suggested session ID: {validation.suggested}</p>}
              </div>
            )}
          </div>
        )}

        <div className="flex gap-3 pt-4 border-t border-border">
          <button
            type="submit"
            disabled={submitting || (validation !== null && !validation.valid)}
            className="bg-primary text-primary-foreground rounded-md px-6 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? 'Creating…' : 'Create Enrollment'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="border border-border rounded-md px-6 py-2 text-sm font-medium hover:bg-muted"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
