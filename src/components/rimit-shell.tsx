'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  auth, aggregator, admissions, partners, rules, finance,
  type UserProfile, type University, type Course, type Student,
  type Enrollment, type IntakeSession, type SubCenter, type PaymentLedger,
} from '@/lib/api';

type View = 'dashboard' | 'universities' | 'students' | 'enrollments' | 'sessions' | 'payments';

interface AppShellProps {
  profile: UserProfile;
  onLogout: () => void;
}

export function useRimitData(profile: UserProfile | null) {
  const [view, setView] = useState<View>('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return { view, setView, loading, setLoading, error, setError };
}

// ──────────────── Login Form ────────────────
export function LoginForm({ onLogin }: { onLogin: (profile: UserProfile) => void }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { token } = await auth.login(username, password);
      localStorage.setItem('rimit_token', token);
      const profile = await auth.profile();
      onLogin(profile);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-3 mb-3">
            <div className="w-10 h-1 bg-primary rounded-full" />
            <span className="text-xs font-medium tracking-[0.3em] text-muted-foreground uppercase">
              RIMIT Education
            </span>
          </div>
          <h1 className="text-3xl font-bold text-foreground">B2B Aggregator Portal</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Unified University Aggregator &amp; Centralized Admission Management
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-card rounded-lg border border-border shadow-sm p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              required
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              required
            />
          </div>

          {error && (
            <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md p-3">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-primary-foreground rounded-md py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition"
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>

          <div className="pt-3 mt-3 border-t border-border text-xs text-muted-foreground space-y-1">
            <p className="font-semibold text-foreground">Demo credentials:</p>
            <p>Super Admin: <code className="bg-muted px-1.5 py-0.5 rounded">admin / admin123</code></p>
            <p>Academic Head: <code className="bg-muted px-1.5 py-0.5 rounded">academic_head / ah123</code></p>
            <p>Counselor: <code className="bg-muted px-1.5 py-0.5 rounded">counselor_kochi / coun123</code></p>
            <p>Finance: <code className="bg-muted px-1.5 py-0.5 rounded">finance_kochi / fin123</code></p>
          </div>
        </form>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          RIMIT Educational Charitable Trust · SPES Education
        </p>
      </div>
    </div>
  );
}

// ──────────────── Sidebar ────────────────
const NAV_ITEMS: { id: View; label: string; icon: string; roles: string[] }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0h6', roles: ['super_admin', 'academic_head', 'counselor', 'finance'] },
  { id: 'universities', label: 'Universities', icon: 'M12 14l9-5-9-5-9 5 9 5z M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z', roles: ['super_admin', 'academic_head', 'counselor', 'finance'] },
  { id: 'students', label: 'Students', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z', roles: ['super_admin', 'academic_head', 'counselor', 'finance'] },
  { id: 'enrollments', label: 'Enrollments', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', roles: ['super_admin', 'academic_head', 'counselor'] },
  { id: 'sessions', label: 'Intake Sessions', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z', roles: ['super_admin', 'academic_head', 'counselor'] },
  { id: 'payments', label: 'Payments', icon: 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z', roles: ['super_admin', 'academic_head', 'finance'] },
];

export function Sidebar({ profile, view, setView, onLogout }: {
  profile: UserProfile;
  view: View;
  setView: (v: View) => void;
  onLogout: () => void;
}) {
  const roleLabel: Record<string, string> = {
    super_admin: 'Super Admin',
    academic_head: 'Academic Head',
    counselor: 'Counselor',
    finance: 'Finance Officer',
  };
  const items = NAV_ITEMS.filter(i => i.roles.includes(profile.role));

  return (
    <aside className="w-60 bg-sidebar border-r border-sidebar-border flex flex-col h-screen sticky top-0">
      <div className="p-5 border-b border-sidebar-border">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-1.5 h-6 bg-primary rounded-sm" />
          <span className="text-sm font-bold tracking-tight">RIMIT</span>
        </div>
        <p className="text-xs text-muted-foreground">B2B Aggregator Portal</p>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {items.map(item => (
          <button
            key={item.id}
            onClick={() => setView(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition ${
              view === item.id
                ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                : 'text-sidebar-foreground hover:bg-sidebar-accent'
            }`}
          >
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
            </svg>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="p-3 border-t border-sidebar-border">
        <div className="px-3 py-2 mb-2">
          <p className="text-sm font-medium text-foreground truncate">{profile.username}</p>
          <p className="text-xs text-muted-foreground">{roleLabel[profile.role]}</p>
          {profile.sub_center_code && (
            <p className="text-xs text-muted-foreground mt-0.5">{profile.sub_center_code}</p>
          )}
        </div>
        <button
          onClick={onLogout}
          className="w-full text-left px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-sidebar-accent hover:text-foreground transition"
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
}

// ──────────────── Status Badge ────────────────
export function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    'Applied': 'bg-blue-50 text-blue-700 border-blue-200',
    'Document Verified': 'bg-cyan-50 text-cyan-700 border-cyan-200',
    'Fee Pending': 'bg-amber-50 text-amber-700 border-amber-200',
    'Fee Paid': 'bg-emerald-50 text-emerald-700 border-emerald-200',
    'Enrolled': 'bg-green-50 text-green-700 border-green-200',
    'Enrollment Generated': 'bg-green-100 text-green-800 border-green-300',
    'Cancelled': 'bg-red-50 text-red-700 border-red-200',
    'captured': 'bg-green-50 text-green-700 border-green-200',
    'pending': 'bg-amber-50 text-amber-700 border-amber-200',
    'failed': 'bg-red-50 text-red-700 border-red-200',
    'active': 'bg-green-50 text-green-700 border-green-200',
    'suspended': 'bg-amber-50 text-amber-700 border-amber-200',
    'terminated': 'bg-red-50 text-red-700 border-red-200',
  };
  const cls = colors[status] || 'bg-slate-50 text-slate-700 border-slate-200';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${cls}`}>
      {status}
    </span>
  );
}

// ──────────────── Page Header ────────────────
export function PageHeader({ title, subtitle, action }: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between mb-6 pb-4 border-b border-border">
      <div>
        <h1 className="text-2xl font-bold text-foreground">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

// ──────────────── Loading + Empty States ────────────────
export function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-destructive/10 border border-destructive/20 rounded-md p-4 text-sm text-destructive">
      {message}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-12 text-sm text-muted-foreground">
      {message}
    </div>
  );
}

// Re-export types for convenience
export type { View, UserProfile, University, Course, Student, Enrollment, IntakeSession, SubCenter, PaymentLedger };
