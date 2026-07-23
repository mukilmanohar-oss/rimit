'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import {
  auth, aggregator, admissions, partners, rules, finance,
  type UserProfile, type University, type Course, type Student,
  type Enrollment, type IntakeSession, type SubCenter, type PaymentLedger,
  type RuleConfiguration, type SystemUser, type StudentDoc, type StudentAcademicHistory,
  type LeadIngestionLog, type UniversityDoc,
} from '@/lib/api';

const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

type View = 'dashboard' | 'universities' | 'course-search' | 'prospectus' | 'leads' | 'leads-create' | 'students' | 'enrollments' | 'sessions' | 'payments' | 'subcenters' | 'users' | 'tickets' | 'notification-logs' | 'lead-monitor' | 'checkout' | 'change-password';

interface AppShellProps {
  profile: UserProfile;
  onLogout: () => void;
}

export function useRimitData(profile: UserProfile | null) {
  const [view, setView] = useState<View>('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    let timeout: NodeJS.Timeout;
    const resetTimer = () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        auth.logout();
        router.push('/login?expired=1');
      }, INACTIVITY_TIMEOUT_MS);
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(e => document.addEventListener(e, resetTimer));
    resetTimer();

    return () => {
      clearTimeout(timeout);
      events.forEach(e => document.removeEventListener(e, resetTimer));
    };
  }, [router]);

  return { view, setView, loading, setLoading, error, setError };
}

// ──────────────── Login Form ────────────────
export function LoginForm({ onLogin }: { onLogin: (profile: UserProfile) => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const form = e.target as HTMLFormElement;
      const otpInput = form.elements.namedItem('otp') as HTMLInputElement;
      const otp = otpInput ? otpInput.value : '123456';
      
      const { token } = await auth.login(username, password, otp);
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
          <div className="space-y-2" hidden>
            <label className="text-sm font-medium text-foreground">MFA OTP (Gap 11 Simulated)</label>
            <input
              type="text"
              name="otp"
              defaultValue="123456"
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

          {/* <div className="pt-3 mt-3 border-t border-border text-xs text-muted-foreground space-y-1">
            <p className="font-semibold text-foreground">Demo credentials:</p>
            <p>Super Admin: <code className="bg-muted px-1.5 py-0.5 rounded">admin / admin123</code></p>
            <p>Academic Head: <code className="bg-muted px-1.5 py-0.5 rounded">academic_head / ah123</code></p>
            <p>Counselor: <code className="bg-muted px-1.5 py-0.5 rounded">counselor_kochi / coun123</code></p>
            <p>Finance: <code className="bg-muted px-1.5 py-0.5 rounded">finance_kochi / fin123</code></p>
          </div> */}
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
  { id: 'course-search', label: 'Course Search', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z', roles: ['super_admin', 'academic_head', 'counselor', 'finance', 'subcenter'] },
  { id: 'prospectus', label: 'Prospectus Library', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253', roles: ['super_admin', 'academic_head', 'counselor', 'finance', 'subcenter'] },
  { id: 'leads-create', label: 'Lead Generator', icon: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z', roles: ['super_admin', 'academic_head', 'counselor'] },
  { id: 'leads', label: 'Leads Directory', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z', roles: ['super_admin', 'academic_head', 'counselor', 'subcenter'] },
  { id: 'students', label: 'Students', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z', roles: ['super_admin', 'academic_head', 'counselor', 'finance', 'subcenter'] },
  { id: 'enrollments', label: 'Enrollments', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', roles: ['super_admin', 'academic_head', 'counselor', 'subcenter'] },
  { id: 'sessions', label: 'Intake Sessions', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z', roles: ['super_admin', 'academic_head', 'counselor'] },
  { id: 'payments', label: 'Payments', icon: 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z', roles: ['super_admin', 'academic_head', 'finance'] },
  { id: 'checkout', label: 'Batch Checkout', icon: 'M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z', roles: ['counselor', 'finance'] },
  { id: 'subcenters', label: 'Sub-Centers', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4', roles: ['super_admin'] },
  { id: 'users', label: 'System Users', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z', roles: ['super_admin'] },
  { id: 'tickets', label: 'Support Tickets', icon: 'M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z', roles: ['super_admin', 'academic_head', 'counselor', 'finance'] },
  { id: 'lead-monitor', label: 'Lead Monitor', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', roles: ['super_admin', 'academic_head'] },
  { id: 'notification-logs', label: 'Notification Logs', icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z', roles: ['super_admin', 'academic_head', 'finance'] },
];

export function Sidebar({ profile, view, setView, onLogout, mobileMenuOpen, setMobileMenuOpen }: {
  profile: UserProfile;
  view: View;
  setView: (v: View) => void;
  onLogout: () => void;
  mobileMenuOpen?: boolean;
  setMobileMenuOpen?: (open: boolean) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);

  const roleLabel: Record<string, string> = {
    super_admin: 'Super Admin',
    academic_head: 'Academic Head',
    counselor: 'Counselor',
    finance: 'Finance Officer',
    subcenter: 'Sub-Center Admin',
  };
  const items = NAV_ITEMS.filter(i => i.roles.includes(profile.role));

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setMobileMenuOpen?.(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside 
        className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 md:relative md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        } ${collapsed ? 'w-16' : 'w-64'} bg-sidebar border-r border-sidebar-border flex flex-col h-full`}
      >
        <div className={`p-5 border-b border-sidebar-border flex items-center justify-between ${collapsed ? 'px-2' : ''}`}>
          {!collapsed && (
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-1.5 h-6 bg-primary rounded-sm" />
                <span className="text-sm font-bold tracking-tight">RIMIT</span>
              </div>
              <p className="text-[10px] text-muted-foreground truncate">B2B Aggregator</p>
            </div>
          )}
          <button 
            onClick={() => setCollapsed(!collapsed)} 
            className={`hidden md:block text-muted-foreground hover:text-foreground p-1 ${
              collapsed ? 'mx-auto' : ''
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <button onClick={() => setMobileMenuOpen?.(false)} className="md:hidden text-muted-foreground hover:text-foreground p-1">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto overflow-x-hidden">
          {items.map(item => (
            <button
              key={item.id}
              onClick={() => {
                setView(item.id);
                setMobileMenuOpen?.(false); // Auto close on mobile
              }}
              title={item.label}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition ${
                view === item.id
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent'
              } ${collapsed ? 'justify-center px-0' : ''}`}
            >
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
              </svg>
              {!collapsed && item.label}
            </button>
          ))}
        </nav>

      <div className={`p-3 border-t border-sidebar-border ${collapsed ? 'text-center' : ''}`}>
        {!collapsed ? (
          <div className="px-3 py-2 mb-2">
            <p className="text-sm font-medium text-foreground truncate">{profile.username}</p>
            <p className="text-xs text-muted-foreground">{roleLabel[profile.role]}</p>
            {profile.sub_center_code && (
              <p className="text-xs text-muted-foreground mt-0.5">{profile.sub_center_code}</p>
            )}
          </div>
        ) : (
          <div className="px-3 py-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto text-xs font-bold">
              {profile.username.charAt(0).toUpperCase()}
            </div>
          </div>
        )}
        <button
          onClick={() => {
            setView('change-password');
            setMobileMenuOpen?.(false);
          }}
          title="Change Password"
          className={`w-full text-left px-3 py-2 mb-1 rounded-md text-sm ${
            view === 'change-password'
              ? 'bg-sidebar-primary text-sidebar-primary-foreground'
              : 'text-muted-foreground hover:bg-sidebar-accent hover:text-foreground'
          } transition ${collapsed ? 'justify-center text-center' : ''}`}
        >
          {collapsed ? '🔑' : 'Change Password'}
        </button>
        <button
          onClick={onLogout}
          title="Sign Out"
          className={`w-full text-left px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-sidebar-accent hover:text-foreground transition ${collapsed ? 'justify-center text-center' : ''}`}
        >
          {collapsed ? '🚪' : 'Sign Out'}
        </button>
      </div>


    </aside>
    </>
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
export function PageHeader({ title, subtitle, action, breadcrumbs }: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  breadcrumbs?: { label: string; onClick?: () => void }[];
}) {
  return (
    <div className="flex items-start justify-between mb-6 pb-4 border-b border-border">
      <div>
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex text-xs text-muted-foreground mb-2 items-center space-x-2">
            {breadcrumbs.map((bc, idx) => (
              <div key={idx} className="flex items-center space-x-2">
                {idx > 0 && <span>/</span>}
                {bc.onClick ? (
                  <button onClick={bc.onClick} className="hover:text-foreground hover:underline transition">
                    {bc.label}
                  </button>
                ) : (
                  <span className="text-foreground font-medium">{bc.label}</span>
                )}
              </div>
            ))}
          </nav>
        )}
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
    <div className="space-y-4 py-6">
      <div className="flex gap-4">
        <Skeleton className="h-8 w-[250px]" />
        <Skeleton className="h-8 w-[250px]" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
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

// ──────────────── Confirm Dialog ────────────────
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  onConfirm,
  confirmText = "Continue",
  cancelText = "Cancel"
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  onConfirm: () => void;
  confirmText?: string;
  cancelText?: string;
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{cancelText}</AlertDialogCancel>
          <AlertDialogAction onClick={(e) => {
            e.preventDefault();
            onConfirm();
            onOpenChange(false);
          }}>{confirmText}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// Re-export types for convenience
export type { View, UserProfile, University, Course, Student, Enrollment, IntakeSession, SubCenter, PaymentLedger, RuleConfiguration, SystemUser, StudentDoc, StudentAcademicHistory, LeadIngestionLog, UniversityDoc };
