'use client';

import { useEffect, useState } from 'react';
import { support, DEFAULT_PAGE_SIZE, withPaging, hasNextPage, hasPrevPage, type Ticket, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';
import { can } from '@/lib/permissions';
import { toast } from 'sonner';

function Field({ label, value, onChange, required = false, type = 'text', as = 'input' }: any) {
  return (
    <div>
      <label className="block text-xs font-medium text-muted-foreground mb-1">{label}</label>
      {as === 'textarea' ? (
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          required={required}
          rows={4}
          className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={e => onChange(e.target.value)}
          required={required}
          className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      )}
    </div>
  );
}

function TicketDetail({ ticket, profile, onBack }: { ticket: Ticket; profile: UserProfile; onBack: () => void }) {
  const [message, setMessage] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [messages, setMessages] = useState(ticket.replies || []);

  const handlePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setSubmitting(true);
    try {
      const msg = await support.addReply(ticket.id, message, isInternal);
      setMessages([...messages, msg]);
      setMessage('');
      toast.success('Reply posted');
    } catch (err: any) {
      toast.error(err.message || 'Failed to post reply');
    } finally {
      setSubmitting(false);
    }
  };

  const isAdmin = can(profile.role, 'student_doc', 'verify');

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <div className="flex items-center justify-between mb-4 shrink-0">
        <button onClick={onBack} className="text-sm text-primary hover:underline flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Back to tickets
        </button>
        <div className="flex gap-2">
          <StatusBadge status={ticket.status} />
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            ticket.escalation_level === 'L3' ? 'bg-red-100 text-red-700' :
            ticket.escalation_level === 'L2' ? 'bg-amber-100 text-amber-700' :
            'bg-green-100 text-green-700'
          }`}>
            {ticket.escalation_level} Priority
          </span>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-6">
        {/* Left Column: Ticket Details & Timeline */}
        <div className="w-full lg:w-1/3 flex flex-col gap-4 overflow-y-auto pr-2">
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
            <h2 className="text-xl font-bold text-foreground mb-2">{ticket.subject}</h2>
            <div className="flex flex-col gap-1 text-sm text-muted-foreground mb-4 border-b border-border pb-4">
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" /></svg>
                ID: {ticket.id.slice(0, 8)}
              </span>
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                Raised by: {ticket.created_by_name}
              </span>
              {ticket.category && (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                  Category: {ticket.category}
                </span>
              )}
            </div>
            
            <h3 className="text-sm font-semibold mb-2">Description</h3>
            <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">{ticket.description}</p>
          </div>
          
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm flex-1">
            <h3 className="text-sm font-semibold mb-4">Status Timeline</h3>
            <div className="relative border-l border-border ml-2 pl-4 space-y-6 pb-2">
              <div className="relative">
                <div className="absolute w-2 h-2 bg-primary rounded-full -left-[21px] top-1.5 ring-4 ring-background"></div>
                <p className="text-sm font-medium">Ticket Created</p>
                <p className="text-xs text-muted-foreground">{new Date(ticket.created_at).toLocaleString()}</p>
              </div>
              <div className="relative">
                <div className={`absolute w-2 h-2 rounded-full -left-[21px] top-1.5 ring-4 ring-background ${ticket.status !== 'Open' ? 'bg-primary' : 'bg-muted-foreground'}`}></div>
                <p className="text-sm font-medium">In Progress</p>
                <p className="text-xs text-muted-foreground">{ticket.status !== 'Open' ? 'Assigned and being reviewed' : 'Pending assignment'}</p>
              </div>
              <div className="relative">
                <div className={`absolute w-2 h-2 rounded-full -left-[21px] top-1.5 ring-4 ring-background ${ticket.status === 'Resolved' || ticket.status === 'Closed' ? 'bg-primary' : 'bg-muted-foreground'}`}></div>
                <p className="text-sm font-medium">Resolved</p>
                <p className="text-xs text-muted-foreground">{ticket.status === 'Resolved' || ticket.status === 'Closed' ? 'Issue marked as resolved' : 'Waiting for resolution'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Chat Interface */}
        <div className="w-full lg:w-2/3 flex flex-col bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b border-border bg-muted/20 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            </div>
            <div>
              <h3 className="font-semibold text-sm">Conversation Thread</h3>
              <p className="text-xs text-muted-foreground">Internal messages and support replies</p>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-muted/5">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                <svg className="w-12 h-12 mb-2 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                <p className="text-sm">No replies yet. Start the conversation below.</p>
              </div>
            )}
            {messages.map((m: any) => {
              const isMe = m.sender === profile.id || m.sender_name === profile.first_name + ' ' + profile.last_name;
              return (
                <div key={m.id} className={`flex flex-col max-w-[80%] ${isMe ? 'ml-auto' : 'mr-auto'}`}>
                  <div className={`flex items-baseline gap-2 mb-1 ${isMe ? 'justify-end' : 'justify-start'}`}>
                    <span className="text-xs font-medium text-foreground">{m.sender_name}</span>
                    <span className="text-[10px] text-muted-foreground">{new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    {m.is_admin_reply && (
                      <span className="text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                        Admin Note
                      </span>
                    )}
                  </div>
                  <div className={`p-3 rounded-2xl text-sm whitespace-pre-wrap ${
                    m.is_admin_reply 
                      ? 'bg-amber-50 text-amber-900 border border-amber-200 rounded-tl-sm' 
                      : isMe 
                        ? 'bg-primary text-primary-foreground rounded-tr-sm' 
                        : 'bg-muted text-foreground border border-border rounded-tl-sm'
                  }`}>
                    {m.message}
                  </div>
                </div>
              );
            })}
          </div>

          <form onSubmit={handlePost} className="p-4 border-t border-border bg-background">
            <div className="relative rounded-xl border border-input focus-within:ring-2 focus-within:ring-primary focus-within:border-primary overflow-hidden shadow-sm transition-shadow bg-background flex flex-col">
              <textarea 
                value={message} 
                onChange={e => setMessage(e.target.value)} 
                required 
                placeholder="Type your reply here..."
                className="w-full px-4 py-3 bg-transparent text-sm focus:outline-none resize-none min-h-[80px]"
              />
              <div className="flex justify-between items-center px-4 py-2 border-t border-border/50 bg-muted/10">
                <div>
                  {isAdmin && (
                    <label className="flex items-center gap-2 text-xs font-medium text-muted-foreground cursor-pointer group">
                      <input type="checkbox" checked={isInternal} onChange={e => setIsInternal(e.target.checked)} className="rounded border-input text-amber-600 focus:ring-amber-600" />
                      <span className="group-hover:text-foreground transition-colors">Internal note</span>
                    </label>
                  )}
                </div>
                <button 
                  type="submit" 
                  disabled={submitting || !message.trim()} 
                  className="bg-primary text-primary-foreground rounded-full p-2 hover:bg-primary/90 disabled:opacity-50 transition-colors shadow-sm flex items-center justify-center h-8 w-8 shrink-0"
                >
                  {submitting ? (
                    <div className="w-3 h-3 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <svg className="w-4 h-4 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function TicketCreateForm({ onBack, onCancel }: { onBack: () => void; onCancel: () => void }) {
  const [form, setForm] = useState({ subject: '', description: '', category: '', escalation_level: 'L1' });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await support.createTicket(form);
      toast.success('Ticket raised successfully');
      onBack();
    } catch (err: any) {
      toast.error(err.message || 'Failed to raise ticket');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <button onClick={onCancel} className="text-sm text-primary mb-4 hover:underline">
        ← Back to tickets
      </button>
      <PageHeader title="Raise New Ticket" subtitle="Submit an operational request or issue" />
      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-lg p-6 space-y-4">
        <Field label="Subject *" value={form.subject} onChange={(v: string) => setForm(f => ({ ...f, subject: v }))} required />
        <Field label="Category" value={form.category} onChange={(v: string) => setForm(f => ({ ...f, category: v }))} />
        <Field label="Description *" as="textarea" value={form.description} onChange={(v: string) => setForm(f => ({ ...f, description: v }))} required />
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Escalation Level</label>
          <select value={form.escalation_level} onChange={e => setForm(f => ({ ...f, escalation_level: e.target.value }))} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
            <option value="L1">L1</option>
            <option value="L2">L2</option>
            <option value="L3">L3</option>
          </select>
        </div>
        <div className="pt-2">
          <button type="submit" disabled={submitting} className="bg-primary text-primary-foreground rounded-md px-6 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50">
            {submitting ? 'Submitting...' : 'Submit Ticket'}
          </button>
        </div>
      </form>
    </div>
  );
}

export function TicketsView({ profile }: { profile: UserProfile }) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [canNext, setCanNext] = useState(false);
  const [canPrev, setCanPrev] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await support.listTickets(withPaging(undefined, { page, pageSize: DEFAULT_PAGE_SIZE }));
      setTickets(data.results);
      setTotalCount(data.count || 0);
      setCanNext(hasNextPage(data));
      setCanPrev(hasPrevPage(data));
    } catch (err: any) {
      setError(err.message || 'Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page]); // eslint-disable-line

  if (selected) {
    return <TicketDetail ticket={selected} profile={profile} onBack={() => { setSelected(null); load(); }} />;
  }

  if (showForm) {
    return <TicketCreateForm onBack={() => { setShowForm(false); load(); }} onCancel={() => setShowForm(false)} />;
  }

  return (
    <div>
      <PageHeader
        title="Helpdesk & Tickets"
        subtitle="Manage operational requests"
        action={
          <button onClick={() => setShowForm(true)} className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90">
            + Raise Ticket
          </button>
        }
      />

      {loading ? <LoadingState /> : error ? <ErrorState message={error} /> :
        tickets.length === 0 ? <EmptyState message="No tickets found" /> : (
          <div className="space-y-3">
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted/30 border-b border-border">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">ID</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Subject</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Level</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Category</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Created By</th>
                    <th className="text-right px-4 py-3 font-medium text-muted-foreground">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {tickets.map(t => (
                    <tr key={t.id} className="hover:bg-muted/20 cursor-pointer" onClick={() => setSelected(t)}>
                      <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{t.id.slice(0, 8)}</td>
                      <td className="px-4 py-3 font-medium text-foreground">{t.subject}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          t.escalation_level === 'L3' ? 'bg-red-100 text-red-700' :
                          t.escalation_level === 'L2' ? 'bg-amber-100 text-amber-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                          {t.escalation_level}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground text-xs">{t.category || '-'}</td>
                      <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                      <td className="px-4 py-3 text-muted-foreground">{t.created_by_name}</td>
                      <td className="px-4 py-3 text-right text-muted-foreground">{new Date(t.created_at).toLocaleDateString()}</td>
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
        )}
    </div>
  );
}
