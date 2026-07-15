'use client';

import { useEffect, useState } from 'react';
import { notifications, DEFAULT_PAGE_SIZE, type NotificationLog, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';
import { exportToCSV } from '@/lib/utils';

export function NotificationLogsView({ profile }: { profile: UserProfile }) {
  const [logs, setLogs] = useState<NotificationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [channelFilter, setChannelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showBroadcast, setShowBroadcast] = useState(false);
  const isSuperAdmin = profile.role === 'super_admin';

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { page: String(page) };
      if (channelFilter) params.channel = channelFilter;
      if (statusFilter) params.delivery_status = statusFilter;
      const data = await notifications.listLogs(params);
      setLogs(data.results);
      setTotalCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notification logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [page, channelFilter, statusFilter]);

  const handleExportCSV = () => {
    const headers = ['Date', 'Recipient', 'Channel', 'Template ID', 'Status', 'Retries', 'Message / Error'];
    const rows = logs.map(log => [
      new Date(log.created_at).toLocaleString('en-IN'),
      log.recipient,
      log.channel,
      log.template_id,
      log.delivery_status,
      String(log.retry_count),
      log.delivery_status === 'failed' ? (log.error_msg || '') : (log.message_body || '')
    ]);
    exportToCSV('notification_logs_export.csv', headers, rows);
  };

  return (
    <div>
      <PageHeader
        title="Notification Logs"
        subtitle="WhatsApp, SMS, and Email system delivery logs"
      />

      <div className="flex gap-4 mb-6 items-end justify-between">
        <div className="flex gap-4">
          <div className="w-48">
            <label className="block text-xs font-medium text-muted-foreground mb-1">Filter Channel</label>
            <select
              value={channelFilter}
              onChange={(e) => { setChannelFilter(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
            >
              <option value="">All Channels</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="sms">SMS</option>
              <option value="email">Email</option>
            </select>
          </div>

          <div className="w-48">
            <label className="block text-xs font-medium text-muted-foreground mb-1">Filter Status</label>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
            >
              <option value="">All Statuses</option>
              <option value="queued">Queued</option>
              <option value="sent">Sent</option>
              <option value="failed">Failed</option>
              <option value="delivered">Delivered</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2">
          {isSuperAdmin && (
            <button
              onClick={() => setShowBroadcast(true)}
              className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-md px-4 py-2 text-sm font-medium"
            >
              + Broadcast Message
            </button>
          )}
          <button
            onClick={handleExportCSV}
            className="border border-border text-muted-foreground hover:text-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-muted"
          >
            Export CSV
          </button>
        </div>
      </div>

      {showBroadcast && (
        <BroadcastModal onClose={() => setShowBroadcast(false)} onSuccess={() => { setShowBroadcast(false); load(); }} />
      )}

      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> :
        logs.length === 0 ? <EmptyState message="No notification logs found" /> : (
          <div className="space-y-4">
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/30 border-b border-border">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Date</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Recipient</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Channel</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Template ID</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Retries</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Message / Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {logs.map(log => (
                    <tr key={log.id} className="hover:bg-muted/20">
                      <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                        {new Date(log.created_at).toLocaleString('en-IN')}
                      </td>
                      <td className="px-4 py-3 font-medium text-foreground">{log.recipient}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs bg-muted px-2 py-0.5 rounded font-mono uppercase">
                          {log.channel}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{log.template_id}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={log.delivery_status} />
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{log.retry_count}</td>
                      <td className="px-4 py-3">
                        {log.delivery_status === 'failed' && log.error_msg ? (
                          <span className="text-xs text-destructive font-medium bg-destructive/10 px-2 py-1 rounded block max-w-xs truncate">
                            {log.error_msg}
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground block max-w-xs truncate" title={log.message_body}>
                            {log.message_body || '—'}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

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
                  disabled={page * DEFAULT_PAGE_SIZE >= totalCount}
                  className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )
      }
    </div>
  );
}

function BroadcastModal({ onClose, onSuccess }: { onClose: () => void, onSuccess: () => void }) {
  const [form, setForm] = useState({ channel: 'whatsapp', template_id: '', recipients: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const recipientList = form.recipients.split('\n').map(s => s.trim()).filter(Boolean);
      if (recipientList.length === 0) throw new Error('Please enter at least one recipient');
      await notifications.broadcast({
        channel: form.channel,
        template_id: form.template_id,
        recipients: recipientList,
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Broadcast failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <div className="bg-card w-full max-w-lg rounded-xl shadow-lg border border-border overflow-hidden flex flex-col max-h-[90vh]">
        <div className="p-4 border-b border-border flex justify-between items-center">
          <h2 className="text-lg font-semibold text-foreground">New Broadcast Message</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground font-bold">✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-4 space-y-4 overflow-y-auto">
          {error && <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">{error}</div>}
          
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Channel</label>
            <select
              value={form.channel}
              onChange={e => setForm(f => ({ ...f, channel: e.target.value }))}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
            >
              <option value="whatsapp">WhatsApp</option>
              <option value="sms">SMS</option>
              <option value="email">Email</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Template ID *</label>
            <input
              type="text"
              required
              value={form.template_id}
              onChange={e => setForm(f => ({ ...f, template_id: e.target.value }))}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm"
              placeholder="e.g. promo_campaign_2026"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Recipients (One per line) *</label>
            <textarea
              required
              rows={6}
              value={form.recipients}
              onChange={e => setForm(f => ({ ...f, recipients: e.target.value }))}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm font-mono"
              placeholder="+919999999999\n+918888888888"
            />
            <p className="text-[10px] text-muted-foreground mt-1">
              Supports up to 10,000 numbers/emails. Processing happens asynchronously.
            </p>
          </div>

          <div className="pt-4 flex gap-2 justify-end">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm border rounded-md hover:bg-muted">Cancel</button>
            <button type="submit" disabled={submitting} className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50">
              {submitting ? 'Sending...' : 'Send Broadcast'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
