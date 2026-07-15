'use client';

import { useEffect, useState } from 'react';
import { partners, admissions, DEFAULT_PAGE_SIZE, withPaging, hasNextPage, hasPrevPage, type SystemUser, type SubCenter, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState } from '../rimit-shell';
import { usePermissions } from '@/lib/permissions';

export function UsersView({ profile }: { profile: UserProfile }) {
  const [users, setUsers] = useState<SystemUser[]>([]);
  const [subCenters, setSubCenters] = useState<SubCenter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<SystemUser | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [canNext, setCanNext] = useState(false);
  const [canPrev, setCanPrev] = useState(false);

  // Form state
  const [form, setForm] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    role: 'counselor',
    sub_center: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const { canCreate, canUpdate, canDelete } = usePermissions(profile.role, 'system_user');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [uData, scData] = await Promise.all([
        partners.listUsers(withPaging(undefined, { page, pageSize: DEFAULT_PAGE_SIZE })),
        partners.listSubCenters({ page_size: '200' }),
      ]);
      setUsers(uData.results);
      setTotalCount(uData.count || 0);
      setCanNext(hasNextPage(uData));
      setCanPrev(hasPrevPage(uData));
      setSubCenters(scData.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page]); // eslint-disable-line

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        username: form.username,
        email: form.email,
        phone: form.phone,
        role: form.role,
      };
      if (form.password) {
        payload.password = form.password;
      }
      if (form.sub_center) {
        payload.sub_center = form.sub_center;
      } else {
        payload.sub_center = null;
      }
      
      // We use 'admissions' here because of a known botch in api.ts
      if (editingUser) {
        await admissions.updateSystemUser(editingUser.id, payload);
      } else {
        await admissions.createSystemUser(payload);
      }
      
      setForm({
        username: '',
        password: '',
        email: '',
        phone: '',
        role: 'counselor',
        sub_center: '',
      });
      setShowForm(false);
      setEditingUser(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${editingUser ? 'update' : 'create'} user`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (u: SystemUser) => {
    setEditingUser(u);
    setForm({
      username: u.username || '',
      password: '', // Don't populate password
      email: u.email,
      phone: u.phone || '',
      role: u.role,
      sub_center: u.sub_center || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this system user?')) return;
    try {
      await partners.deleteUser(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    }
  };

  const roleLabel: Record<string, string> = {
    super_admin: 'Super Admin',
    academic_head: 'Academic Head',
    counselor: 'Counselor',
    finance: 'Finance Officer',
    subcenter: 'Sub-Center Admin',
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
        <div className="bg-card w-full max-w-md rounded-xl shadow-lg border border-border overflow-hidden">
          <div className="px-6 py-4 border-b border-border flex justify-between items-center">
            <h3 className="font-semibold text-lg">{editingUser ? 'Edit User' : 'Create New User'}</h3>
            <button onClick={() => { setShowForm(false); setEditingUser(null); }} className="text-muted-foreground hover:text-foreground">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>
          
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive m-6 mb-0">
              {error}
            </div>
          )}

          <form onSubmit={handleCreate} className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Username *</label>
              <input
                type="text"
                value={form.username}
                onChange={e => setForm(prev => ({ ...prev, username: e.target.value }))}
                required
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Password {editingUser ? '' : '*'}</label>
              <input
                type="password"
                value={form.password}
                onChange={e => setForm(prev => ({ ...prev, password: e.target.value }))}
                required={!editingUser}
                placeholder={editingUser ? 'Leave blank to keep unchanged' : ''}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Email *</label>
              <input
                type="email"
                value={form.email}
                onChange={e => setForm(prev => ({ ...prev, email: e.target.value }))}
                required
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Phone</label>
              <input
                type="text"
                value={form.phone}
                onChange={e => setForm(prev => ({ ...prev, phone: e.target.value }))}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Role *</label>
              <select
                value={form.role}
                onChange={e => setForm(prev => ({ ...prev, role: e.target.value }))}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              >
                <option value="super_admin">Super Admin</option>
                <option value="academic_head">Academic Head</option>
                <option value="counselor">Counselor</option>
                <option value="finance">Finance Officer</option>
                <option value="subcenter">Sub-Center Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Sub-Center Linkage</label>
              <select
                value={form.sub_center}
                onChange={e => setForm(prev => ({ ...prev, sub_center: e.target.value }))}
                disabled={form.role === 'super_admin'}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm disabled:opacity-50"
              >
                <option value="">No sub-center (HQ / Global)</option>
                {subCenters.map(sc => (
                  <option key={sc.id} value={sc.id}>{sc.name} ({sc.center_code})</option>
                ))}
              </select>
            </div>
            <div className="pt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => { setShowForm(false); setEditingUser(null); }}
                className="px-4 py-2 text-sm font-medium rounded-md hover:bg-muted text-foreground"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !form.username || !form.email}
                className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {submitting ? 'Saving...' : editingUser ? 'Update User' : 'Create User'}
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
        title="System Users"
        subtitle="Manage user accounts and role permissions"
        action={canCreate && (
          <button
            onClick={() => {
              setEditingUser(null);
              setForm({ username: '', email: '', first_name: '', last_name: '', role: 'counselor', sub_center: '', password: '', phone: '' });
              setShowForm(true);
            }}
            className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md text-sm font-medium transition-colors"
          >
            + Create User
          </button>
        )}
      />

      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> :
        users.length === 0 ? <EmptyState message="No users found" /> : (
          <div className="space-y-3">
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
<table className="w-full text-sm">
                <thead className="bg-muted/30 border-b border-border">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Username</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Email</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Phone</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Role</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Sub-center</th>
                    <th className="text-right px-4 py-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {users.map(u => (
                    <tr key={u.id} className="hover:bg-muted/20">
                      <td className="px-4 py-3 font-bold text-foreground">{u.username || '—'}</td>
                      <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                      <td className="px-4 py-3 text-muted-foreground">{u.phone || '—'}</td>
                      <td className="px-4 py-3 text-foreground font-semibold">
                        {roleLabel[u.role] || u.role}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs bg-muted px-2 py-0.5 rounded">{u.sub_center_code || 'Global / HQ'}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {canUpdate && <button onClick={() => handleEdit(u)} className="text-primary text-sm hover:underline mr-4">Edit</button>}
                        {canDelete && profile.user_id !== Number(u.id) && (
                          <button
                            onClick={() => handleDelete(u.id)}
                            className="text-xs text-destructive hover:underline font-semibold"
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
</div>
            </div>

            <div className="flex items-center justify-between py-2">
              <span className="text-xs text-muted-foreground">
                Page {page} of {Math.max(1, Math.ceil(totalCount / DEFAULT_PAGE_SIZE))} (Total {totalCount} records)
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={!canPrev || page === 1}
                  className="px-3 py-1 text-xs border border-border rounded hover:bg-muted disabled:opacity-50 font-medium"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={!canNext}
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
