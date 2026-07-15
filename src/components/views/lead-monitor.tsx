'use client';

import { useEffect, useState } from 'react';
import { leads, admissions, type LeadIngestionLog, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState } from '../rimit-shell';
import { toast } from 'sonner';

export function LeadMonitorView({ profile }: { profile: UserProfile }) {
  const [logs, setLogs] = useState<LeadIngestionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [search, setSearch] = useState('');

  // Stats
  const [stats, setStats] = useState({
    total: 0,
    ingested: 0,
    fetchFailed: 0,
    deadLetter: 0,
    converted: 0,
  });

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (sourceFilter) params.source = sourceFilter;
      if (search) params.search = search;

      const data = await leads.list({ ...params, page_size: '200' });
      setLogs(data.results);

      // Compute statistics based on unfiltered list or fetch separately.
      // Since it's paginated, we'll fetch all leads for stats computation (or simulate stats from results in dev)
      const results: LeadIngestionLog[] = [];
      // Fetch multiple pages for accurate stats, bounded for safety.
      let nextPage = 1;
      for (let i = 0; i < 5; i++) {
        const pageData = await leads.list({ page: String(nextPage), page_size: '200' }).catch(() => ({ results: [] } as any));
        if (!pageData?.results?.length) break;
        results.push(...pageData.results);
        if (!pageData.next) break;
        nextPage += 1;
      }
      const computed = results.reduce(
        (acc, curr) => {
          acc.total += 1;
          if (curr.status === 'ingested') acc.ingested += 1;
          else if (curr.status === 'fetch_failed') acc.fetchFailed += 1;
          else if (curr.status === 'dead_letter') acc.deadLetter += 1;
          else if (curr.status === 'converted') acc.converted += 1;
          return acc;
        },
        { total: 0, ingested: 0, fetchFailed: 0, deadLetter: 0, converted: 0 }
      );
      setStats(computed);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load lead logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [statusFilter, sourceFilter, search]);

  const handleConvert = async (leadId: string) => {
    try {
      await admissions.convertLead(leadId);
      toast.success('Lead successfully converted to Student Profile');
      load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Conversion failed');
    }
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      ingested: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800/30',
      fetch_failed: 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800/30',
      dead_letter: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800/30',
      converted: 'bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800/30',
    };
    const labels: Record<string, string> = {
      ingested: 'Ingested',
      fetch_failed: 'Fetch Failed',
      dead_letter: 'Dead Letter',
      converted: 'Converted',
    };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badges[status] || 'bg-gray-100 text-gray-800'}`}>
        {labels[status] || status}
      </span>
    );
  };

  if (loading && logs.length === 0) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lead Ingestion Log Monitor"
        subtitle="Monitor the health of inbound Meta Lead Ads and campaigns webhook integrations"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-card border border-border p-4 rounded-xl shadow-sm space-y-1">
          <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Total leads</p>
          <p className="text-2xl font-extrabold text-foreground">{stats.total}</p>
        </div>
        <div className="bg-card border border-border p-4 rounded-xl shadow-sm space-y-1">
          <p className="text-[10px] uppercase font-bold text-blue-500 tracking-wider">Ingested</p>
          <p className="text-2xl font-extrabold text-blue-600 dark:text-blue-400">{stats.ingested}</p>
        </div>
        <div className="bg-card border border-border p-4 rounded-xl shadow-sm space-y-1">
          <p className="text-[10px] uppercase font-bold text-amber-500 tracking-wider">Fetch Failed</p>
          <p className="text-2xl font-extrabold text-amber-600 dark:text-amber-400">{stats.fetchFailed}</p>
        </div>
        <div className="bg-card border border-border p-4 rounded-xl shadow-sm space-y-1">
          <p className="text-[10px] uppercase font-bold text-red-500 tracking-wider">Dead Letter</p>
          <p className="text-2xl font-extrabold text-red-600 dark:text-red-400">{stats.deadLetter}</p>
        </div>
        <div className="bg-card border border-border p-4 rounded-xl shadow-sm space-y-1">
          <p className="text-[10px] uppercase font-bold text-emerald-500 tracking-wider">Converted</p>
          <p className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">{stats.converted}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-card border border-border rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-sm">
        <div className="flex flex-wrap gap-3 w-full md:w-auto">
          <input
            type="text"
            placeholder="Search by Lead ID or campaign..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="px-3 py-2 rounded-md border border-input bg-background text-sm min-w-[200px]"
          />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-md border border-input bg-background text-sm"
          >
            <option value="">All Statuses</option>
            <option value="ingested">Ingested</option>
            <option value="fetch_failed">Fetch Failed</option>
            <option value="dead_letter">Dead Letter</option>
            <option value="converted">Converted</option>
          </select>
          <select
            value={sourceFilter}
            onChange={e => setSourceFilter(e.target.value)}
            className="px-3 py-2 rounded-md border border-input bg-background text-sm"
          >
            <option value="">All Sources</option>
            <option value="meta">Meta Ads</option>
            <option value="google">Google Ads</option>
            <option value="referral">Referral</option>
          </select>
        </div>
      </div>

      {error && <ErrorState message={error} />}

      {logs.length === 0 ? (
        <EmptyState message="No lead ingestion logs found" />
      ) : (
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 border-b border-border">
                <tr className="text-left font-medium text-muted-foreground">
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Leadgen ID</th>
                  <th className="px-4 py-3">Details (Name/Phone/Email)</th>
                  <th className="px-4 py-3">Campaign</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Ingested At</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {logs.map(log => {
                  const details = (log.normalized_data || {}) as any;
                  return (
                    <tr key={log.id} className="hover:bg-muted/15 transition">
                      <td className="px-4 py-3 capitalize font-semibold text-foreground">{log.source}</td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{log.leadgen_id.slice(0, 16)}...</td>
                      <td className="px-4 py-3 space-y-0.5 text-xs text-muted-foreground">
                        <div className="font-bold text-foreground">{details.name || details.full_name || 'No Name'}</div>
                        <div>{details.phone || details.phone_number || '—'}</div>
                        <div>{details.email || '—'}</div>
                      </td>
                      <td className="px-4 py-3 font-medium text-foreground text-xs">{log.campaign_id || '—'}</td>
                      <td className="px-4 py-3">{getStatusBadge(log.status)}</td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">{new Date(log.created_at).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right">
                        {log.status === 'ingested' && (
                          <button
                            onClick={() => handleConvert(log.id)}
                            className="bg-primary text-primary-foreground px-3 py-1.5 rounded-md text-xs font-semibold hover:bg-primary/90 transition"
                          >
                            Convert to Student
                          </button>
                        )}
                        {log.status === 'fetch_failed' && (
                          <span className="text-xs text-destructive italic font-medium" title={log.error_msg}>
                            Error: {log.error_msg ? `${log.error_msg.slice(0, 20)}...` : 'Failed'}
                          </span>
                        )}
                        {log.status === 'converted' && (
                          <span className="text-xs text-emerald-600 font-semibold">
                            Converted
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
