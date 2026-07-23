'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import { auth, type UserProfile } from '@/lib/api';
import { PageHeader } from '../rimit-shell';

export function ChangePasswordView({ profile }: { profile: UserProfile }) {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changing, setChanging] = useState(false);
  const [passError, setPassError] = useState<string | null>(null);
  const [passSuccess, setPassSuccess] = useState<string | null>(null);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPassError(null);
    setPassSuccess(null);
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    setChanging(true);
    try {
      await auth.changePassword(oldPassword, newPassword);
      toast.success('Password changed successfully');
      setPassSuccess('Password changed successfully');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to change password';
      toast.error(errMsg);
      setPassError(errMsg);
    } finally {
      setChanging(false);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-6">
      <PageHeader
        title="Change Password"
        subtitle="Update your account credentials"
      />

      <div className="bg-card border border-border rounded-lg shadow-sm p-6 space-y-4">
        {passError && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive text-xs p-2.5 rounded">
            {passError}
          </div>
        )}
        {passSuccess && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs p-2.5 rounded">
            {passSuccess}
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Current Password</label>
            <input
              type="password"
              value={oldPassword}
              onChange={e => setOldPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="flex gap-2 pt-2 justify-end">
            <button
              type="submit"
              disabled={changing}
              className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition"
            >
              {changing ? 'Updating...' : 'Update Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
