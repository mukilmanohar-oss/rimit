'use client';

import { useEffect, useState } from 'react';
import { partners, type SubCenter, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';
import { usePermissions } from '@/lib/permissions';

export function SubCentersView({ profile }: { profile: UserProfile }) {
  const [subCenters, setSubCenters] = useState<SubCenter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingCenter, setEditingCenter] = useState<SubCenter | null>(null);

  // Form state
  const [form, setForm] = useState({
    center_code: '',
    name: '',
    location: '',
    state: '',
    contact_phone: '',
    contact_email: '',
    commission_percent: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const { canCreate, canUpdate } = usePermissions(profile.role, 'sub_center');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      const data = await partners.listSubCenters(params);
      setSubCenters(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sub-centers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [statusFilter]); // eslint-disable-line

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (editingCenter) {
        await partners.updateSubCenter(editingCenter.id, form);
      } else {
        await partners.createSubCenter(form);
      }
      setForm({
        center_code: '',
        name: '',
        location: '',
        state: '',
        contact_phone: '',
        contact_email: '',
        commission_percent: '',
      });
      setShowForm(false);
      setEditingCenter(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${editingCenter ? 'update' : 'create'} sub-center`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (sc: SubCenter) => {
    setEditingCenter(sc);
    setForm({
      center_code: sc.center_code,
      name: sc.name,
      location: sc.location,
      state: sc.state || '',
      contact_phone: sc.contact_phone || '',
      contact_email: sc.contact_email || '',
      commission_percent: (sc.commission_percent ?? '').toString(),
    });
    setShowForm(true);
  };

  const handleStatusChange = async (id: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'active' ? 'suspended' : 'active';
    if (!confirm(`Are you sure you want to change the status to ${nextStatus}?`)) return;
    try {
      await partners.updateSubCenter(id, { status: nextStatus });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    }
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div className="bg-card w-full max-w-lg rounded-xl shadow-lg border border-border overflow-hidden">
          <div className="px-6 py-4 border-b border-border flex justify-between items-center">
            <h3 className="font-semibold text-lg">{editingCenter ? 'Edit Sub-Center' : 'Onboard New Sub-Center'}</h3>
            <button onClick={() => { setShowForm(false); setEditingCenter(null); }} className="text-muted-foreground hover:text-foreground">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>

          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive m-6 mb-0">
              {error}
            </div>
          )}

          <form onSubmit={handleCreate} className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Center Code *</label>
              <input
                type="text"
                value={form.center_code}
                onChange={e => setForm(prev => ({ ...prev, center_code: e.target.value }))}
                required
                placeholder="E.g., KL-KOC-001"
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={e => setForm(prev => ({ ...prev, name: e.target.value }))}
                required
                placeholder="E.g., Kochi Center"
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Location *</label>
              <input
                type="text"
                value={form.location}
                onChange={e => setForm(prev => ({ ...prev, location: e.target.value }))}
                required
                placeholder="E.g., Edapally, Kochi"
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">State *</label>
              <input
                type="text"
                value={form.state}
                onChange={e => setForm(prev => ({ ...prev, state: e.target.value }))}
                placeholder="E.g., Kerala"
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Contact Phone</label>
              <input
                type="text"
                value={form.contact_phone}
                onChange={e => setForm(prev => ({ ...prev, contact_phone: e.target.value }))}
                placeholder="E.g., +919876543210"
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Contact Email</label>
              <input
                type="email"
                value={form.contact_email}
                onChange={e => setForm(prev => ({ ...prev, contact_email: e.target.value }))}
                placeholder="E.g., kochi@rimit.com"
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Commission % (Gross Pool)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={form.commission_percent}
                onChange={e => setForm(prev => ({ ...prev, commission_percent: e.target.value }))}
                placeholder="E.g., 75.00"
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
              <p className="text-[11px] text-muted-foreground mt-1">Sub-center share of Gross Commission Pool (0–100%).</p>
            </div>
          </div>

            <div className="pt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => { setShowForm(false); setEditingCenter(null); }}
                className="px-4 py-2 text-sm font-medium rounded-md hover:bg-muted text-foreground"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !form.center_code || !form.name || !form.location}
                className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {submitting ? 'Saving...' : editingCenter ? 'Update Center' : 'Create Center'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Sub-Centers"
        subtitle="Manage B2B sub-center locations"
        action={canCreate && (
          <button
            onClick={() => {
              setEditingCenter(null);
              setForm({ center_code: '', name: '', location: '', state: '', contact_phone: '', contact_email: '', commission_percent: '' });
              setShowForm(true);
            }}
            className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
          >
            + Onboard Sub-Center
          </button>
        )}
      />

      <div className="flex gap-3 mb-4 max-w-xs">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="terminated">Terminated</option>
        </select>
      </div>

      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> :
        subCenters.length === 0 ? <EmptyState message="No sub-centers found" /> : (
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/30 border-b border-border">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Code</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Location</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Contact</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Commission %</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {subCenters.map(sc => (
                  <tr key={sc.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3 font-bold text-foreground">{sc.center_code}</td>
                    <td className="px-4 py-3 text-foreground font-medium">{sc.name}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {sc.location}{sc.state ? `, ${sc.state}` : ''}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground space-y-0.5">
                      <div>{sc.contact_phone || '—'}</div>
                      <div>{sc.contact_email || '—'}</div>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {sc.commission_percent !== undefined && sc.commission_percent !== null ? (
                        <span className="font-semibold text-foreground">{Number(sc.commission_percent).toFixed(2)}%</span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={sc.status} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      {canUpdate && (
                        <>
                          <button onClick={() => handleEdit(sc)} className="text-primary text-sm hover:underline mr-4">Edit</button>
                          {sc.status !== 'terminated' && (
                            <button
                              onClick={() => handleStatusChange(sc.id, sc.status)}
                              className="text-xs text-primary hover:underline font-semibold"
                            >
                              {sc.status === 'active' ? 'Suspend' : 'Activate'}
                            </button>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    </div>
  );
}
