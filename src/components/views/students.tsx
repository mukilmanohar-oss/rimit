'use client';

import { useEffect, useState } from 'react';
import { admissions, aggregator, finance, type Student, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';
import { usePermissions } from '@/lib/permissions';
import { StudentDetail } from './student-detail';
import { exportToCSV } from '@/lib/utils';
import { toast } from 'sonner';
import { ConfirmDialog } from '../rimit-shell';

export function StudentsView({ profile }: { profile: UserProfile }) {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [selected, setSelected] = useState<Student | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Batch checkout states
  const [selectedForCheckout, setSelectedForCheckout] = useState<Set<string>>(new Set());
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const { canCreate, canUpdate, canDelete } = usePermissions(profile.role, 'student');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { page: String(page) };
      if (search) params.search = search;
      if (statusFilter) params.lead_status = statusFilter;
      const data = await admissions.listStudents(params);
      setStudents(data.results);
      setTotalCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load students');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, statusFilter]); // eslint-disable-line

  const handleExportCSV = () => {
    const headers = ['Name', 'Phone', 'Email', 'DOB', 'Sub-center Code', 'Course', 'Status'];
    const rows = students.map(s => [
      s.full_name,
      s.primary_phone,
      s.email || '',
      new Date(s.dob).toLocaleDateString('en-IN'),
      s.sub_center_code || '',
      s.course_name || '',
      s.lead_status || '',
    ]);
    exportToCSV('students_export.csv', headers, rows);
  };

  const handleToggleSelect = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const next = new Set(selectedForCheckout);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedForCheckout(next);
  };

  const handleBatchCheckout = async () => {
    if (selectedForCheckout.size === 0) return;
    setCheckoutLoading(true);
    try {
      const res = await finance.batchCheckout(Array.from(selectedForCheckout));
      toast.success(`✓ Invoice #${res.invoice_id} created for ₹${res.total_amount}. Redirecting to gateway...`);
      setSelectedForCheckout(new Set());
      load();
    } catch (err: any) {
      toast.error(err.message || 'Batch checkout failed');
    } finally {
      setCheckoutLoading(false);
    }
  };

  if (selected) {
    return <StudentDetail
      student={selected}
      profile={profile}
      onBack={() => { setSelected(null); load(); }}
      onEdit={() => { setEditingStudent(selected); setSelected(null); }}
    />;
  }

  if (editingStudent) {
    return <StudentEditForm
      student={editingStudent}
      onBack={() => { setEditingStudent(null); setSelected(editingStudent); load(); }}
      onCancel={() => { setEditingStudent(null); setSelected(editingStudent); }}
    />;
  }

  if (showForm) {
    return <StudentRegistrationForm
      onBack={() => { setShowForm(false); load(); }}
      onCancel={() => setShowForm(false)}
    />;
  }

  return (
    <div>
      <PageHeader
        title="Leads & Students"
        subtitle={profile.sub_center_code ? `Sub-center: ${profile.sub_center_code}` : 'All sub-centers'}
        action={
          <div className="flex gap-2">
            {selectedForCheckout.size > 0 && (
              <button
                onClick={handleBatchCheckout}
                disabled={checkoutLoading}
                className="bg-green-600 text-white rounded-md px-4 py-2 text-sm font-medium hover:bg-green-700 disabled:opacity-50"
              >
                {checkoutLoading ? "Processing..." : `Batch Checkout (${selectedForCheckout.size})`}
              </button>
            )}
            {canCreate && (
              <button
                onClick={() => setShowForm(true)}
                className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
              >
                + Add Lead / Student
              </button>
            )}
          </div>
        }
      />

      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search by name, phone, email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (setPage(1), load())}
          className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Statuses</option>
          <option value="Pending Payment">Pending Payment</option>
          <option value="Enrolled">Enrolled</option>
        </select>
        <button
          onClick={() => { setPage(1); load(); }}
          className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          Search
        </button>
        <button
          onClick={handleExportCSV}
          className="border border-border text-muted-foreground hover:text-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Export CSV
        </button>
      </div>

      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> :
        students.length === 0 ? <EmptyState message="No students found" /> : (
          <div className="space-y-4">
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/30 border-b border-border">
                  <tr>
                    <th className="w-10 px-4 py-3"></th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Name</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Phone</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">DOB</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Course</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Sub-center</th>
                    <th className="text-right px-4 py-3 font-medium text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {students.map(s => (
                    <tr key={s.id} className="hover:bg-muted/20 cursor-pointer" onClick={() => setSelected(s)}>
                      <td className="px-4 py-3 text-center" onClick={e => e.stopPropagation()}>
                        {s.lead_status === 'Pending Payment' && (
                          <input
                            type="checkbox"
                            checked={selectedForCheckout.has(s.id)}
                            onChange={(e) => handleToggleSelect(e as any, s.id)}
                            className="rounded border-input text-primary focus:ring-primary cursor-pointer"
                          />
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium text-foreground">{s.full_name}</td>
                      <td className="px-4 py-3 text-muted-foreground">{s.primary_phone}</td>
                      <td className="px-4 py-3 text-muted-foreground">{new Date(s.dob).toLocaleDateString('en-IN')}</td>
                      <td className="px-4 py-3 text-muted-foreground truncate max-w-[150px]" title={s.course_name || ''}>{s.course_name || '-'}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs bg-muted px-2 py-0.5 rounded">{s.sub_center_code || '-'}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <StatusBadge status={s.lead_status || 'Pending Payment'} />
                      </td>
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
                  disabled={page >= Math.ceil(totalCount / 25)}
                  className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}


function StudentRegistrationForm({ onBack, onCancel }: { onBack: () => void; onCancel: () => void }) {
  const [form, setForm] = useState({
    full_name: '', dob: '', gender: 'M',
    primary_phone: '', email: '', aadhar_number: '',
    father_name: '', mother_name: '', parent_phone: '',
    alternate_phone: '', alternate_email: '',
    admission_type: 'Fresh', admission_semester: '1',
    address_line1: '', address_city: '', address_state: '', address_district: '', address_pincode: '',
    same_as_permanent: true,
    course_id: '', sub_course: ''
  });
  const [courses, setCourses] = useState<any[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aadharWarning, setAadharWarning] = useState<string | null>(null);
  const [consentGiven, setConsentGiven] = useState(false);

  useEffect(() => {
    aggregator.listCourses().then(res => setCourses(res.results)).catch(console.error);
  }, []);

  const handleAadharBlur = async () => {
    const clean = form.aadhar_number.replace(/\\s/g, '');
    if (clean.length !== 12) return;
    try {
      const res = await admissions.checkAadhar(clean);
      if (res.exists) {
        setAadharWarning('Duplicate Detected: A student with this Aadhar number already exists.');
      } else {
        setAadharWarning(null);
      }
    } catch {
      // Ignore network errors on check
    }
  };

  const set = (k: string, v: string) => setForm(prev => ({ ...prev, [k]: v }));

  const isFormValid = () => {
    const phoneValid = /^[0-9]{10}$/.test(form.primary_phone);
    const emailValid = form.email ? /^[^@]+@[^@]+\.[^@]+$/.test(form.email) : true;
    const aadharValid = form.aadhar_number.replace(/\s/g, '').length === 12;
    return form.full_name && form.dob && phoneValid && emailValid && aadharValid && form.course_id && consentGiven;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid()) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        full_name: form.full_name,
        dob: form.dob,
        gender: form.gender,
        primary_phone: form.primary_phone,
        email: form.email,
        aadhar_number: form.aadhar_number,
        parent_name: form.parent_name,
        parent_phone: form.parent_phone,
                course: form.course_id,
        sub_course: form.sub_course,
        address_block: {
          perm_domicile_type: 'Other',
          domicile_state: form.address_state,
          perm_address: form.address_line1,
          perm_country: 'INDIA',
          perm_state: form.address_state,
          perm_district: form.address_district,
          perm_city: form.address_city,
          perm_pincode: form.address_pincode,
          corr_address: form.address_line1,
          corr_country: 'INDIA',
          corr_state: form.address_state,
          corr_district: form.address_district,
          corr_city: form.address_city,
          corr_pincode: form.address_pincode,
        },
        data_subject_consent: {
          consent_given: true,
          timestamp: new Date().toISOString(),
          scope: ['admissions', 'marketing', 'notifications'],
        },
      };
      const student = await admissions.createStudent(payload);
      toast.success(`✓ ${student.full_name} registered successfully.`);
      setTimeout(() => onBack(), 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed');
      toast.error('Registration failed. Please check the form errors.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <button onClick={onCancel} className="text-sm text-primary mb-4 hover:underline">
        ← Back to students
      </button>
      <PageHeader title="Register New Lead / Student" subtitle="Multi-step B2B sub-center registration form" />

      {error && <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-lg p-6 space-y-6 max-w-2xl">
        {/* Personal */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Personal Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Full Name *" value={form.full_name} onChange={v => set('full_name', v)} required />
            <Field label="Date of Birth *" type="date" value={form.dob} onChange={v => set('dob', v)} required />
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Gender</label>
              <select value={form.gender} onChange={e => set('gender', e.target.value)} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm">
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Admission Type</label>
              <select value={form.admission_type} onChange={e => set('admission_type', e.target.value)} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm">
                <option value="Fresh">Fresh</option>
                <option value="Lateral">Lateral</option>
              </select>
            </div>
            <Field label="Admission Semester" value={form.admission_semester} onChange={v => set('admission_semester', v)} />
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Aadhar Number (12 digits) *</label>
              <input
                type="text" value={form.aadhar_number} onChange={e => { set('aadhar_number', e.target.value); setAadharWarning(null); }}
                onBlur={handleAadharBlur} required pattern="[0-9]{12}"
                className={`w-full px-3 py-2 rounded-md border bg-background text-sm focus:outline-none focus:ring-2 ${aadharWarning ? 'border-amber-500 focus:ring-amber-500 text-amber-800' : 'border-input focus:ring-ring'}`}
              />
              {aadharWarning && <p className="text-xs text-amber-600 font-medium mt-1">{aadharWarning}</p>}
            </div>
          </div>
        </div>

        {/* Academic Profile */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Academic Profile</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Target Course *</label>
              <select value={form.course_id} onChange={e => set('course_id', e.target.value)} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm" required>
                <option value="">Select Course...</option>
                {courses.map(c => <option key={c.id} value={c.id}>{c.name} ({c.stream})</option>)}
              </select>
            </div>
            <Field label="Sub-Course Specialization" value={form.sub_course} onChange={v => set('sub_course', v)} />
          </div>
        </div>

        {/* Contact */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Contact</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Primary Phone (+91XXXXXXXXXX) *" value={form.primary_phone} onChange={v => set('primary_phone', v)} required pattern="^[0-9]{10}$" />
            <Field label="Alternate Phone" value={form.alternate_phone} onChange={v => set('alternate_phone', v)} />
            <Field label="Email" type="email" value={form.email} onChange={v => set('email', v)} pattern="^[^@]+@[^@]+.[^@]+$" />
            <Field label="Alternate Email" type="email" value={form.alternate_email} onChange={v => set('alternate_email', v)} />
            <Field label="Father Name" value={form.father_name} onChange={v => set('father_name', v)} />
            <Field label="Mother Name" value={form.mother_name} onChange={v => set('mother_name', v)} />
            <Field label="Parent Phone" value={form.parent_phone} onChange={v => set('parent_phone', v)} />
          </div>
        </div>

        {/* Address */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Permanent Address</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <Field label="Complete Address *" value={form.address_line1} onChange={v => set('address_line1', v)} required />
            </div>
            <Field label="City *" value={form.address_city} onChange={v => set('address_city', v)} required />
            <Field label="District *" value={form.address_district} onChange={v => set('address_district', v)} required />
            <Field label="State *" value={form.address_state} onChange={v => set('address_state', v)} required />
            <Field label="Pincode *" value={form.address_pincode} onChange={v => set('address_pincode', v)} required pattern="[0-9]{6}" />
          </div>

          <div className="mt-4 mb-2 flex items-center gap-2">
            <input 
              type="checkbox" 
              id="same_as_perm" 
              checked={form.same_as_permanent} 
              onChange={e => set('same_as_permanent', e.target.checked as any)} 
            />
            <label htmlFor="same_as_perm" className="text-sm font-medium">Correspondence Address Same As Permanent</label>
          </div>
          
          {!form.same_as_permanent && (
             <div className="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-3 rounded mt-2">
                NOTE: IF THE CORRESPONDENCE ADDRESS IS DIFFERENT FROM THE PERMANENT ADDRESS, SUBMIT ANY ONE SUPPORTING DOCUMENT SUCH AS RENT AGREEMENT OR ELECTRICITY BILL OR ANY OTHER VALID OFFICIAL DOCUMENT.
             </div>
          )}
        </div>
        {/* DPDP Consent */}
        <div className="bg-muted/40 border border-border p-4 rounded-lg space-y-2">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={consentGiven}
              onChange={e => setConsentGiven(e.target.checked)}
              className="mt-1 rounded border-input text-primary focus:ring-ring"
            />
            <span className="text-xs text-muted-foreground leading-relaxed">
              <strong>DPDP Act 2023 Consent Mandate:</strong> I hereby grant explicit consent to RIMIT Educational Charitable Trust and its authorized sub-center partner to process, store, and verify my demographic data, Aadhar hash, academic credentials, and uploaded documents for the sole purpose of course admissions, financial escrow clearance, and status notifications.
            </span>
          </label>
        </div>

        <div className="flex gap-3 pt-4 border-t border-border">
          <button type="submit" disabled={submitting || !isFormValid()} className="bg-primary text-primary-foreground rounded-md px-6 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50">
            {submitting ? "Saving..." : "Save Lead / Student"}
          </button>
          <button type="button" onClick={onCancel} className="border border-border rounded-md px-6 py-2 text-sm font-medium hover:bg-muted">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', required, pattern }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
  pattern?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-muted-foreground mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        pattern={pattern}
        className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
    </div>
  );
}

function StudentEditForm({ student, onBack, onCancel }: { student: Student; onBack: () => void; onCancel: () => void }) {
  const [form, setForm] = useState({
    full_name: student.full_name || "", dob: student.dob || "", gender: student.gender || "M",
    primary_phone: student.primary_phone || "", email: student.email || "", 
    parent_name: student.parent_name || "", parent_phone: student.parent_phone || "",
    address_line1: student.address_data?.line1 || "", address_city: student.address_data?.city || "", 
    address_state: student.address_data?.state || "", address_pincode: student.address_data?.pincode || "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: string, v: string) => setForm(prev => ({ ...prev, [k]: v }));

  const isFormValid = () => {
    const phoneValid = /^[0-9]{10}$/.test(form.primary_phone);
    const emailValid = form.email ? /^[^@]+@[^@]+\.[^@]+$/.test(form.email) : true;
    return form.full_name && form.dob && phoneValid && emailValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid()) return;
    setSubmitting(true);
    setError(null);
    try {
      let address_block = undefined;
      if (form.address_line1 && form.address_city && form.address_state && form.address_pincode) {
        address_block = {
          perm_domicile_type: 'Other',
          domicile_state: form.address_state,
          perm_address: form.address_line1,
          perm_country: 'INDIA',
          perm_state: form.address_state,
          perm_district: form.address_city, // fallback
          perm_city: form.address_city,
          perm_pincode: form.address_pincode,
          corr_address: form.address_line1,
          corr_country: 'INDIA',
          corr_state: form.address_state,
          corr_district: form.address_city,
          corr_city: form.address_city,
          corr_pincode: form.address_pincode,
        };
      }

      const payload = {
        full_name: form.full_name, dob: form.dob, gender: form.gender,
        primary_phone: form.primary_phone, email: form.email,
        parent_name: form.parent_name, parent_phone: form.parent_phone,
        alternate_email: form.alternate_email,
        alternate_phone: form.alternate_phone,
        admission_type: form.admission_type,
        admission_semester: form.admission_semester,
        address_block: address_block,
      };
      await admissions.updateStudent(student.id, payload);
      toast.success(`? ${student.full_name} updated successfully.`);
      setTimeout(() => onBack(), 1500);
    } catch (err) {
      setError("Update failed. Please check the form errors.");
      toast.error("Update failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <button onClick={onCancel} className="text-sm text-primary mb-4 hover:underline">
        ? Back to student details
      </button>
      <PageHeader title="Edit Student Profile" subtitle={`Updating ${student.full_name}`} />

      {error && <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-lg p-6 space-y-6 max-w-2xl">
        {/* Personal */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Personal Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Full Name *" value={form.full_name} onChange={v => set("full_name", v)} required />
            <Field label="Date of Birth *" type="date" value={form.dob} onChange={v => set("dob", v)} required />
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Gender</label>
              <select
                value={form.gender}
                onChange={e => set("gender", e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
            </div>
            {/* Aadhar is typically immutable or requires special process, so omitted from edit for safety */}
          </div>
        </div>

        {/* Contact */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Contact</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Primary Phone (+91XXXXXXXXXX) *" value={form.primary_phone} onChange={v => set("primary_phone", v)} required />
            <Field label="Email" type="email" value={form.email} onChange={v => set("email", v)} />
            <Field label="Parent Name" value={form.parent_name} onChange={v => set("parent_name", v)} />
            <Field label="Parent Phone" value={form.parent_phone} onChange={v => set("parent_phone", v)} />
          </div>
        </div>

        {/* Address */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Address</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <Field label="Address Line 1" value={form.address_line1} onChange={v => set("address_line1", v)} />
            </div>
            <Field label="City" value={form.address_city} onChange={v => set("address_city", v)} />
            <Field label="State" value={form.address_state} onChange={v => set("address_state", v)} />
            <Field label="Pincode" value={form.address_pincode} onChange={v => set("address_pincode", v)} pattern="[0-9]{6}" />
          </div>
        </div>

        <div className="flex gap-3 pt-4 border-t border-border">
          <button
            type="submit"
            disabled={submitting || !isFormValid()}
            className="bg-primary text-primary-foreground rounded-md px-6 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? "Saving..." : "Save Changes"}
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

