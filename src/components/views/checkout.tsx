'use client';

import { useEffect, useState } from 'react';
import { admissions, finance, type Student, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, StatusBadge } from '../rimit-shell';

export function CheckoutView({ profile }: { profile: UserProfile }) {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch only students in 'Pending Payment' state
      // (Using lead_status param as implemented in our backend search/filter)
      const data = await admissions.listStudents({ lead_status: 'Pending Payment', page_size: '200' });
      setStudents(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pending payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  const toggleSelection = (id: string) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedIds(newSet);
  };

  const selectAll = () => {
    if (selectedIds.size === students.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(students.map(s => s.id)));
    }
  };

  const handleCheckout = async () => {
    if (selectedIds.size === 0) return;
    setCheckoutLoading(true);
    try {
      const response = await finance.batchCheckout(Array.from(selectedIds));
      if (response.gateway_redirect_url) {
        window.location.href = response.gateway_redirect_url;
      } else {
        alert("Success: " + response.message);
        load();
        setSelectedIds(new Set());
      }
    } catch (err) {
      alert("Checkout failed: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setCheckoutLoading(false);
    }
  };

  const selectedStudents = students.filter(s => selectedIds.has(s.id));

  const n = (v: any) => {
    if (v === null || v === undefined) return 0;
    if (typeof v === 'number') return v;
    const parsed = parseFloat(String(v));
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const totals = selectedStudents.reduce(
    (acc, s) => {
      acc.totalFee += n(s.course_total_fee);
      acc.yourCommission += n(s.your_commission);
      acc.netPayable += n(s.net_payable);
      return acc;
    },
    { totalFee: 0, yourCommission: 0, netPayable: 0 }
  );

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <PageHeader 
        title="Batch Checkout" 
        subtitle="Review pending leads and pay upfront fees via escrow."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-card border border-border rounded-lg overflow-hidden shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 border-b border-border">
                <tr>
                  <th className="px-4 py-3 text-left w-12">
                    <input 
                      type="checkbox" 
                      checked={students.length > 0 && selectedIds.size === students.length}
                      onChange={selectAll}
                      className="rounded border-input text-primary focus:ring-primary"
                    />
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Student Name</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Course</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">Course Fee</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">Your Commission</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">Net Payable</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {students.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                      No leads pending payment.
                    </td>
                  </tr>
                )}
                {students.map(s => (
                  <tr key={s.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3">
                      <input 
                        type="checkbox"
                        checked={selectedIds.has(s.id)}
                        onChange={() => toggleSelection(s.id)}
                        className="rounded border-input text-primary focus:ring-primary"
                      />
                    </td>
                    <td className="px-4 py-3 font-medium text-foreground">{s.full_name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{s.course_name || '—'}</td>
                    <td className="px-4 py-3 text-right font-semibold text-foreground">₹{n(s.course_total_fee).toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-right font-bold text-emerald-700">₹{n(s.your_commission).toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-right font-bold text-primary">₹{n(s.net_payable).toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3"><StatusBadge status={s.lead_status || 'Unknown'} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <div className="bg-card border border-border rounded-lg shadow-sm p-6 sticky top-6">
            <h2 className="text-lg font-bold mb-4 text-foreground">Order Summary</h2>
            
            <div className="space-y-3 mb-6">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Selected Leads</span>
                <span className="font-medium text-foreground">{selectedIds.size}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Total Fee</span>
                <span className="font-medium text-foreground">₹{totals.totalFee.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Your Commission (Upfront)</span>
                <span className="font-bold text-emerald-700">-₹{totals.yourCommission.toLocaleString('en-IN')}</span>
              </div>
              <div className="border-t border-border pt-3 mt-3 flex justify-between">
                <span className="font-bold text-foreground">Total</span>
                <span className="text-xl font-bold text-primary">₹{totals.netPayable.toLocaleString('en-IN')}</span>
              </div>
            </div>

            <p className="text-xs text-muted-foreground mb-6">
              By proceeding, you agree to the escrow terms. Funds will be held securely until enrollment is verified.
            </p>

            <button
              onClick={handleCheckout}
              disabled={selectedIds.size === 0 || checkoutLoading}
              className="w-full bg-primary text-primary-foreground rounded-md py-3 text-sm font-bold hover:bg-primary/90 disabled:opacity-50 transition"
            >
              {checkoutLoading ? 'Processing...' : `Proceed to Pay ₹${totals.netPayable.toLocaleString('en-IN')}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
