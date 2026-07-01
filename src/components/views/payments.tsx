'use client';

import { useEffect, useState } from 'react';
import { finance, type PaymentLedger, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';

export function PaymentsView({ profile }: { profile: UserProfile }) {
  const [payments, setPayments] = useState<PaymentLedger[]>([]);
  const [summary, setSummary] = useState<{ total_collected: string; total_pending: string; captured_count: number; pending_count: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      const [data, sum] = await Promise.all([
        finance.listPayments(params),
        finance.summary().catch(() => null),
      ]);
      setPayments(data.results);
      setSummary(sum);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <PageHeader title="Payments" subtitle="Financial ledger and collection summary" />

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-card border border-border rounded-lg p-4 border-l-4 border-l-emerald-500">
            <p className="text-xs text-muted-foreground uppercase">Collected</p>
            <p className="text-xl font-bold text-emerald-600 mt-1">₹{parseFloat(summary.total_collected || '0').toLocaleString('en-IN')}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4 border-l-4 border-l-amber-500">
            <p className="text-xs text-muted-foreground uppercase">Pending</p>
            <p className="text-xl font-bold text-amber-600 mt-1">₹{parseFloat(summary.total_pending || '0').toLocaleString('en-IN')}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-muted-foreground uppercase">Captured</p>
            <p className="text-xl font-bold text-foreground mt-1">{summary.captured_count}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-muted-foreground uppercase">Pending count</p>
            <p className="text-xl font-bold text-foreground mt-1">{summary.pending_count}</p>
          </div>
        </div>
      )}

      <div className="flex gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 rounded-md border border-input bg-background text-sm"
        >
          <option value="">All statuses</option>
          <option value="captured">Captured</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
          <option value="refunded">Refunded</option>
        </select>
        <button
          onClick={load}
          className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          Apply
        </button>
      </div>

      {payments.length === 0 ? <EmptyState message="No payment records" /> : (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/30 border-b border-border">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Transaction Ref</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Student</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Course</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Sub-center</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">Amount</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {payments.map(p => (
                <tr key={p.id} className="hover:bg-muted/20">
                  <td className="px-4 py-3 font-mono text-xs text-foreground">{p.transaction_ref}</td>
                  <td className="px-4 py-3 font-medium text-foreground">{p.student_name || '—'}</td>
                  <td className="px-4 py-3 text-muted-foreground">{p.course_name || '—'}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs bg-muted px-2 py-0.5 rounded">{p.sub_center_code || '—'}</span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-foreground">₹{parseFloat(p.amount_paid).toLocaleString('en-IN')}</td>
                  <td className="px-4 py-3"><StatusBadge status={p.status} /></td>
                  <td className="px-4 py-3 text-muted-foreground">{new Date(p.created_at).toLocaleDateString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
