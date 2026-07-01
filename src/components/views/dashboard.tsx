'use client';

import { useEffect, useState } from 'react';
import { aggregator, admissions, finance, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, StatusBadge } from '../rimit-shell';

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
        const [unis, courses, students, enrollments, summary] = await Promise.all([
          aggregator.listUniversities(),
          aggregator.listCourses(),
          admissions.listStudents(),
          admissions.listEnrollments(),
          (profile.role === 'finance' || profile.role === 'super_admin' || profile.role === 'academic_head')
            ? finance.summary().catch(() => null)
            : Promise.resolve(null),
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
          recent_enrollments: enrollments.results.slice(0, 5),
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <KpiCard label="Universities" value={data.universities} accent="border-l-4 border-l-primary" />
        <KpiCard label="Courses" value={data.courses} accent="border-l-4 border-l-emerald-500" />
        <KpiCard label="Students" value={data.students} accent="border-l-4 border-l-amber-500" />
        <KpiCard label="Enrollments" value={data.enrollments} accent="border-l-4 border-l-cyan-500" />
      </div>

      {(profile.role === 'finance' || profile.role === 'super_admin') && (
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
            <h2 className="text-sm font-semibold">Recent Enrollments</h2>
          </div>
          <div className="divide-y divide-border">
            {data.recent_enrollments.length === 0 ? (
              <div className="px-5 py-8 text-sm text-muted-foreground text-center">No enrollments yet</div>
            ) : (
              data.recent_enrollments.map(e => (
                <div key={e.id} className="px-5 py-3 flex items-center justify-between hover:bg-muted/20">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-foreground truncate">{e.student_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{e.course_name}</p>
                  </div>
                  <StatusBadge status={e.status} />
                </div>
              ))
            )}
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
