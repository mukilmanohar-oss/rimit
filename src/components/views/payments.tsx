'use client';

import { useEffect, useState } from 'react';
import { finance, type PaymentLedger, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';
import { can } from '@/lib/permissions';
import { exportToCSV } from '@/lib/utils';

export function PaymentsView({ profile }: { profile: UserProfile }) {
  const [payments, setPayments] = useState<PaymentLedger[]>([]);
  const [summary, setSummary] = useState<{ total_collected: string; total_pending: string; captured_count: number; pending_count: number } | null>(null);
  const [breakdown, setBreakdown] = useState<Array<{ sub_center__center_code: string; sub_center__name: string; total: string; count: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedPayment, setSelectedPayment] = useState<PaymentLedger | null>(null);

  const canSeeBreakdown = can(profile.role, 'payment', 'breakdown');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = { page: String(page) };
      if (statusFilter) params.status = statusFilter;
      const [data, sum, bkdn] = await Promise.all([
        finance.listPayments(params),
        finance.summary().catch(() => null),
        canSeeBreakdown ? finance.bySubCenter().catch(() => []) : Promise.resolve([])
      ]);
      setPayments(data.results);
      setTotalCount(data.count);
      setSummary(sum);
      if (canSeeBreakdown) setBreakdown(bkdn);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page]); // eslint-disable-line

  const handleExportCSV = () => {
    const headers = ['Transaction Ref', 'Student Name', 'Course Name', 'Sub-center Code', 'Amount Paid', 'Status', 'Created At'];
    const rows = payments.map(p => [
      p.transaction_ref,
      p.student_name || '',
      p.course_name || '',
      p.sub_center_code || '',
      p.amount_paid,
      p.status,
      new Date(p.created_at).toLocaleDateString('en-IN')
    ]);
    exportToCSV('payments_export.csv', headers, rows);
  };

  if (loading) return <LoadingState />;
  if (error && !selectedPayment) return <ErrorState message={error} />;

  if (selectedPayment) {
    return (
      <div>
        <button onClick={() => setSelectedPayment(null)} className="text-sm text-primary mb-4 hover:underline">
          ← Back to payments
        </button>
        <PageHeader title="Payment Receipt" subtitle={selectedPayment.transaction_ref} />
        <div className="bg-card border border-border rounded-lg p-6 max-w-2xl mx-auto shadow-sm">
          <div className="flex justify-between items-start mb-6 border-b border-border pb-6">
            <div>
              <h2 className="text-xl font-bold text-foreground">RIMIT Institute</h2>
              <p className="text-xs text-muted-foreground mt-1">Official Fee Receipt</p>
            </div>
            <div className="text-right">
              <StatusBadge status={selectedPayment.status} />
              <p className="text-xs text-muted-foreground mt-2">Date: {new Date(selectedPayment.created_at).toLocaleString('en-IN')}</p>
            </div>
          </div>
          
          <dl className="grid grid-cols-2 gap-y-4 gap-x-6 text-sm mb-6">
            <div>
              <dt className="text-xs text-muted-foreground">Transaction Reference</dt>
              <dd className="font-mono font-medium text-foreground">{selectedPayment.transaction_ref}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Gateway / Method</dt>
              <dd className="font-medium text-foreground uppercase">{selectedPayment.gateway}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Student Name</dt>
              <dd className="font-medium text-foreground">{selectedPayment.student_name}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Course</dt>
              <dd className="font-medium text-foreground">{selectedPayment.course_name}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Sub-center</dt>
              <dd className="font-medium text-foreground">{selectedPayment.sub_center_code}</dd>
            </div>
          </dl>
          
          <div className="bg-muted/30 border border-border rounded-lg p-4 flex justify-between items-center mb-6">
            <span className="font-semibold text-foreground">Amount Paid</span>
            <span className="text-2xl font-bold text-foreground">₹{parseFloat(selectedPayment.amount_paid).toLocaleString('en-IN')}</span>
          </div>

          <div className="text-center text-xs text-muted-foreground">
            <p>This is a computer generated receipt and does not require a physical signature.</p>
          </div>
          
          <div className="mt-6 flex justify-end">
            <button className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90">
              Download PDF
            </button>
          </div>
        </div>
      </div>
    );
  }

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

      {canSeeBreakdown && breakdown.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold mb-3 text-foreground">Sub-Center Collections Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {breakdown.map(b => (
              <div key={b.sub_center__center_code} className="bg-card border border-border rounded-lg p-4 flex justify-between items-center">
                <div>
                  <p className="font-semibold text-foreground">{b.sub_center__name}</p>
                  <p className="text-xs text-muted-foreground mt-1">Code: {b.sub_center__center_code}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-emerald-600">₹{parseFloat(b.total).toLocaleString('en-IN')}</p>
                  <p className="text-xs text-muted-foreground mt-1">{b.count} txns</p>
                </div>
              </div>
            ))}
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
          onClick={() => { setPage(1); load(); }}
          className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
        >
          Apply
        </button>
        <button
          onClick={handleExportCSV}
          className="border border-border text-muted-foreground hover:text-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Export CSV
        </button>
      </div>

          <div className="space-y-4">
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
                    <tr 
                      key={p.id} 
                      className="hover:bg-muted/20 cursor-pointer"
                      onClick={() => setSelectedPayment(p)}
                    >
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

            <div className="flex items-center justify-between py-2">
              <span className="text-xs text-muted-foreground">
                Page {page} of {Math.max(1, Math.ceil(totalCount / 25))} (Total {totalCount} records)
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
                  disabled={page * 25 >= totalCount}
                  className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
    </div>
  );
}
