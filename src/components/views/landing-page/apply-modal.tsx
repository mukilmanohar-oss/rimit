'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { toast } from 'sonner';

interface ApplyModalProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  initialStep?: number;
}

export function ApplyModal({ isOpen, onOpenChange, initialStep = 1 }: ApplyModalProps) {
  const [applyStep, setApplyStep] = useState(initialStep);
  const [applyLoading, setApplyLoading] = useState(false);
  
  const [appName, setAppName] = useState('');
  const [appPhone, setAppPhone] = useState('');
  const [appEmail, setAppEmail] = useState('');
  const [appCompany, setAppCompany] = useState('');
  const [appCity, setAppCity] = useState('');
  const [appStudentBase, setAppStudentBase] = useState('New Setup (0 students)');

  // Reset state when opened
  if (isOpen && applyStep !== initialStep && !appName && !appPhone) {
      setApplyStep(initialStep);
  }

  const handleApplyNext = () => {
    if (!appName || !appPhone || !appEmail) {
      toast.error('Please fill name, phone, and email.');
      return;
    }
    setApplyStep(2);
  };

  const submitApplication = (e: React.FormEvent) => {
    e.preventDefault();
    setApplyLoading(true);
    setTimeout(() => {
      setApplyLoading(false);
      onOpenChange(false);
      toast.success('Application Received. Our team will contact you within 24 hours.');
      setApplyStep(1);
      setAppName('');
      setAppPhone('');
      setAppEmail('');
      setAppCompany('');
      setAppCity('');
      setAppStudentBase('New Setup (0 students)');
    }, 1500);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg p-0 overflow-hidden bg-white border-gray-100">
        <DialogHeader className="bg-gray-50 px-8 py-6 border-b border-gray-100 text-left">
          <DialogTitle className="text-xl font-bold text-gray-900 mb-4">Partnership Application</DialogTitle>
          <DialogDescription className="sr-only">Apply to become a partner.</DialogDescription>
          <div className="flex items-center justify-between relative">
            <div className="absolute left-0 top-1/2 w-full h-1 bg-gray-200 -z-10 -translate-y-1/2"></div>
            <div className="absolute left-0 top-1/2 h-1 bg-bosse-green -z-10 -translate-y-1/2 transition-all duration-300" style={{ width: applyStep === 1 ? '50%' : '100%' }}></div>
            
            <div className="w-8 h-8 rounded-full bg-bosse-green text-white flex items-center justify-center text-sm font-bold shadow-md">1</div>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors duration-300 ${applyStep === 2 ? 'bg-bosse-green text-white shadow-md' : 'bg-gray-200 text-gray-500 border border-gray-300'}`}>2</div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-2 font-medium w-full">
            <span>Basic Details</span>
            <span>Institution Info</span>
          </div>
        </DialogHeader>

        <div className="px-8 py-6">
          <form onSubmit={applyStep === 1 ? (e) => { e.preventDefault(); handleApplyNext(); } : submitApplication}>
            
            {applyStep === 1 && (
              <div className="space-y-4 animate-fade-in">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                  <input type="text" required value={appName} onChange={(e) => setAppName(e.target.value)} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bosse-green outline-none bg-gray-50 focus:bg-white" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
                    <input type="tel" required value={appPhone} onChange={(e) => setAppPhone(e.target.value)} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bosse-green outline-none bg-gray-50 focus:bg-white" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                    <input type="email" required value={appEmail} onChange={(e) => setAppEmail(e.target.value)} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bosse-green outline-none bg-gray-50 focus:bg-white" />
                  </div>
                </div>
                <button type="submit" className="w-full mt-4 py-3 bg-bosse-blue text-white rounded-lg font-bold hover:bg-blue-900 transition-colors">
                  Next Step <i className="fa-solid fa-arrow-right ml-1"></i>
                </button>
              </div>
            )}

            {applyStep === 2 && (
              <div className="space-y-4 animate-fade-in">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Institution/Company Name</label>
                  <input type="text" value={appCompany} onChange={(e) => setAppCompany(e.target.value)} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bosse-green outline-none bg-gray-50 focus:bg-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">City/District *</label>
                  <input type="text" required value={appCity} onChange={(e) => setAppCity(e.target.value)} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bosse-green outline-none bg-gray-50 focus:bg-white" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Current Student Base (Approx)</label>
                  <select value={appStudentBase} onChange={(e) => setAppStudentBase(e.target.value)} className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-bosse-green outline-none bg-gray-50 focus:bg-white">
                    <option>New Setup (0 students)</option>
                    <option>1 - 50 students</option>
                    <option>51 - 200 students</option>
                    <option>200+ students</option>
                  </select>
                </div>
                <div className="flex gap-3 mt-4">
                  <button type="button" onClick={() => setApplyStep(1)} className="w-1/3 py-3 bg-gray-100 text-gray-700 rounded-lg font-bold hover:bg-gray-200 transition-colors">
                    Back
                  </button>
                  <button disabled={applyLoading} type="submit" className="w-2/3 py-3 bg-bosse-green text-white rounded-lg font-bold hover:bg-green-700 transition-colors shadow-md flex justify-center items-center gap-2">
                    {applyLoading ? <><i className="fa-solid fa-spinner fa-spin"></i> Processing...</> : 'Submit Application'}
                  </button>
                </div>
              </div>
            )}
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
