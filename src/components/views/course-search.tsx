'use client';

import { useEffect, useRef, useState } from 'react';
import { aggregator, admissions, rules, DEFAULT_PAGE_SIZE, type Course, type University, type IntakeSession, type Student, type UserProfile, type FeeStructure } from '@/lib/api';
import { can } from '@/lib/permissions';
import { PageHeader, LoadingState, ErrorState, EmptyState } from '../rimit-shell';
import { toast } from 'sonner';

export function CourseSearchView({ profile }: { profile: UserProfile }) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [universities, setUniversities] = useState<University[]>([]);
  const [sessions, setSessions] = useState<IntakeSession[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const requestIdRef = useRef(0);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [uniFilter, setUniFilter] = useState('');
  const [streams, setStreams] = useState<string[]>([]);
  const [maxDuration, setMaxDuration] = useState(48); // default max 4 years
  const [maxBudget, setMaxBudget] = useState('');

  // UI state
  const [expandedCourse, setExpandedCourse] = useState<string | null>(null);
  
  // Enroll Modal state
  const [enrollCourse, setEnrollCourse] = useState<Course | null>(null);
  const [enrollForm, setEnrollForm] = useState({ student: '', session: '' });
  const [validating, setValidating] = useState(false);
  const [enrolling, setEnrolling] = useState(false);

  // Commission breakdown state
  const [commissionBreakdown, setCommissionBreakdown] = useState<any | null>(null);
  const [fetchingCommission, setFetchingCommission] = useState(false);

  const handleShowCommissionBreakdown = async (courseId: string) => {
    setFetchingCommission(true);
    try {
      const data = await aggregator.getCourseCommission(courseId);
      setCommissionBreakdown(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to fetch commission breakdown');
    } finally {
      setFetchingCommission(false);
    }
  };

  const preflightResult = (enrollCourse && enrollForm.student && enrollForm.session)
    ? { valid: true, reason: '' }
    : null;

  const loadFilterData = async () => {
    try {
      const fetchAll = async <T,>(
        fetchPage: (page: number) => Promise<{ results: T[]; next: string | null }>,
        maxPages: number = 5
      ): Promise<T[]> => {
        const results: T[] = [];
        for (let p = 1; p <= maxPages; p++) {
          const data = await fetchPage(p);
          results.push(...(data.results || []));
          if (!data.next) break;
        }
        return results;
      };

      const [unis, sess, studs] = await Promise.all([
        fetchAll<University>((p) => aggregator.listUniversities({ is_active: 'true', page: String(p), page_size: '200' })),
        rules.listIntakeSessions({ is_active: 'true', page_size: '200' }),
        fetchAll<Student>((p) => admissions.listStudents({ is_active: 'true', page: String(p), page_size: '200' })),
      ]);

      setUniversities(unis);
      setSessions((sess as any).results || []);
      setStudents(studs);
    } catch (err) {
      console.error('Failed to load filter metadata', err);
    }
  };

  const loadCourses = async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (searchQuery) params.search = searchQuery;
      if (uniFilter) params.university = uniFilter;
      if (maxBudget) params.budget_max = maxBudget;

      // Fetch multiple backend pages (bounded) so client-side filters don't hide unseen results.
      const all: Course[] = [];
      for (let p = 1; p <= 5; p++) {
        const data = await aggregator.listCourses({ ...params, page: String(p), page_size: '200' });
        all.push(...(data.results || []));
        if (!data.next) break;
      }

      if (requestId !== requestIdRef.current) return;

      // Client-side filtering for streams and duration since backend doesn't support array filters for stream
      let filtered = all;
      if (streams.length > 0) {
        filtered = filtered.filter(c => streams.includes(c.stream));
      }
      filtered = filtered.filter(c => c.duration_months <= maxDuration);

      const total = filtered.length;
      const totalPages = Math.max(1, Math.ceil(total / DEFAULT_PAGE_SIZE));
      const safePage = Math.min(page, totalPages);
      if (safePage !== page) setPage(safePage);
      const start = (safePage - 1) * DEFAULT_PAGE_SIZE;
      const paged = filtered.slice(start, start + DEFAULT_PAGE_SIZE);

      setTotalCount(total);
      setCourses(paged);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search courses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadFilterData();
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadCourses();
  }, [searchQuery, uniFilter, streams, maxDuration, maxBudget, page]);

  const handleQuickEnroll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enrollCourse) return;
    setEnrolling(true);
    try {
      await admissions.createEnrollment({
        student: enrollForm.student,
        course: enrollCourse.id,
        session: enrollForm.session,
      });
      toast.success('Enrollment created successfully!');
      setEnrollCourse(null);
      setEnrollForm({ student: '', session: '' });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Enrollment failed');
    } finally {
      setEnrolling(false);
    }
  };

  const handleDownloadProspectus = async (course: Course) => {
    try {
      // 1) Try course-mapped prospectus
      let docs = await aggregator.listProspectus({ course: course.id, doc_type: 'prospectus', is_public: 'true', page_size: '1' });
      let doc = docs.results?.[0];

      // 2) Fallback: university-level prospectus
      if (!doc) {
        docs = await aggregator.listProspectus({ university: course.university, doc_type: 'prospectus', is_public: 'true', page_size: '1' });
        doc = docs.results?.[0];
      }

      if (!doc) {
        toast.error('No prospectus found for this course/university.');
        return;
      }

      const data = await aggregator.downloadDoc(doc.id);
      window.open(data.url, '_blank');
      toast.success('Opening prospectus download…');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to download prospectus');
    }
  };

  const toggleStream = (stream: string) => {
    setStreams(prev =>
      prev.includes(stream) ? prev.filter(s => s !== stream) : [...prev, stream]
    );
    setPage(1);
  };

  const getStreamBadgeColor = (stream: string) => {
    const colors: Record<string, string> = {
      Undergraduate: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      Postgraduate: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
      Diploma: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
      'Open Schooling': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
    };
    return colors[stream] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Course & Fee Search Engine"
        subtitle="Search and filter courses across all partner universities with real-time fee breakdown"
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Faceted Filters Sidebar */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-6 self-start">
          <h3 className="font-bold text-foreground text-sm uppercase tracking-wider border-b border-border pb-2">Filters</h3>
          
          {/* University Dropdown */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-muted-foreground">University</label>
            <select
              value={uniFilter}
              onChange={e => { setUniFilter(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All Universities</option>
              {universities.map(u => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </select>
          </div>

          {/* Stream Checkboxes */}
          <div className="space-y-2.5">
            <label className="block text-xs font-semibold text-muted-foreground">Course Stream</label>
            <div className="space-y-2">
              {['Undergraduate', 'Postgraduate', 'Diploma', 'Open Schooling'].map(stream => (
                <label key={stream} className="flex items-center gap-2.5 text-sm text-foreground cursor-pointer">
                  <input
                    type="checkbox"
                    checked={streams.includes(stream)}
                    onChange={() => toggleStream(stream)}
                    className="rounded border-input text-primary focus:ring-ring"
                  />
                  {stream}
                </label>
              ))}
            </div>
          </div>

          {/* Duration Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-semibold text-muted-foreground">
              <span>Max Duration</span>
              <span className="text-primary">{maxDuration} Months</span>
            </div>
            <input
              type="range"
              min="3"
              max="60"
              step="3"
              value={maxDuration}
              onChange={e => { setMaxDuration(Number(e.target.value)); setPage(1); }}
              className="w-full h-1.5 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground px-1">
              <span>3m</span>
              <span>24m</span>
              <span>48m</span>
              <span>60m</span>
            </div>
          </div>

          {/* Max Budget Input */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-muted-foreground">Max Budget (Total Fee, ₹)</label>
            <div className="relative">
              <span className="absolute left-3 top-2 text-muted-foreground text-sm">₹</span>
              <input
                type="number"
                placeholder="E.g., 100000"
                value={maxBudget}
                onChange={e => { setMaxBudget(e.target.value); setPage(1); }}
                className="w-full pl-7 pr-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring font-medium"
              />
            </div>
          </div>
        </div>

        {/* Results Pane */}
        <div className="lg:col-span-3 space-y-4">
          {/* Main Search Bar */}
          <div className="relative">
            <span className="absolute left-3.5 top-3 text-muted-foreground">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </span>
            <input
              type="text"
              placeholder="Search courses by name, keywords, eligibility requirements..."
              value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setPage(1); }}
              className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-border bg-card text-base shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {loading ? (
            <LoadingState />
          ) : error ? (
            <ErrorState message={error} />
          ) : totalCount === 0 ? (
            <EmptyState message="No courses match search criteria" />
          ) : (
            <div className="space-y-4">
              {courses.map(course => {
                const isExpanded = expandedCourse === course.id;
                return (
                  <div
                    key={course.id}
                    className="bg-card border border-border rounded-xl shadow-sm overflow-hidden hover:border-primary/45 transition"
                  >
                    <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="space-y-1.5 flex-1">
                        <div className="flex flex-wrap gap-2 items-center">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${getDocTypeLabelOrColor(course.stream)}`}>
                            {course.stream}
                          </span>
                          <span className="text-xs text-muted-foreground font-medium">
                            Duration: {course.duration_months} Months
                          </span>
                        </div>
                        <h4 className="font-bold text-foreground text-lg">{course.name}</h4>
                        <p className="text-xs text-muted-foreground">{course.university_name} ({course.university_state})</p>
                      </div>

                      <div className="flex items-center gap-6 justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0">
                        <div className="text-right">
                          <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wide">Total Course Fee</p>
                          <p className="text-xl font-extrabold text-primary">₹{course.total_fee?.toLocaleString('en-IN') || 0}</p>
                        </div>
                        
                        <div className="flex gap-2">
                          {can(profile.role, 'fee_structure', 'read') && (
                            <button
                              onClick={() => setExpandedCourse(isExpanded ? null : course.id)}
                              className="px-3.5 py-2 border border-border rounded-lg text-sm font-medium hover:bg-muted transition"
                            >
                              {isExpanded ? 'Hide Fees' : 'View Fees'}
                            </button>
                          )}
                          <button
                            onClick={() => handleDownloadProspectus(course)}
                            className="px-3.5 py-2 border border-border rounded-lg text-sm font-semibold text-primary hover:bg-primary/5 transition"
                          >
                            Download Prospectus
                          </button>
                          <button
                            onClick={() => {
                              setEnrollCourse(course);
                              setEnrollForm({ student: '', session: '' });
                            }}
                            className="bg-primary text-primary-foreground px-3.5 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition"
                          >
                            Quick Enroll
                          </button>
                        </div>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="bg-muted/30 border-t border-border px-5 py-4 space-y-3">
                        <div className="flex justify-between items-center">
                          <h5 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Fee Breakdown</h5>
                          <div className="flex items-center gap-4">
                            <button
                              onClick={() => handleShowCommissionBreakdown(course.id)}
                              disabled={fetchingCommission}
                              className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
                            >
                              {fetchingCommission ? 'Loading...' : 'Commission Breakdown'}
                            </button>
                            {course.eligibility_text && (
                              <p className="text-xs text-muted-foreground italic max-w-md truncate">
                                Eligibility: <span className="font-medium text-foreground">{course.eligibility_text}</span>
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="border-b border-border text-left">
                                <th className="py-2 text-muted-foreground font-medium">Fee Type</th>
                                <th className="py-2 text-muted-foreground font-medium text-right">Amount</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                              {course.fees && course.fees.length > 0 ? (
                                course.fees.map((fee: FeeStructure) => (
                                  <tr key={fee.id}>
                                    <td className="py-2.5 font-semibold capitalize text-foreground">{fee.fee_type.replace('_', ' ')}</td>
                                    <td className="py-2.5 font-bold text-foreground text-right">₹{parseFloat(fee.amount).toLocaleString('en-IN')}</td>
                                  </tr>
                                ))
                              ) : (
                                <tr>
                                  <td colSpan={2} className="py-4 text-center text-muted-foreground">No active fee structure defined.</td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
              <div className="flex items-center justify-between py-2">
                <span className="text-xs text-muted-foreground">
                  Page {page} of {Math.max(1, Math.ceil(totalCount / DEFAULT_PAGE_SIZE))} (Total {totalCount} records)
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
                    disabled={page >= Math.ceil(totalCount / DEFAULT_PAGE_SIZE)}
                    className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Enroll Modal */}
      {enrollCourse && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card w-full max-w-md rounded-xl shadow-lg border border-border overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-lg">Quick Enroll Candidate</h3>
                <p className="text-xs text-muted-foreground truncate max-w-[320px]">{enrollCourse.name}</p>
              </div>
              <button
                onClick={() => {
                  setEnrollCourse(null);
                  setEnrollForm({ student: '', session: '' });
                }}
                className="text-muted-foreground hover:text-foreground"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
            </div>

            <form onSubmit={handleQuickEnroll} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1">Select Candidate (Student) *</label>
                <select
                  value={enrollForm.student}
                  onChange={e => setEnrollForm(prev => ({ ...prev, student: e.target.value }))}
                  required
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">Select Candidate</option>
                  {students.map(s => (
                    <option key={s.id} value={s.id}>{s.full_name} ({s.primary_phone})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1">Select Intake Session *</label>
                <select
                  value={enrollForm.session}
                  onChange={e => setEnrollForm(prev => ({ ...prev, session: e.target.value }))}
                  required
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">Select Session</option>
                  {sessions.map(s => (
                    <option key={s.id} value={s.id}>{s.session_name}</option>
                  ))}
                </select>
              </div>

              {/* Preflight Validation Matrix Feedback */}
              {validating ? (
                <div className="bg-muted/50 rounded-lg p-3 text-xs text-muted-foreground animate-pulse">
                  Validating candidate admission criteria & session eligibility...
                </div>
              ) : preflightResult ? (
                <div className={`p-3 rounded-lg text-xs font-medium border ${
                  preflightResult.valid 
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-300 dark:border-emerald-900/30' 
                    : 'bg-red-50 text-red-800 border-red-200 dark:bg-red-950/20 dark:text-red-300 dark:border-red-900/30'
                }`}>
                  <div className="font-bold mb-0.5">{preflightResult.valid ? '✓ Candidate Eligible' : '✕ Validation Error'}</div>
                  <div>{preflightResult.reason || (preflightResult.valid ? 'Pre-flight checks passed successfully.' : 'Eligibility matrix verification failed.')}</div>
                </div>
              ) : null}

              <div className="pt-4 flex justify-end gap-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => {
                    setEnrollCourse(null);
                    setEnrollForm({ student: '', session: '' });
                  }}
                  className="px-4 py-2 text-sm font-medium rounded-md hover:bg-muted text-foreground"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={enrolling || validating || !enrollForm.student || !enrollForm.session || !!(preflightResult && !preflightResult.valid)}
                  className="px-4 py-2 text-sm font-semibold rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition"
                >
                  {enrolling ? 'Enrolling...' : 'Submit Application'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Commission Breakdown Modal */}
      {commissionBreakdown && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card w-full max-w-md rounded-xl shadow-lg border border-border overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-lg text-foreground">Commission Breakdown</h3>
                <p className="text-xs text-muted-foreground truncate max-w-[320px]">{commissionBreakdown.course_name}</p>
              </div>
              <button
                onClick={() => setCommissionBreakdown(null)}
                className="text-muted-foreground hover:text-foreground"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">University</span>
                  <span className="font-medium text-foreground">{commissionBreakdown.university_name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Total Course Fee</span>
                  <span className="font-semibold text-foreground">₹{parseFloat(commissionBreakdown.total_course_fee).toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">University Share %</span>
                  <span className="font-medium text-foreground">{parseFloat(commissionBreakdown.university_share_percent).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between text-sm pl-4 border-l-2 border-muted">
                  <span className="text-xs text-muted-foreground">Default Share %</span>
                  <span className="text-xs font-medium text-foreground">{parseFloat(commissionBreakdown.default_university_share_percent).toFixed(2)}%</span>
                </div>
                {commissionBreakdown.course_specific_university_share_percent !== null && (
                  <div className="flex justify-between text-sm pl-4 border-l-2 border-muted">
                    <span className="text-xs text-muted-foreground">Course Override %</span>
                    <span className="text-xs font-medium text-foreground">{parseFloat(commissionBreakdown.course_specific_university_share_percent).toFixed(2)}%</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">University Share (Amt)</span>
                  <span className="font-medium text-foreground">₹{parseFloat(commissionBreakdown.university_share).toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between text-sm border-t border-border pt-2">
                  <span className="text-muted-foreground font-semibold">Gross Commission Pool</span>
                  <span className="font-semibold text-foreground">₹{parseFloat(commissionBreakdown.gross_commission_pool).toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Sub-center Share %</span>
                  <span className="font-medium text-foreground">{parseFloat(commissionBreakdown.sub_center_commission_percent).toFixed(2)}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Sub-center Commission</span>
                  <span className="font-medium text-emerald-600 font-bold">₹{parseFloat(commissionBreakdown.sub_center_commission).toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">RIMIT Commission</span>
                  <span className="font-medium text-primary">₹{parseFloat(commissionBreakdown.rimit_commission).toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between text-sm border-t-2 border-double border-border pt-3 mt-3">
                  <span className="font-bold text-foreground">Net Payable to Gateway</span>
                  <span className="text-lg font-bold text-primary">₹{parseFloat(commissionBreakdown.net_payable).toLocaleString('en-IN')}</span>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setCommissionBreakdown(null)}
                  className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Inline helper for course list stream badge color
function getDocTypeLabelOrColor(stream: string) {
  const colors: Record<string, string> = {
    Undergraduate: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    Postgraduate: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
    Diploma: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
    'Open Schooling': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
  };
  return colors[stream] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
}
