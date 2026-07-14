'use client';

import { useEffect, useState } from 'react';
import { admissions, aggregator, rules, finance, type Enrollment, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';
import { usePermissions } from '@/lib/permissions';
import { exportToCSV } from '@/lib/utils';
import { toast } from 'sonner';
import { ConfirmDialog } from '../rimit-shell';
import { Combobox } from '@/components/ui/combobox';

export function EnrollmentsView({ profile }: { profile: UserProfile }) {
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingEnrollment, setEditingEnrollment] = useState<Enrollment | null>(null);
  const [selected, setSelected] = useState<Enrollment | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const { canCreate, canUpdate } = usePermissions(profile.role, 'enrollment');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { page: String(page) };
      if (statusFilter) params.status = statusFilter;
      const data = await admissions.listEnrollments(params);
      setEnrollments(data.results);
      setTotalCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load enrollments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page]); // eslint-disable-line

  const handleExportCSV = () => {
    const headers = ['Student Name', 'Course Name', 'University Name', 'Session', 'Status', 'Created At'];
    const rows = enrollments.map(e => [
      e.student_name || '',
      e.course_name || '',
      e.university_name || '',
      e.session_name || '',
      e.status,
      new Date(e.created_at).toLocaleDateString('en-IN')
    ]);
    exportToCSV('enrollments_export.csv', headers, rows);
  };

  if (showForm) {
    return <EnrollmentCreateForm onBack={() => { setShowForm(false); load(); }} onCancel={() => setShowForm(false)} />;
  }

  if (selected) {
    return <EnrollmentDetail 
      enrollment={selected} 
      onBack={() => { setSelected(null); load(); }} 
      onEdit={() => { setEditingEnrollment(selected); setSelected(null); }}
      canUpdate={canUpdate}
    />;
  }

  if (editingEnrollment) {
    return <EnrollmentEditForm 
      enrollment={editingEnrollment} 
      onBack={() => { setEditingEnrollment(null); setSelected(editingEnrollment); load(); }} 
      onCancel={() => { setEditingEnrollment(null); setSelected(editingEnrollment); }} 
    />;
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
          onClick={() => { setPage(1); load(); }}
          className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          Apply
        </button>
        <button
          onClick={handleExportCSV}
          className="border border-border text-muted-foreground hover:text-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Export CSV
        </button>
      </div>

      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> :
        enrollments.length === 0 ? <EmptyState message="No enrollments found" /> : (
          <div className="space-y-4">
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

            <div className="flex items-center justify-between py-2">
              <span className="text-xs text-muted-foreground">
                Page {page} of {Math.max(1, Math.ceil(totalCount / 25))} (Total {totalCount} records)
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * 25 >= totalCount}
                  className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )
      }
    </div>
  );
}

function EnrollmentDetail({ enrollment, onBack, onEdit, canUpdate }: { enrollment: Enrollment; onBack: () => void; onEdit: () => void; canUpdate: boolean }) {
  const [detail, setDetail] = useState<Enrollment>(enrollment);
  const [timeline, setTimeline] = useState<any[]>([]);
const [transitioning, setTransitioning] = useState(false);
  const [showMockPayment, setShowMockPayment] = useState(false);
  const [mockAmount, setMockAmount] = useState("30000");
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cancelDialog, setCancelDialog] = useState(false);

  const loadTimeline = async () => {
    try {
      const data = await admissions.getEnrollmentTimeline(detail.id);
      setTimeline(data.timeline || []);
    } catch {
      // ignore timeline load errors
    }
  };

  useEffect(() => { loadTimeline(); }, []); // eslint-disable-line

const handleMockPayment = async () => {
    if (!detail) return;
    setPaymentLoading(true);
    setError(null);
    try {
      await finance.mockPayment(detail.id, mockAmount);
      toast.success(`Simulated payment of ₹${mockAmount} successful!`);
      setShowMockPayment(false);
      loadTimeline();
      const updated = await admissions.getEnrollment(detail.id);
      setDetail(updated);
    } catch (err) {
      toast.error("Mock payment failed");
      setError(err instanceof Error ? err.message : "Mock payment failed");
    } finally {
      setPaymentLoading(false);
    }
  };

  const transition = async (newStatus: string) => {
    setTransitioning(true);
    setError(null);
    try {
      const updated = await admissions.transitionStatus(detail.id, newStatus);
      setDetail(updated);
      loadTimeline();
      toast.success(`Enrollment transitioned to ${newStatus}`);
    } catch (err) {
      let errMsg = 'Transition failed';
      if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message);
          if (parsed.status && Array.isArray(parsed.status)) {
            errMsg = parsed.status[0];
          } else if (parsed.non_field_errors) {
            errMsg = parsed.non_field_errors[0];
          } else if (parsed.detail) {
            errMsg = parsed.detail;
          } else {
            errMsg = err.message;
          }
        } catch {
          errMsg = err.message;
        }
      }
      setError(errMsg);
      toast.error(errMsg);
    } finally {
      setTransitioning(false);
    }
  };

  return (
    <div>
      <button onClick={onBack} className="text-sm text-primary mb-4 hover:underline">
        ← Back to enrollments
      </button>
      <PageHeader 
        title="Enrollment Detail" 
        subtitle={detail.enrollment_number || `ID: ${detail.id.slice(0, 8)}`} 
        action={
          <div className="flex gap-2">
            {canUpdate && (
              <button
              onClick={onEdit}
              className="border border-border text-foreground hover:bg-muted rounded-md px-3 py-1.5 text-sm font-medium"
            >
              Edit 
              </button>
            )}
            {canUpdate && (
              <button
              onClick={() => setCancelDialog(true)}
              className="bg-destructive text-white hover:bg-destructive/90 rounded-md px-3 py-1.5 text-sm font-medium"
              disabled={detail.status === 'Cancelled'}
            >
              Cancel Enrollment
            </button>
            )}
          </div>
        }
      />

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
            {detail.status === 'Fee Pending' && (
              <div className="mb-4">
                <button
                  onClick={() => setShowMockPayment(true)}
                  className="w-full bg-emerald-600 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-emerald-700 transition"
                >
                  Simulate Payment Capture (Mock)
                </button>
              </div>
            )}
            {detail.status === 'Fee Pending' && (
              <div className="mb-4">
                <button
                  onClick={() => setShowMockPayment(true)}
                  className="w-full bg-emerald-600 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-emerald-700 transition"
                >
                  Simulate Payment Capture (Mock)
                </button>
              </div>
            )}
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

                    {canUpdate && detail.next_valid_statuses && detail.next_valid_statuses.length > 0 && (
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

          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Audit Timeline</h3>
            <div className="space-y-4">
              {timeline.length === 0 ? (
                <p className="text-xs text-muted-foreground">No audit logs available.</p>
              ) : (
                timeline.map((entry, idx) => (
                  <div key={idx} className="relative pl-4 border-l-2 border-muted">
                    <span className="absolute -left-[5px] top-1 w-2 h-2 rounded-full bg-primary" />
                    <p className="text-[10px] text-muted-foreground">{new Date(entry.timestamp).toLocaleString('en-IN')}</p>
                    <p className="text-sm font-medium text-foreground">{entry.action}</p>
                    {entry.user_name && <p className="text-xs text-muted-foreground">By {entry.user_name}</p>}
                    {entry.new_data?.status && entry.old_data?.status !== entry.new_data?.status && (
                      <p className="text-xs mt-1 bg-muted inline-block px-1.5 py-0.5 rounded border border-border">
                        {entry.old_data?.status || 'None'} → {entry.new_data.status}
                      </p>
                    )}
                    {entry.notes && <p className="text-xs italic mt-1">{entry.notes}</p>}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
      
      <ConfirmDialog
        open={cancelDialog}
        onOpenChange={setCancelDialog}
        title="Cancel Enrollment?"
        description="Are you sure you want to cancel this enrollment? This action will mark it as cancelled (soft delete) and stop any further processing."
        onConfirm={() => {
          transition('Cancelled');
          setCancelDialog(false);
        }}
        confirmText="Cancel Enrollment"
      />

      {showMockPayment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-background border border-border p-6 rounded-lg shadow-lg max-w-sm w-full">
            <h3 className="text-lg font-bold mb-4">Simulate Payment (Mock)</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Enter the amount to mock a successful payment capture via Razorpay.
            </p>
            <input
              type="number"
              value={mockAmount}
              onChange={(e) => setMockAmount(e.target.value)}
              className="w-full border border-border bg-background text-foreground p-2 rounded-md mb-4"
              placeholder="Amount (e.g. 30000)"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowMockPayment(false)}
                className="px-4 py-2 text-sm font-medium border border-border hover:bg-muted rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={handleMockPayment}
                disabled={paymentLoading || !mockAmount}
                className="px-4 py-2 text-sm font-medium bg-emerald-600 text-white hover:bg-emerald-700 rounded-md disabled:opacity-50"
              >
                {paymentLoading ? 'Processing...' : 'Simulate Payment'}
              </button>
            </div>
          </div>
        </div>
      )}
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
      const enrollment = await admissions.createEnrollment(form);
      toast.success(`✓ Enrollment for ${enrollment.student_name} created successfully.`);
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
      toast.error('Enrollment creation failed. Please check form errors.');
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
          <Combobox
            options={students.map(s => ({ value: s.id, label: `${s.full_name} (${s.primary_phone})` }))}
            value={form.student}
            onChange={(val) => { setForm(p => ({ ...p, student: val })); setValidation(null); }}
            onBlur={preflight}
            placeholder="Search student…"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Course *</label>
          <Combobox
            options={courses.map(c => ({ value: c.id, label: `${c.name} — ${c.university_name || 'No University'}` }))}
            value={form.course}
            onChange={(val) => { setForm(p => ({ ...p, course: val })); setValidation(null); }}
            onBlur={preflight}
            placeholder="Search course…"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Intake Session *</label>
          <Combobox
            options={sessions.map(s => ({ value: s.id, label: `${s.session_name} ${s.is_fresh_allowed ? '(fresh allowed)' : '(continuing only)'}` }))}
            value={form.session}
            onChange={(val) => { setForm(p => ({ ...p, session: val })); setValidation(null); }}
            onBlur={preflight}
            placeholder="Search session…"
          />
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

function EnrollmentEditForm({ enrollment, onBack, onCancel }: { enrollment: Enrollment; onBack: () => void; onCancel: () => void }) {
  const [notes, setNotes] = useState(enrollment.notes || "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await admissions.updateEnrollment(enrollment.id, { notes });
      toast.success(`? Enrollment updated successfully.`);
      setTimeout(() => onBack(), 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Enrollment update failed");
      toast.error("Enrollment update failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <button onClick={onCancel} className="text-sm text-primary mb-4 hover:underline">? Back to enrollments</button>
      <PageHeader title="Edit Enrollment" subtitle={`Editing enrollment ID: ${enrollment.id.slice(0, 8)}`} />

      {error && <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-lg p-6 space-y-4 max-w-2xl">
        
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm h-32"
            placeholder="Add internal notes..."
          />
        </div>

        <div className="flex gap-3 pt-4 border-t border-border">
          <button
            type="submit"
            disabled={submitting}
            className="bg-primary text-primary-foreground rounded-md px-6 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? "Saving�" : "Save Changes"}
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

