'use client';

import { useEffect, useState } from 'react';
import { aggregator, admissions, finance, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, StatusBadge } from '../rimit-shell';
import { can } from '@/lib/permissions';

interface DashboardData {
  universities: number;
  courses: number;
  students: number;
  enrollments: number;
  payments_collected: string;
  payments_pending: string;
  recent_enrollments: Array<{
    id: string;
    student_name: string;
    course_name: string;
    status: string;
    created_at: string;
  }>;
  recent_payments: Array<{
    id: string;
    student_name: string;
    amount_paid: string;
    status: string;
    created_at: string;
  }>;
  status_breakdown: Record<string, number>;
}

export function DashboardView({ profile }: { profile: UserProfile }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [unis, courses, students, enrollments, summary, payments] = await Promise.all([
          aggregator.listUniversities(),
          aggregator.listCourses(),
          admissions.listStudents(),
          admissions.listEnrollments(),
          can(profile.role, 'payment', 'read')
            ? finance.summary().catch(() => null)
            : Promise.resolve(null),
          can(profile.role, 'payment', 'read')
            ? finance.listPayments().catch(() => ({ results: [] }))
            : Promise.resolve({ results: [] }),
        ]);

        const status_breakdown: Record<string, number> = {};
        enrollments.results.forEach(e => {
          status_breakdown[e.status] = (status_breakdown[e.status] || 0) + 1;
        });

        setData({
          universities: unis.count,
          courses: courses.count,
          students: students.count,
          enrollments: enrollments.count,
          payments_collected: summary?.total_collected || '0',
          payments_pending: summary?.total_pending || '0',
          recent_enrollments: enrollments.results.slice(0, 5) as any,
          recent_payments: (payments as any).results.slice(0, 5) as any,
          status_breakdown,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    })();
  }, [profile.role]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;

  const roleLabel: Record<string, string> = {
    super_admin: 'Super Admin',
    academic_head: 'Academic Head',
    counselor: 'Counselor',
    finance: 'Finance Officer',
  };

  return (
    <div>
      <PageHeader
        title={`Welcome, ${profile.username}`}
        subtitle={`${roleLabel[profile.role]}${profile.sub_center_code ? ` · ${profile.sub_center_code}` : ''}`}
      />
      {!profile.sub_center_code && (profile.role === 'super_admin' || profile.role === 'academic_head') && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-2 rounded-md text-sm mb-6 flex items-center gap-2">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"></path></svg>
          You are viewing global aggregated data across all sub-centers.
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Universities" value={data.universities} accent="border-l-4 border-l-primary" />
        <KpiCard label="Courses" value={data.courses} accent="border-l-4 border-l-emerald-500" />
        <KpiCard label="Students" value={data.students} accent="border-l-4 border-l-amber-500" />
        <KpiCard label="Enrollments" value={data.enrollments} accent="border-l-4 border-l-cyan-500" />
      </div>

      {can(profile.role, 'payment', 'read') && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div className="bg-card border border-border rounded-lg p-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Total Collected</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">
              ₹{parseFloat(data.payments_collected || '0').toLocaleString('en-IN')}
            </p>
          </div>
          <div className="bg-card border border-border rounded-lg p-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wide">Pending Fees</p>
            <p className="text-2xl font-bold text-amber-600 mt-1">
              ₹{parseFloat(data.payments_pending || '0').toLocaleString('en-IN')}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="px-5 py-3 border-b border-border bg-muted/30">
            <h2 className="text-sm font-semibold">Live Activity Feed</h2>
          </div>
          <div className="divide-y divide-border">
            {(() => {
              const feed = [
                ...data.recent_enrollments.map(e => ({ type: 'enrollment', time: new Date(e.created_at).getTime(), data: e })),
                ...data.recent_payments.map(p => ({ type: 'payment', time: new Date(p.created_at).getTime(), data: p }))
              ].sort((a, b) => b.time - a.time).slice(0, 10);

              if (feed.length === 0) return <div className="px-5 py-8 text-sm text-muted-foreground text-center">No recent activity</div>;

              return feed.map((item, i) => (
                <div key={i} className="px-5 py-3 flex items-center justify-between hover:bg-muted/20">
                  <div className="min-w-0 flex-1 flex items-start gap-3">
                    <div className="mt-0.5">
                      {item.type === 'enrollment' ? (
                        <span className="w-2 h-2 rounded-full bg-cyan-500 inline-block" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                      )}
                    </div>
                    <div>
                      {item.type === 'enrollment' ? (
                        <>
                          <p className="text-sm font-medium text-foreground truncate">
                            New Enrollment: {(item.data as any).student_name}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">{(item.data as any).course_name}</p>
                        </>
                      ) : (
                        <>
                          <p className="text-sm font-medium text-foreground truncate">
                            Payment Received: ₹{parseFloat((item.data as any).amount_paid).toLocaleString('en-IN')}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">{(item.data as any).student_name}</p>
                        </>
                      )}
                      <p className="text-[10px] text-muted-foreground mt-0.5">{new Date(item.time).toLocaleString('en-IN')}</p>
                    </div>
                  </div>
                  <StatusBadge status={(item.data as any).status} />
                </div>
              ));
            })()}
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="px-5 py-3 border-b border-border bg-muted/30">
            <h2 className="text-sm font-semibold">Enrollment Status Breakdown</h2>
          </div>
          <div className="p-5 space-y-3">
            {Object.keys(data.status_breakdown).length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No data</p>
            ) : (
              Object.entries(data.status_breakdown).map(([status, count]) => {
                const max = Math.max(...Object.values(data.status_breakdown));
                const pct = max > 0 ? (count / max) * 100 : 0;
                return (
                  <div key={status}>
                    <div className="flex items-center justify-between mb-1">
                      <StatusBadge status={status} />
                      <span className="text-sm font-medium text-foreground">{count}</span>
                    </div>
                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function KpiCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div className={`bg-card border border-border rounded-lg p-5 ${accent}`}>
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-foreground mt-2">{value}</p>
    </div>
  );
}
