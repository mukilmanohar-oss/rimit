'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { auth, type UserProfile } from '@/lib/api';
import { toast } from 'sonner';

interface LoginModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onLogin: (profile: UserProfile) => void;
}

export function LoginModal({ isOpen, onOpenChange, onLogin }: LoginModalProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    try {
      const res = await auth.login(email, password);
      localStorage.setItem('rimit_token', res.token);
      const profile = await auth.profile();
      toast.success('Successfully logged in.');
      onOpenChange(false);
      onLogin(profile);
    } catch (err: any) {
      toast.error(err.message || 'Invalid credentials');
    } finally {
      setLoginLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md p-0 overflow-hidden bg-white border-gray-100">
        <DialogHeader className="bg-bosse-light px-8 py-6 border-b border-gray-100 text-center flex flex-col items-center">
          <div className="inline-flex w-12 h-12 rounded-full bg-bosse-blue items-center justify-center text-white font-bold text-xl mb-3 shadow-inner">
            <i className="fa-solid fa-user-lock"></i>
          </div>
          <DialogTitle className="text-2xl font-bold text-gray-900">Partner Login</DialogTitle>
          <DialogDescription className="sr-only">Login to the partner portal.</DialogDescription>
        </DialogHeader>
        <div className="px-8 py-8">
          <form onSubmit={handleLogin}>
            <div className="mb-5">
              <label className="block text-sm font-medium text-gray-700 mb-1">Centre Code / Email</label>
              <input 
                type="text" 
                required 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bosse-blue focus:border-bosse-blue bg-gray-50 focus:bg-white transition-colors" 
                placeholder="e.g. BSS-2026-X" 
              />
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input 
                type="password" 
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bosse-blue focus:border-bosse-blue bg-gray-50 focus:bg-white transition-colors" 
                placeholder="••••••••" 
              />
            </div>
            <button disabled={loginLoading} type="submit" className="w-full py-3 px-4 rounded-lg shadow-sm font-bold text-white bg-bosse-blue hover:bg-blue-900 transition-colors flex items-center justify-center gap-2">
              {loginLoading ? <><i className="fa-solid fa-spinner fa-spin"></i> Authenticating...</> : 'Sign In'}
            </button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
