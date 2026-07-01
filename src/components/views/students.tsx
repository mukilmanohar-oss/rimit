'use client';

import { useEffect, useState } from 'react';
import { admissions, type Student, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';

export function StudentsView({ profile }: { profile: UserProfile }) {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);

  const canCreate = profile.role === 'counselor' || profile.role === 'academic_head' || profile.role === 'super_admin';

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      const data = await admissions.listStudents(params);
      setStudents(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load students');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  if (showForm) {
    return <StudentRegistrationForm
      onBack={() => { setShowForm(false); load(); }}
      onCancel={() => setShowForm(false)}
    />;
  }

  return (
    <div>
      <PageHeader
        title="Students"
        subtitle={profile.sub_center_code ? `Sub-center: ${profile.sub_center_code}` : 'All sub-centers'}
        action={canCreate && (
          <button
            onClick={() => setShowForm(true)}
            className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
          >
            + Register Student
          </button>
        )}
      />

      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search by name, phone, email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && load()}
          className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          onClick={load}
          className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          Search
        </button>
      </div>

      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> :
        students.length === 0 ? <EmptyState message="No students found" /> : (
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 border-b border-border">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Phone</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Email</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">DOB</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Sub-center</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">Enrollments</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {students.map(s => (
                  <tr key={s.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3 font-medium text-foreground">{s.full_name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{s.primary_phone}</td>
                    <td className="px-4 py-3 text-muted-foreground">{s.email || '—'}</td>
                    <td className="px-4 py-3 text-muted-foreground">{new Date(s.dob).toLocaleDateString('en-IN')}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs bg-muted px-2 py-0.5 rounded">{s.sub_center_code || '—'}</span>
                    </td>
                    <td className="px-4 py-3 text-right text-foreground font-medium">{s.enrollment_count ?? 0}</td>
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

function StudentRegistrationForm({ onBack, onCancel }: { onBack: () => void; onCancel: () => void }) {
  const [form, setForm] = useState({
    full_name: '', dob: '', gender: 'M',
    primary_phone: '', email: '', aadhar_number: '',
    parent_name: '', parent_phone: '',
    address_line1: '', address_city: '', address_state: '', address_pincode: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const set = (k: string, v: string) => setForm(prev => ({ ...prev, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);
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
        address_data: {
          line1: form.address_line1,
          city: form.address_city,
          state: form.address_state,
          pincode: form.address_pincode,
        },
      };
      const student = await admissions.createStudent(payload);
      setSuccess(`✓ ${student.full_name} registered successfully.`);
      setTimeout(() => onBack(), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <button onClick={onCancel} className="text-sm text-primary mb-4 hover:underline">
        ← Back to students
      </button>
      <PageHeader title="Register New Student" subtitle="Multi-step B2B sub-center registration form" />

      {error && <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive mb-4">{error}</div>}
      {success && <div className="bg-emerald-50 border border-emerald-200 rounded-md p-3 text-sm text-emerald-700 mb-4">{success}</div>}

      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-lg p-6 space-y-6 max-w-2xl">
        {/* Personal */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Personal Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Full Name *" value={form.full_name} onChange={v => set('full_name', v)} required />
            <Field label="Date of Birth *" type="date" value={form.dob} onChange={v => set('dob', v)} required />
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Gender</label>
              <select
                value={form.gender}
                onChange={e => set('gender', e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
            </div>
            <Field label="Aadhar Number (12 digits) *" value={form.aadhar_number} onChange={v => set('aadhar_number', v)} required pattern="\d{12}" />
          </div>
        </div>

        {/* Contact */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Contact</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Primary Phone (+91XXXXXXXXXX) *" value={form.primary_phone} onChange={v => set('primary_phone', v)} required />
            <Field label="Email" type="email" value={form.email} onChange={v => set('email', v)} />
            <Field label="Parent Name" value={form.parent_name} onChange={v => set('parent_name', v)} />
            <Field label="Parent Phone" value={form.parent_phone} onChange={v => set('parent_phone', v)} />
          </div>
        </div>

        {/* Address */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground border-b border-border pb-2">Address</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <Field label="Address Line 1" value={form.address_line1} onChange={v => set('address_line1', v)} />
            </div>
            <Field label="City" value={form.address_city} onChange={v => set('address_city', v)} />
            <Field label="State" value={form.address_state} onChange={v => set('address_state', v)} />
            <Field label="Pincode" value={form.address_pincode} onChange={v => set('address_pincode', v)} pattern="\d{6}" />
          </div>
        </div>

        <div className="flex gap-3 pt-4 border-t border-border">
          <button
            type="submit"
            disabled={submitting}
            className="bg-primary text-primary-foreground rounded-md px-6 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? 'Registering…' : 'Register Student'}
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
