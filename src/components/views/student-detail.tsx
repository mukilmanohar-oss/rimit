'use client';

import { useEffect, useState } from 'react';
import { admissions, type Student, type StudentDoc, type StudentAcademicHistory, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge, ConfirmDialog } from '../rimit-shell';
import { toast } from 'sonner';

interface StudentDetailProps {
  student: Student;
  profile: UserProfile;
  onBack: () => void;
  onEdit?: () => void;
}

export function StudentDetail({ student: initialStudent, profile, onBack, onEdit }: StudentDetailProps) {
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'academic' | 'documents'>('profile');

  // Academic form state
  const [showAcademicForm, setShowAcademicForm] = useState(false);
  const [academicForm, setAcademicForm] = useState({
    qualification: '10th',
    institution: '',
    board_university: '',
    year_of_passing: new Date().getFullYear(),
    score_type: 'percentage',
    score_value: '',
    result: 'Pass',
    subject_stream: '',
  });

  // Document form state
  const [showDocForm, setShowDocForm] = useState(false);
  const [docForm, setDocForm] = useState({
    category: 'identity',
    title: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docSubmitting, setDocSubmitting] = useState(false);

  // Reject state
  const [rejectingDocId, setRejectingDocId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const canEdit = profile.role === 'counselor' || profile.role === 'academic_head' || profile.role === 'super_admin';
  const isAdmin = profile.role === 'academic_head' || profile.role === 'super_admin';

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const fullStudent = await admissions.getStudent(initialStudent.id);
      setStudent(fullStudent);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load student details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [initialStudent.id]); // eslint-disable-line

  const handleAddAcademic = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!student) return;
    setError(null);
    try {
      await admissions.createStudentAcademicHistory(student.id, {
        qualification: academicForm.qualification,
        institution: academicForm.institution,
        board_university: academicForm.board_university,
        year_of_passing: Number(academicForm.year_of_passing),
        score_type: academicForm.score_type,
        score_value: String(academicForm.score_value),
        result: academicForm.result,
        subject_stream: academicForm.subject_stream,
      });
      setShowAcademicForm(false);
      setAcademicForm({
        qualification: '10th',
        institution: '',
        board_university: '',
        year_of_passing: new Date().getFullYear(),
        score_type: 'percentage',
        score_value: '',
        result: 'Pass',
        subject_stream: '',
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add academic history');
    }
  };

  const handleDocUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!student || !selectedFile) return;
    setDocSubmitting(true);
    setError(null);
    try {
      // Mocking S3 uploading by sending the expected payload to standard StudentDoc API
      await admissions.createStudentDoc({
        student: student.id,
        doc_category: docForm.category,
        title: docForm.title || selectedFile.name,
        s3_object_uri: `s3://rimit-docs/students/${student.id}/${Date.now()}_${selectedFile.name}`,
        file_size_bytes: selectedFile.size,
        mime_type: selectedFile.type || 'application/pdf',
      });
      setShowDocForm(false);
      setDocForm({ category: 'identity', title: '' });
      setSelectedFile(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload document');
    } finally {
      setDocSubmitting(false);
    }
  };

  const handleVerifyDoc = async (id: string) => {
    try {
      await admissions.verifyStudentDoc(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    }
  };

  const handleRejectDoc = async (id: string) => {
    if (!rejectionReason.trim()) return;
    try {
      await admissions.rejectStudentDoc(id, rejectionReason);
      setRejectingDocId(null);
      setRejectionReason('');
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rejection failed');
    }
  };

  const [docToDelete, setDocToDelete] = useState<string | null>(null);

  const handleDeleteDoc = async (id: string) => {
    try {
      await admissions.deleteStudentDoc(id);
      load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete document');
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  const [studentToDelete, setStudentToDelete] = useState(false);

  const handleDeleteStudent = async () => {
    if (!student) return;
    try {
      // Soft delete by setting is_active to false
      await admissions.updateStudent(student.id, { is_active: false });
      toast.success(`✓ ${student.full_name} deleted successfully.`);
      setStudentToDelete(false);
      onBack();
    } catch (err) {
      toast.error('Failed to delete student.');
      setError(err instanceof Error ? err.message : 'Failed to delete student');
    }
  };

  if (loading && !student) return <LoadingState />;
  if (error && !student) return <ErrorState message={error} />;
  if (!student) return <EmptyState message="Student not found" />;

  return (
    <div>
      <PageHeader
        title={student.full_name}
        subtitle={`Registered: ${new Date(student.created_at).toLocaleDateString('en-IN')}${!student.is_active ? ' (Deleted)' : ''}`}
        breadcrumbs={[{ label: 'Students', onClick: onBack }, { label: student.full_name }]}
        action={
          <div className="flex gap-2">
            {onEdit && canEdit && (
              <button
                onClick={onEdit}
                className="border border-border text-foreground hover:bg-muted rounded-md px-3 py-1.5 text-sm font-medium"
              >
                Edit Student
              </button>
            )}
            {canEdit && (
              <button
                onClick={() => setStudentToDelete(true)}
                className="bg-destructive text-white hover:bg-destructive/90 rounded-md px-3 py-1.5 text-sm font-medium"
              >
                Delete
              </button>
            )}
          </div>
        }
      />

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive mb-4">
          {error}
        </div>
      )}

      {/* Tabs Header */}
      <div className="flex border-b border-border mb-6">
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
            activeTab === 'profile'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Profile Details
        </button>
        <button
          onClick={() => setActiveTab('academic')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
            activeTab === 'academic'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Academic History ({student.academic_histories?.length ?? 0})
        </button>
        <button
          onClick={() => setActiveTab('documents')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
            activeTab === 'documents'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Documents Vault ({student.documents?.length ?? 0})
        </button>
      </div>

      {/* Profile Details Tab */}
      {activeTab === 'profile' && (
        <div className="bg-card border border-border rounded-lg p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                Personal Information
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Full Name</span>
                  <span className="font-medium text-foreground">{student.full_name}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Date of Birth</span>
                  <span className="font-medium text-foreground">{new Date(student.dob).toLocaleDateString('en-IN')}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Gender</span>
                  <span className="font-medium text-foreground">
                    {student.gender === 'M' ? 'Male' : student.gender === 'F' ? 'Female' : 'Other'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Sub-center Code</span>
                  <span className="font-medium text-foreground">{student.sub_center_code || '—'}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                Contact &amp; Family
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Primary Phone</span>
                  <span className="font-medium text-foreground">{student.primary_phone}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Email Address</span>
                  <span className="font-medium text-foreground">{student.email || '—'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Parent / Guardian Name</span>
                  <span className="font-medium text-foreground">{student.parent_name || '—'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Parent Phone</span>
                  <span className="font-medium text-foreground">{student.parent_phone || '—'}</span>
                </div>
              </div>
            </div>

            <div className="md:col-span-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                Address Details
              </h3>
              <div className="text-sm bg-muted/30 p-4 rounded-md border border-border">
                {student.address_data && Object.keys(student.address_data).length > 0 ? (
                  <div>
                    <p className="text-foreground">{student.address_data.line1 || 'No address line 1'}</p>
                    <p className="text-muted-foreground mt-1">
                      {student.address_data.city && `${student.address_data.city}, `}
                      {student.address_data.state && `${student.address_data.state} - `}
                      {student.address_data.pincode}
                    </p>
                  </div>
                ) : (
                  <p className="text-muted-foreground">No address recorded</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Academic History Tab */}
      {activeTab === 'academic' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-foreground">Academic History</h3>
            {canEdit && !showAcademicForm && (
              <button
                onClick={() => setShowAcademicForm(true)}
                className="bg-primary text-primary-foreground rounded-md px-3 py-1.5 text-sm font-medium hover:bg-primary/90"
              >
                + Add Qualification
              </button>
            )}
          </div>

          {showAcademicForm && (
            <form onSubmit={handleAddAcademic} className="bg-card border border-border rounded-lg p-5 space-y-4 max-w-xl">
              <h4 className="text-sm font-bold text-foreground">Add Qualification Record</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Qualification *</label>
                  <select
                    value={academicForm.qualification}
                    onChange={e => setAcademicForm(prev => ({ ...prev, qualification: e.target.value }))}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  >
                    <option value="10th">10th Standard</option>
                    <option value="12th">12th Standard</option>
                    <option value="UG">Undergraduate</option>
                    <option value="PG">Postgraduate</option>
                    <option value="Diploma">Diploma</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Year of Passing *</label>
                  <input
                    type="number"
                    value={academicForm.year_of_passing}
                    onChange={e => setAcademicForm(prev => ({ ...prev, year_of_passing: Number(e.target.value) }))}
                    required
                    min="1950"
                    max={new Date().getFullYear()}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Institution Name *</label>
                  <input
                    type="text"
                    value={academicForm.institution}
                    onChange={e => setAcademicForm(prev => ({ ...prev, institution: e.target.value }))}
                    required
                    placeholder="E.g., St. Mary's School"
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Board / University *</label>
                  <input
                    type="text"
                    value={academicForm.board_university}
                    onChange={e => setAcademicForm(prev => ({ ...prev, board_university: e.target.value }))}
                    required
                    placeholder="E.g., CBSE, MG University"
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Score Type *</label>
                  <select
                    value={academicForm.score_type}
                    onChange={e => setAcademicForm(prev => ({ ...prev, score_type: e.target.value }))}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  >
                    <option value="percentage">Percentage (%)</option>
                    <option value="cgpa">CGPA</option>
                    <option value="grade">Grade</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Score Value *</label>
                  <input
                    type="text"
                    value={academicForm.score_value}
                    onChange={e => setAcademicForm(prev => ({ ...prev, score_value: e.target.value }))}
                    required
                    placeholder="E.g. 85.5 or 9.2"
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Result *</label>
                  <select
                    value={academicForm.result}
                    onChange={e => setAcademicForm(prev => ({ ...prev, result: e.target.value }))}
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  >
                    <option value="Pass">Pass</option>
                    <option value="Fail">Fail</option>
                    <option value="Awaiting">Awaiting</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Subject / Stream</label>
                  <input
                    type="text"
                    value={academicForm.subject_stream}
                    onChange={e => setAcademicForm(prev => ({ ...prev, subject_stream: e.target.value }))}
                    placeholder="E.g., Science, Computer Science"
                    className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                  />
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
                >
                  Save Record
                </button>
                <button
                  type="button"
                  onClick={() => setShowAcademicForm(false)}
                  className="border border-border rounded-md px-4 py-2 text-sm font-medium hover:bg-muted"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}

          {!student.academic_histories || student.academic_histories.length === 0 ? (
            <EmptyState message="No academic qualification records found." />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {student.academic_histories.map((ac) => (
                <div key={ac.id} className="bg-card border border-border rounded-lg p-4 space-y-2 shadow-sm relative">
                  <div className="flex justify-between items-start">
                    <span className="text-sm font-bold text-foreground bg-primary/10 text-primary px-2.5 py-0.5 rounded-full">
                      {ac.qualification}
                    </span>
                    <span className="text-xs text-muted-foreground">{ac.year_of_passing}</span>
                  </div>
                  <div className="text-sm">
                    <p className="font-semibold text-foreground">{ac.institution}</p>
                    <p className="text-muted-foreground">{ac.board_university}</p>
                    <p className="text-muted-foreground">Result: <span className="font-medium text-foreground">{ac.result || 'Pass'}</span></p>
                  </div>
                  <div className="bg-muted/30 p-2 rounded text-xs border border-border">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">{ac.score_type === 'percentage' ? 'Percentage' : ac.score_type.toUpperCase()}</span>
                      <span className="font-semibold text-foreground">{ac.score_value}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Documents Vault Tab */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-semibold text-foreground">Documents Vault</h3>
            {canEdit && !showDocForm && (
              <button
                onClick={() => setShowDocForm(true)}
                className="bg-primary text-primary-foreground rounded-md px-3 py-1.5 text-sm font-medium hover:bg-primary/90"
              >
                + Upload Document
              </button>
            )}
          </div>

          {showDocForm && (
            <form onSubmit={handleDocUpload} className="bg-card border border-border rounded-lg p-5 space-y-4 max-w-md">
              <h4 className="text-sm font-bold text-foreground">Upload Document</h4>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Document Title *</label>
                <input
                  type="text"
                  value={docForm.title}
                  onChange={e => setDocForm(prev => ({ ...prev, title: e.target.value }))}
                  required
                  placeholder="E.g., Aadhar Card Front"
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Category *</label>
                <select
                  value={docForm.category}
                  onChange={e => setDocForm(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                >
                  <option value="identity">Identity Proof</option>
                  <option value="marklist">Marklist / Certificate</option>
                  <option value="migration">Migration Certificate</option>
                  <option value="experience">Experience Certificate</option>
                  <option value="photo">Passport Photo</option>
                  <option value="other">Other Document</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Select File *</label>
                <input
                  type="file"
                  onChange={e => setSelectedFile(e.target.files?.[0] || null)}
                  required
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm file:mr-4 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={docSubmitting || !selectedFile}
                  className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                >
                  {docSubmitting ? 'Uploading…' : 'Upload File'}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowDocForm(false); setSelectedFile(null); }}
                  className="border border-border rounded-md px-4 py-2 text-sm font-medium hover:bg-muted"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}

          {!student.documents || student.documents.length === 0 ? (
            <EmptyState message="No documents uploaded yet." />
          ) : (
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/30 border-b border-border">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Document Title</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Category</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Details</th>
                    <th className="text-right px-4 py-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {student.documents.map((d) => (
                    <tr key={d.id} className="hover:bg-muted/10">
                      <td className="px-4 py-3">
                        <div className="font-semibold text-foreground">{d.title}</div>
                        <div className="text-xs text-muted-foreground font-mono truncate max-w-xs">{d.s3_object_uri}</div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground uppercase text-xs font-semibold">
                        {d.doc_category}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={d.status} />
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">
                        {d.status === 'rejected' && d.rejection_reason && (
                          <div className="text-destructive font-medium">Reason: {d.rejection_reason}</div>
                        )}
                        {d.status === 'verified' && d.verified_at && (
                          <div>Verified on {new Date(d.verified_at).toLocaleDateString('en-IN')}</div>
                        )}
                        {d.file_size_bytes > 0 && (
                          <div>Size: {(d.file_size_bytes / 1024).toFixed(1)} KB</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        {/* Verify/Reject Controls for Admin roles */}
                        {isAdmin && d.status === 'pending' && (
                          <>
                            {rejectingDocId === d.id ? (
                              <div className="inline-flex items-center gap-1.5">
                                <input
                                  type="text"
                                  placeholder="Reason..."
                                  value={rejectionReason}
                                  onChange={e => setRejectionReason(e.target.value)}
                                  className="px-2 py-1 border border-input rounded text-xs focus:outline-none"
                                />
                                <button
                                  onClick={() => handleRejectDoc(d.id)}
                                  className="bg-destructive text-white rounded px-2 py-1 text-xs hover:bg-destructive/90"
                                >
                                  Submit
                                </button>
                                <button
                                  onClick={() => { setRejectingDocId(null); setRejectionReason(''); }}
                                  className="text-xs text-muted-foreground hover:underline"
                                >
                                  Cancel
                                </button>
                              </div>
                            ) : (
                              <>
                                <button
                                  onClick={() => handleVerifyDoc(d.id)}
                                  className="bg-emerald-600 text-white rounded px-2.5 py-1 text-xs font-medium hover:bg-emerald-700"
                                >
                                  Verify
                                </button>
                                <button
                                  onClick={() => setRejectingDocId(d.id)}
                                  className="bg-amber-600 text-white rounded px-2.5 py-1 text-xs font-medium hover:bg-amber-700"
                                >
                                  Reject
                                </button>
                              </>
                            )}
                          </>
                        )}
                        {canEdit && (
                          <button
                            onClick={() => setDocToDelete(d.id)}
                            className="text-destructive hover:underline text-xs font-medium"
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <ConfirmDialog
        open={!!docToDelete}
        onOpenChange={(open) => !open && setDocToDelete(null)}
        title="Delete Document?"
        description="Are you sure you want to delete this document?"
        onConfirm={() => { if (docToDelete) handleDeleteDoc(docToDelete); }}
        confirmText="Delete"
      />

      <ConfirmDialog
        open={studentToDelete}
        onOpenChange={setStudentToDelete}
        title="Delete Student?"
        description="Are you sure you want to delete this student record? This action cannot be fully undone."
        onConfirm={handleDeleteStudent}
        confirmText="Delete"
      />
    </div>
  );
}
