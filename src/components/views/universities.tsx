'use client';

import { useEffect, useState } from 'react';
import { aggregator, DEFAULT_PAGE_SIZE, withPaging, hasNextPage, hasPrevPage, type University, type Course, type UserProfile, type FeeStructure } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, ConfirmDialog } from '../rimit-shell';
import { usePermissions } from '@/lib/permissions';

import { toast } from 'sonner';

export function UniversitiesView({ profile }: { profile: UserProfile }) {
  const [universities, setUniversities] = useState<University[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<University | null>(null);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [canNext, setCanNext] = useState(false);
  const [canPrev, setCanPrev] = useState(false);

  // Add University form state
  const [showAddUni, setShowAddUni] = useState(false);
  const [editingUni, setEditingUni] = useState<University | null>(null);
  const [uniForm, setUniForm] = useState({
    name: '',
    state: '',
    accreditation: '',
    description: '',
    default_university_share_percent: '',
  });
  const [submittingUni, setSubmittingUni] = useState(false);

  const { canCreate, canUpdate, canDelete } = usePermissions(profile.role, 'university');

  const load = async (targetPage: number = page) => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (stateFilter) params.state = stateFilter;
      const data = await aggregator.listUniversities(withPaging(params, { page: targetPage, pageSize: DEFAULT_PAGE_SIZE }));
      setUniversities(data.results);
      setTotalCount(data.count || 0);
      setCanNext(hasNextPage(data));
      setCanPrev(hasPrevPage(data));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load universities');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page]); // eslint-disable-line

  const triggerSearch = () => {
    if (page === 1) load(1);
    else setPage(1);
  };

  const handleCreateUni = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingUni(true);
    setError(null);
    try {
      if (editingUni) {
        await aggregator.updateUniversity(editingUni.id, uniForm);
        toast.success('University updated successfully');
      } else {
        await aggregator.createUniversity(uniForm);
        toast.success('University created successfully');
      }
      setShowAddUni(false);
      setEditingUni(null);
      setUniForm({ name: '', state: '', accreditation: '', description: '', default_university_share_percent: '' });
      load();
    } catch (err) {
      let errorMsg = `Failed to ${editingUni ? 'update' : 'create'} university`;
      if (err instanceof Error) {
        try {
          const parsed = JSON.parse(err.message);
          if (parsed && typeof parsed === 'object') {
            const firstKey = Object.keys(parsed)[0];
            const errorList = parsed[firstKey];
            if (Array.isArray(errorList) && errorList.length > 0) {
              const rawMsg = errorList[0];
              errorMsg = rawMsg.charAt(0).toUpperCase() + rawMsg.slice(1);
            } else if (typeof errorList === 'string') {
              errorMsg = errorList.charAt(0).toUpperCase() + errorList.slice(1);
            } else if (parsed.detail) {
              errorMsg = parsed.detail;
            }
          }
        } catch (e) {
          if (err.message && !err.message.includes('HTTP')) {
            errorMsg = err.message;
          }
        }
      }
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setSubmittingUni(false);
    }
  };

  const handleEditClick = (u: University) => {
    setEditingUni(u);
    setUniForm({
      name: u.name,
      state: u.state,
      accreditation: u.accreditation || '',
      description: u.description || '',
      default_university_share_percent: (u.default_university_share_percent ?? '').toString(),
    });
    setShowAddUni(true);
  };

  if (loading) return <LoadingState />;
  if (error && !showAddUni) return <ErrorState message={error} />;

  if (selected) {
    return (
      <UniversityDetail
        university={selected}
        profile={profile}
        onBack={() => {
          setSelected(null);
          load();
        }}
      />
    );
  }

  if (showAddUni) {
    return (
      <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div className="bg-card w-full max-w-md rounded-xl shadow-lg border border-border overflow-hidden">
          <div className="px-6 py-4 border-b border-border flex justify-between items-center">
            <h3 className="font-semibold text-lg">{editingUni ? 'Edit University' : 'Add New University'}</h3>
            <button onClick={() => { setShowAddUni(false); setEditingUni(null); }} className="text-muted-foreground hover:text-foreground">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>
          <form onSubmit={handleCreateUni} className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">University Name *</label>
              <input
                type="text"
                value={uniForm.name}
                onChange={e => setUniForm(prev => ({ ...prev, name: e.target.value }))}
                required
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">State *</label>
                <input
                  type="text"
                  value={uniForm.state}
                  onChange={e => setUniForm(prev => ({ ...prev, state: e.target.value }))}
                  required
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Accreditation</label>
                <input
                  type="text"
                  value={uniForm.accreditation}
                  onChange={e => setUniForm(prev => ({ ...prev, accreditation: e.target.value }))}
                  placeholder="E.g., NAAC A++"
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Description</label>
              <textarea
                value={uniForm.description}
                onChange={e => setUniForm(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Default University Share % (of Total Fee)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={uniForm.default_university_share_percent}
                onChange={e => setUniForm(prev => ({ ...prev, default_university_share_percent: e.target.value }))}
                placeholder="E.g., 50.00"
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
              <p className="text-[11px] text-muted-foreground mt-1">University’s default share of Total Fee (0–100%). Courses may override.</p>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => { setShowAddUni(false); setEditingUni(null); }}
                className="px-4 py-2 text-sm font-medium rounded-md hover:bg-muted text-foreground"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingUni || !uniForm.name || !uniForm.state}
                className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {submittingUni ? 'Saving...' : editingUni ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Universities"
        subtitle="Manage academic partners and course providers"
        action={
          canCreate && (
            <button
              onClick={() => {
                setEditingUni(null);
                setUniForm({ name: '', state: '', accreditation: '', description: '' });
                setShowAddUni(true);
              }}
              className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
            >
              + Add University
            </button>
          )
        }
      />

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search by name, accreditation…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && triggerSearch()}
          className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <input
          type="text"
          placeholder="State"
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && triggerSearch()}
          className="w-40 px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          onClick={triggerSearch}
          className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          Search
        </button>
      </div>

      {universities.length === 0 ? (
        <EmptyState message="No universities found" />
      ) : (
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {universities.map(u => (
              <div
                key={u.id}
                className="bg-card rounded-xl border p-5 cursor-pointer transition-all hover:shadow-md hover:border-primary/50 border-border flex flex-col justify-between"
              >
                <div onClick={() => setSelected(u)} className="flex-1 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-2 gap-4">
                      <h3 className="font-semibold text-lg text-foreground leading-tight flex-1 min-w-0 break-words">{u.name}</h3>
                      {canUpdate ? (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleEditClick(u); }}
                          className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-md transition-colors flex-shrink-0"
                          title="Edit University"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                        </button>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap gap-2 items-center mb-3">
                      <span className="text-xs bg-muted px-2 py-0.5 rounded text-muted-foreground font-medium break-all">
                        {u.state}
                      </span>
                      {u.accreditation && (
                        <span className="text-xs text-muted-foreground font-medium bg-muted/50 px-2 py-0.5 rounded border border-border/30 break-all">
                          {u.accreditation}
                        </span>
                      )}
                    </div>
                  </div>
                  {u.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2 mt-auto">{u.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>

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
        </div>
      )}
    </div>
  );
}

function UniversityDetail({ university, profile, onBack }: { university: University; profile: UserProfile; onBack: () => void }) {
  const [detail, setDetail] = useState<University | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add Course form state
  const [showAddCourse, setShowAddCourse] = useState(false);
  const [courseForm, setCourseForm] = useState({
    name: '',
    stream: 'Undergraduate',
    duration_months: 36,
    eligibility_text: '',
    university_share_percent: '',
  });
  const [submittingCourse, setSubmittingCourse] = useState(false);

  // Add Fee form state
  const [activeCourseId, setActiveCourseId] = useState<string | null>(null);
  const [feeForm, setFeeForm] = useState({
    fee_type: 'tuition',
    amount: '',
  });
  const [submittingFee, setSubmittingFee] = useState(false);

  const [uniToDelete, setUniToDelete] = useState<boolean>(false);
  const [courseToDelete, setCourseToDelete] = useState<string | null>(null);
  const [feeToDelete, setFeeToDelete] = useState<string | null>(null);

  const { canCreate, canUpdate, canDelete } = usePermissions(profile.role, 'course');

  const loadDetail = async () => {
    setLoading(true);
    try {
      const d = await aggregator.getUniversity(university.id);
      setDetail(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDetail(); }, [university.id]); // eslint-disable-line

  const handleDeleteUni = async () => {
    try {
      await aggregator.deleteUniversity(university.id);
      onBack();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete university');
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingCourse(true);
    setError(null);

    const cleanedName = courseForm.name.trim().toLowerCase();
    const isDuplicate = detail?.courses?.some(
      (c: any) => c.name.trim().toLowerCase() === cleanedName
    );
    if (isDuplicate) {
      setError("A course with this name already exists under this university.");
      setSubmittingCourse(false);
      return;
    }

    try {
      await aggregator.createCourse({
        university: university.id,
        name: courseForm.name,
        stream: courseForm.stream,
        duration_months: Number(courseForm.duration_months),
        eligibility_text: courseForm.eligibility_text,
        university_share_percent: courseForm.university_share_percent ? Number(courseForm.university_share_percent) : undefined,
        is_active: true,
      });
      setCourseForm({ name: '', stream: 'Undergraduate', duration_months: 36, eligibility_text: '', university_share_percent: '' });
      setShowAddCourse(false);
      loadDetail();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create course');
    } finally {
      setSubmittingCourse(false);
    }
  };

  const handleDeleteCourse = async (courseId: string) => {
    try {
      await aggregator.deleteCourse(courseId);
      loadDetail();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete course');
    }
  };

  const handleCreateFee = async (e: React.FormEvent, courseId: string) => {
    e.preventDefault();
    setSubmittingFee(true);
    setError(null);
    try {
      await aggregator.createFee({
        course: courseId,
        fee_type: feeForm.fee_type,
        amount: feeForm.amount,
        currency: 'INR',
        is_active: true,
      });
      setFeeForm({ fee_type: 'tuition', amount: '' });
      setActiveCourseId(null);
      loadDetail();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create fee structure');
    } finally {
      setSubmittingFee(false);
    }
  };

  const handleDeleteFee = async (feeId: string) => {
    try {
      await aggregator.deleteFee(feeId);
      loadDetail();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete fee item');
    }
  };

  if (loading || !detail) return <LoadingState />;

  return (
    <div>
      <div className="flex justify-end items-center mb-4">
        {canDelete && (
          <button
            onClick={() => setUniToDelete(true)}
            className="bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive hover:text-destructive-foreground px-3 py-1.5 rounded text-xs font-semibold"
          >
            Delete University
          </button>
        )}
      </div>

        <PageHeader 
          title={detail.name} 
          subtitle={`${detail.state} · ${detail.accreditation || 'Not accredited'}`} 
          breadcrumbs={[{ label: 'Universities', onClick: onBack }, { label: detail.name }]}
        />

        {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm p-3 rounded-md mb-4">
          {error}
        </div>
      )}

      {detail.description && <p className="text-sm text-muted-foreground mb-6">{detail.description}</p>}

      {/* Add Course Overlay */}
      {showAddCourse && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-card border border-border w-full max-w-sm rounded-lg shadow-lg p-6 space-y-4">
            <h3 className="text-base font-bold text-foreground">Add Course to {detail.name}</h3>
            <form onSubmit={handleCreateCourse} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Course Name *</label>
                <input
                  type="text"
                  value={courseForm.name}
                  onChange={e => setCourseForm(prev => ({ ...prev, name: e.target.value }))}
                  required
                  placeholder="E.g., Bachelor of Technology"
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Stream *</label>
                  <select
                    value={courseForm.stream}
                    onChange={e => setCourseForm(prev => ({ ...prev, stream: e.target.value }))}
                    required
                    className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm focus:outline-none"
                  >
                    <option value="Undergraduate">Undergraduate</option>
                    <option value="Postgraduate">Postgraduate</option>
                    <option value="Diploma">Diploma</option>
                    <option value="Open Schooling">Open Schooling</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Duration (Months) *</label>
                  <input
                    type="number"
                    value={courseForm.duration_months}
                    onChange={e => setCourseForm(prev => ({ ...prev, duration_months: Number(e.target.value) }))}
                    required
                    className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Eligibility Text</label>
                <input
                  type="text"
                  value={courseForm.eligibility_text}
                  onChange={e => setCourseForm(prev => ({ ...prev, eligibility_text: e.target.value }))}
                  placeholder="10+2 with Physics, Chem, Math"
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">University Share % Override</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={courseForm.university_share_percent}
                  onChange={e => setCourseForm(prev => ({ ...prev, university_share_percent: e.target.value }))}
                  placeholder="Leave blank to inherit university default"
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm"
                />
              </div>
              <div className="flex gap-2 pt-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowAddCourse(false)}
                  className="px-3 py-1.5 border border-border rounded-md text-xs font-medium hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCourse}
                  className="bg-primary text-primary-foreground rounded-md px-4 py-1.5 text-xs font-medium hover:bg-primary/90 disabled:opacity-50"
                >
                  {submittingCourse ? 'Adding...' : 'Add Course'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold">Courses ({detail.courses?.length ?? 0})</h2>
        {canCreate && (
          <button
            onClick={() => setShowAddCourse(true)}
            className="text-xs bg-primary text-primary-foreground rounded-md px-3 py-1.5 font-medium hover:bg-primary/90"
          >
            + Add Course
          </button>
        )}
      </div>

      {detail.courses && detail.courses.length > 0 ? (
        <div className="space-y-4 mb-8">
          {detail.courses.map(c => (
            <div key={c.id} className="bg-card border border-border rounded-lg p-5">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-foreground text-sm">{c.name}</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    {c.stream} · {c.duration_months} months
                  </p>
                  {c.eligibility_text && (
                    <p className="text-xs text-muted-foreground mt-1">Eligibility: {c.eligibility_text}</p>
                  )}
                </div>

                <div className="text-right space-y-2">
                  {c.fees && c.fees.length > 0 ? (
                    <div className="space-y-1">
                      {c.fees.map(f => (
                        <div key={f.id} className="text-xs flex items-center justify-end gap-2">
                          <span className="text-muted-foreground">{f.fee_type}:</span>{' '}
                          <span className="font-semibold text-foreground">₹{parseFloat(f.amount).toLocaleString('en-IN')}</span>
                          {canCreate && (
                            <button
                              onClick={() => setFeeToDelete(f.id)}
                              className="text-destructive hover:underline font-bold"
                              title="Delete Fee Item"
                            >
                              ✕
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">No fees configured</p>
                  )}

                  {canDelete && (
                    <div className="flex gap-2 justify-end">
                      {activeCourseId === c.id ? (
                        <form onSubmit={(e) => handleCreateFee(e, c.id)} className="bg-muted p-2 rounded-md space-y-2 text-left w-48">
                          <select
                            value={feeForm.fee_type}
                            onChange={e => setFeeForm(prev => ({ ...prev, fee_type: e.target.value }))}
                            required
                            className="w-full px-2 py-1 text-xs border rounded bg-background focus:outline-none"
                          >
                            <option value="admission">Admission Fee</option>
                            <option value="tuition">Tuition Fee</option>
                            <option value="exam">Examination Fee</option>
                            <option value="library">Library Fee</option>
                            <option value="lab">Lab Fee</option>
                            <option value="other">Other</option>
                          </select>
                          <input
                            type="number"
                            required
                            placeholder="Amount (₹)"
                            value={feeForm.amount}
                            onChange={e => setFeeForm(prev => ({ ...prev, amount: e.target.value }))}
                            className="w-full px-2 py-1 text-xs border rounded bg-background"
                          />
                          <div className="flex gap-1 justify-end">
                            <button
                              type="button"
                              onClick={() => setActiveCourseId(null)}
                              className="text-[10px] border px-2 py-0.5 rounded bg-background"
                            >
                              Cancel
                            </button>
                            <button
                              type="submit"
                              disabled={submittingFee}
                              className="text-[10px] bg-primary text-primary-foreground px-2 py-0.5 rounded"
                            >
                              Add
                            </button>
                          </div>
                        </form>
                      ) : (
                        <button
                          onClick={() => {
                            setActiveCourseId(c.id);
                            setFeeForm({ fee_type: '', amount: '' });
                          }}
                          className="text-[11px] text-primary hover:underline font-semibold"
                        >
                          + Add Fee
                        </button>
                      )}

                      <button
                        onClick={() => setCourseToDelete(c.id)}
                        className="text-[11px] text-destructive hover:underline font-semibold ml-2"
                      >
                        Delete Course
                      </button>
                    </div>
                  )}
                </div>
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

      <ConfirmDialog
        open={uniToDelete}
        onOpenChange={setUniToDelete}
        title="Delete University?"
        description="Are you sure you want to delete this university? All courses and fees linked to it will also be deleted."
        onConfirm={handleDeleteUni}
        confirmText="Delete"
      />
      <ConfirmDialog
        open={!!courseToDelete}
        onOpenChange={(open) => !open && setCourseToDelete(null)}
        title="Delete Course?"
        description="Are you sure you want to delete this course?"
        onConfirm={() => { if (courseToDelete) handleDeleteCourse(courseToDelete); }}
        confirmText="Delete"
      />
      <ConfirmDialog
        open={!!feeToDelete}
        onOpenChange={(open) => !open && setFeeToDelete(null)}
        title="Delete Fee?"
        description="Are you sure you want to delete this fee item?"
        onConfirm={() => { if (feeToDelete) handleDeleteFee(feeToDelete); }}
        confirmText="Delete"
      />
    </div>
  );
}

