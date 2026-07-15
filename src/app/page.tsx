'use client';

import { useState, useEffect } from 'react';
import { auth, type UserProfile } from '@/lib/api';
import {
  Sidebar, type View,
} from '@/components/rimit-shell';
import { LandingPage } from '@/components/views/landing-page';
import { DashboardView } from '@/components/views/dashboard';
import { UniversitiesView } from '@/components/views/universities';
import { StudentsView } from '@/components/views/students';
import { EnrollmentsView } from '@/components/views/enrollments';
import { SessionsView } from '@/components/views/sessions';
import { PaymentsView } from '@/components/views/payments';
import { SubCentersView } from '@/components/views/sub-centers';
import { UsersView } from '@/components/views/users';
import { TicketsView } from '@/components/views/tickets';
import { NotificationLogsView } from '@/components/views/notification-logs';
import { ProspectusView } from '@/components/views/prospectus';
import { CourseSearchView } from '@/components/views/course-search';
import { LeadMonitorView } from '@/components/views/lead-monitor';
import { CheckoutView } from '@/components/views/checkout';
import { LeadsCreateView } from '@/components/views/leads-create';
import { LeadsView } from '@/components/views/leads';

export default function Home() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [bootstrapping, setBootstrapping] = useState(true);
  const [view, setView] = useState<View>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Bootstrap: check for existing token
  useEffect(() => {
    (async () => {
      const token = typeof window !== 'undefined' ? localStorage.getItem('rimit_token') : null;
      if (token) {
        try {
          const p = await auth.profile();
          setProfile(p);
        } catch {
          localStorage.removeItem('rimit_token');
        }
      }
      setBootstrapping(false);
    })();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('rimit_token');
    setProfile(null);
    setView('dashboard');
  };

  if (bootstrapping) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!profile) {
    return <LandingPage onLogin={setProfile} />;
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      {/* Mobile Top Navigation */}
      <div className="md:hidden flex items-center justify-between p-4 border-b border-border bg-sidebar sticky top-0 z-30">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-5 bg-primary rounded-sm" />
          <span className="text-sm font-bold tracking-tight">RIMIT</span>
        </div>
        <button 
          onClick={() => setMobileMenuOpen(true)}
          className="text-muted-foreground hover:text-foreground"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      <Sidebar 
        profile={profile} 
        view={view} 
        setView={setView} 
        onLogout={handleLogout} 
        mobileMenuOpen={mobileMenuOpen}
        setMobileMenuOpen={setMobileMenuOpen}
      />
      
      <main className="flex-1 p-4 md:p-8 overflow-x-hidden min-w-0">
        {view === 'dashboard' && <DashboardView profile={profile} />}
        {view === 'universities' && <UniversitiesView profile={profile} />}
        {view === 'students' && <StudentsView profile={profile} />}
        {view === 'enrollments' && <EnrollmentsView profile={profile} />}
        {view === 'sessions' && <SessionsView profile={profile} />}
        {view === 'payments' && <PaymentsView profile={profile} />}
        {view === 'subcenters' && <SubCentersView profile={profile} />}
        {view === 'users' && <UsersView profile={profile} />}
        {view === 'tickets' && <TicketsView profile={profile} />}
        {view === 'prospectus' && <ProspectusView profile={profile} />}
        {view === 'course-search' && <CourseSearchView profile={profile} />}
        {view === 'lead-monitor' && <LeadMonitorView profile={profile} />}
        {view === 'notification-logs' && <NotificationLogsView profile={profile} />}
        {view === 'checkout' && <CheckoutView profile={profile} />}
        {view === 'leads-create' && <LeadsCreateView profile={profile} />}
        {view === 'leads' && <LeadsView profile={profile} />}
      </main>
    </div>
  );
}
