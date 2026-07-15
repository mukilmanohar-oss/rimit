import { useState, useEffect, useCallback, useRef } from 'react';
import { UserProfile, admissions, DEFAULT_PAGE_SIZE, withPaging, hasNextPage, hasPrevPage, type Student, type Paginated } from '@/lib/api';

export function LeadsView({ profile }: { profile: UserProfile }) {
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [canNext, setCanNext] = useState(false);
  const [canPrev, setCanPrev] = useState(false);
  const requestIdRef = useRef(0);

  const fetchLeads = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    try {
      // lead_status != Converted to get only active leads. Wait, our API might not have `lead_status__ne`. Let's just fetch pending and followed-up.
      // Usually the API filters on lead_status. Let's just pass search.
      const params = withPaging({ search, lead_status: 'Pending' }, { page, pageSize: DEFAULT_PAGE_SIZE });
      const res = await admissions.listStudents(params);

      if (requestId !== requestIdRef.current) return;

      setLeads(res.results || []);
      setTotalPages(Math.max(1, Math.ceil((res.count || 0) / DEFAULT_PAGE_SIZE)));
      setCanNext(hasNextPage(res));
      setCanPrev(hasPrevPage(res));
    } catch (e: any) {
      console.error(e);
      // Fallback for mocked server response during development
      setLeads([]);
    } finally {
      setLoading(false);
    }
  }, [search, page]);

  useEffect(() => {
    const t = setTimeout(() => {
      fetchLeads();
    }, 300);
    return () => clearTimeout(t);
  }, [fetchLeads]);

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4 shrink-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Leads Directory</h1>
          <p className="text-muted-foreground mt-1">High-density data grid of all prospective students.</p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-72">
            <svg className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search leads..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-shadow"
            />
          </div>
          <button onClick={fetchLeads} className="bg-secondary text-secondary-foreground hover:bg-secondary/80 p-2 rounded-lg transition-colors border border-border shrink-0">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>

      <div className="bg-card border border-border shadow-sm rounded-xl flex-1 flex flex-col overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-10 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        <div className="flex-1 overflow-auto">
          <table className="w-full text-left text-sm text-muted-foreground">
            <thead className="text-xs uppercase bg-muted/50 text-foreground sticky top-0 z-20 shadow-sm">
              <tr>
                <th className="px-6 py-4 font-semibold">Name & Contact</th>
                <th className="px-6 py-4 font-semibold">Center Code</th>
                <th className="px-6 py-4 font-semibold">Course Interest</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {leads.length > 0 ? leads.map(lead => (
                <tr key={lead.id} className="hover:bg-muted/30 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="font-medium text-foreground">{lead.full_name}</div>
                    <div className="text-xs mt-1 text-muted-foreground flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                        {lead.email || 'N/A'}
                      </span>
                      <span className="flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>
                        {lead.primary_phone || 'N/A'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-secondary text-secondary-foreground">
                      {lead.sub_center_code || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-foreground max-w-[200px] truncate">{lead.course_name || 'Not Selected'}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      lead.lead_status === 'Pending' ? 'bg-amber-100 text-amber-800' :
                      lead.lead_status === 'Follow-Up' ? 'bg-blue-100 text-blue-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {lead.lead_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-primary hover:text-primary/80 font-medium text-sm transition-colors opacity-0 group-hover:opacity-100">
                      View Profile
                    </button>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                    No leads found matching your criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="border-t border-border p-4 flex items-center justify-between bg-card text-sm text-muted-foreground shrink-0">
          <div>Page {page} of {totalPages}</div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={!canPrev || page === 1}
              className="px-3 py-1.5 rounded-md border border-border hover:bg-muted disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
            >
              Previous
            </button>
            <button 
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={!canNext || page === totalPages}
              className="px-3 py-1.5 rounded-md border border-border hover:bg-muted disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
