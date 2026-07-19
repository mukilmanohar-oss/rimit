'use client';

import { useEffect, useState } from 'react';
import { rules, type IntakeSession, type RuleConfiguration, type UserProfile } from '@/lib/api';
import { PageHeader, LoadingState, ErrorState, EmptyState, StatusBadge } from '../rimit-shell';
import { usePermissions } from '@/lib/permissions';

export function SessionsView({ profile }: { profile: UserProfile }) {
  const [sessions, setSessions] = useState<IntakeSession[]>([]);
  const [matrixRules, setMatrixRules] = useState<RuleConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
const [showRuleForm, setShowRuleForm] = useState(false);
  const [editingSession, setEditingSession] = useState<IntakeSession | null>(null);
  const [editingRule, setEditingRule] = useState<RuleConfiguration | null>(null);

  // Form state
  const [form, setForm] = useState({
    session_name: '',
    start_date: '',
    end_date: '',
    is_fresh_allowed: true,
  });
  const [submitting, setSubmitting] = useState(false);

  // Rule Form state
  const [ruleForm, setRuleForm] = useState({
    rule_name: '',
    description: '',
    conditions: '{\n  "action": "reject",\n  "reason": "Invalid"\n}',
    priority: 100,
  });
  const [submittingRule, setSubmittingRule] = useState(false);

  const { canCreate, canUpdate } = usePermissions(profile.role, 'intake_session');
  const { canRead: canReadRules } = usePermissions(profile.role, 'rules_config');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sessionsData, rulesData] = await Promise.all([
        rules.listIntakeSessions(),
        canReadRules ? rules.listRulesConfigurations() : { results: [] }
      ]);
      setSessions(sessionsData.results);
      if (canReadRules) setMatrixRules((rulesData as any).results || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        session_name: form.session_name,
        start_date: form.start_date,
        end_date: form.end_date || undefined,
        is_fresh_allowed: form.is_fresh_allowed,
      };
      if (editingSession) {
        await rules.updateIntakeSession(editingSession.id, payload);
      } else {
        await rules.createIntakeSession({ ...payload, is_active: true });
      }
      setForm({
        session_name: '',
        start_date: '',
        end_date: '',
        is_fresh_allowed: true,
      });
      setShowForm(false);
      setEditingSession(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${editingSession ? 'update' : 'create'} session`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSession = (s: IntakeSession) => {
    setEditingSession(s);
    setForm({
      session_name: s.session_name,
      start_date: s.start_date,
      end_date: s.end_date || '',
      is_fresh_allowed: s.is_fresh_allowed,
    });
    setShowForm(true);
  };

  const handleToggleActive = async (s: IntakeSession) => {
    try {
      await rules.updateIntakeSession(s.id, { is_active: !s.is_active });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle status');
    }
  };

  const handleToggleFresh = async (s: IntakeSession) => {
    try {
      await rules.updateIntakeSession(s.id, { is_fresh_allowed: !s.is_fresh_allowed });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle fresh candidate allowance');
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingRule(true);
    setError(null);
    try {
      let parsedConditions = {};
      try {
        parsedConditions = JSON.parse(ruleForm.conditions);
      } catch {
        throw new Error('Conditions must be valid JSON');
      }
      const payload = {
        rule_name: ruleForm.rule_name,
        description: ruleForm.description,
        conditions: parsedConditions,
        priority: ruleForm.priority,
      };
      
      if (editingRule) {
        await rules.updateRule(editingRule.id, payload);
      } else {
        await rules.createRule({ ...payload, is_active: true });
      }
      setRuleForm({ rule_name: '', description: '', conditions: '{\n  "action": "reject",\n  "reason": "Invalid"\n}', priority: 100 });
      setShowRuleForm(false);
      setEditingRule(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${editingRule ? 'update' : 'create'} rule`);
    } finally {
      setSubmittingRule(false);
    }
  };

  const handleEditRule = (r: RuleConfiguration) => {
    setEditingRule(r);
    setRuleForm({
      rule_name: r.rule_name,
      description: r.description || '',
      conditions: JSON.stringify(r.conditions, null, 2),
      priority: r.priority,
    });
    setShowRuleForm(true);
  };

  const handleToggleRule = async (r: RuleConfiguration) => {
    try {
      await rules.updateRule(r.id, { is_active: !r.is_active });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle rule');
    }
  };

  const handleDeleteRule = async (id: string) => {
    if (!confirm('Delete this rule?')) return;
    try {
      await rules.deleteRule(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete rule');
    }
  };

  if (loading) return <LoadingState />;
  if (error && !showForm) return <ErrorState message={error} />;

  if (showForm) {
    return (
      <div>
        <button onClick={() => { setShowForm(false); setEditingSession(null); }} className="text-sm text-primary mb-4 hover:underline">
          ← Back to sessions
        </button>
        <PageHeader title={editingSession ? "Edit Intake Session" : "Create Intake Session"} subtitle="Define new student intake window" />

        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleCreate} className="bg-card border border-border rounded-lg p-6 space-y-4 max-w-md">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Session Name *</label>
            <input
              type="text"
              value={form.session_name}
              onChange={e => setForm(prev => ({ ...prev, session_name: e.target.value }))}
              required
              placeholder="E.g., October 2026"
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Start Date *</label>
            <input
              type="date"
              value={form.start_date}
              onChange={e => setForm(prev => ({ ...prev, start_date: e.target.value }))}
              required
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">End Date</label>
            <input
              type="date"
              value={form.end_date}
              onChange={e => setForm(prev => ({ ...prev, end_date: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
            />
          </div>
          <div className="flex items-center gap-2 py-2">
            <input
              type="checkbox"
              id="is_fresh_allowed"
              checked={form.is_fresh_allowed}
              onChange={e => setForm(prev => ({ ...prev, is_fresh_allowed: e.target.checked }))}
              className="rounded border-input text-primary focus:ring-ring"
            />
            <label htmlFor="is_fresh_allowed" className="text-sm font-medium text-foreground">
              Allow Fresh Candidates
            </label>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="bg-primary text-primary-foreground rounded-md px-6 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? 'Saving...' : editingSession ? 'Update Session' : 'Create Session'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="border border-border rounded-md px-6 py-2 text-sm font-medium hover:bg-muted"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    );
  }

  if (showRuleForm) {
    return (
      <div>
        <button onClick={() => { setShowRuleForm(false); setEditingRule(null); }} className="text-sm text-primary mb-4 hover:underline">
          ← Back to sessions
        </button>
        <PageHeader title="Create Session Matrix Rule" subtitle="Define complex rules for enrollment validation" />

        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 text-sm text-destructive mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleCreateRule} className="bg-card border border-border rounded-lg p-6 space-y-4 max-w-xl">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Rule Name *</label>
            <input
              type="text"
              value={ruleForm.rule_name}
              onChange={e => setRuleForm(prev => ({ ...prev, rule_name: e.target.value }))}
              required
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              placeholder="e.g. block_fresh_july"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Description</label>
            <input
              type="text"
              value={ruleForm.description}
              onChange={e => setRuleForm(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Priority (Lower = Higher Priority)</label>
              <input
                type="number"
                value={ruleForm.priority}
                onChange={e => setRuleForm(prev => ({ ...prev, priority: parseInt(e.target.value) || 100 }))}
                className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Conditions (JSONB) *</label>
            <textarea
              required
              rows={8}
              value={ruleForm.conditions}
              onChange={e => setRuleForm(prev => ({ ...prev, conditions: e.target.value }))}
              className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm font-mono"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={submittingRule}
              className="bg-primary text-primary-foreground rounded-md px-6 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {submittingRule ? 'Saving...' : editingRule ? 'Update Rule' : 'Create Rule'}
            </button>
            <button
              type="button"
              onClick={() => setShowRuleForm(false)}
              className="border border-border rounded-md px-6 py-2 text-sm font-medium hover:bg-muted"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Intake Sessions"
        subtitle="Enrollment windows with Session Enforcement Matrix"
        action={
          canCreate && (
            <button
              onClick={() => setShowForm(true)}
              className="bg-primary text-primary-foreground rounded-md px-4 py-2 text-sm font-medium hover:bg-primary/90"
            >
              + Create Session
            </button>
          )
        }
      />

      {/* Session Enforcement Matrix Rules */}
      {canReadRules && (
        <div className="mb-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">Session Enforcement Matrix</h2>
            <button
              onClick={() => setShowRuleForm(true)}
              className="text-xs bg-muted hover:bg-muted/80 text-foreground px-3 py-1.5 rounded-md font-medium border"
            >
              + Add Rule
            </button>
          </div>

          {matrixRules.length === 0 ? (
             <div className="bg-amber-50 border border-amber-200 rounded-md p-4 text-sm text-amber-800">
               No active rules configured.
             </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {matrixRules.map(rule => (
                <div key={rule.id} className="bg-card border border-border rounded-lg p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-foreground text-sm">{rule.rule_name}</h3>
                        <span className="text-[10px] bg-muted px-1.5 rounded text-muted-foreground border">P{rule.priority}</span>
                      </div>
                      <StatusBadge status={rule.is_active ? 'active' : 'suspended'} />
                    </div>
                    {rule.description && <p className="text-xs text-muted-foreground mb-3">{rule.description}</p>}
                    <pre className="bg-muted/50 p-2 rounded text-[10px] text-muted-foreground overflow-auto max-h-32 border">
                      {JSON.stringify(rule.conditions, null, 2)}
                    </pre>
                  </div>
                  <div className="mt-4 flex gap-3">
                    <button onClick={() => handleToggleRule(rule)} className="text-[11px] text-primary hover:underline font-semibold">
                      {rule.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button onClick={() => handleDeleteRule(rule.id)} className="text-[11px] text-destructive hover:underline font-semibold">
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground">Active Intake Sessions</h2>
      </div>

      {sessions.length === 0 ? <EmptyState message="No intake sessions configured" /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sessions.map(s => (
            <div key={s.id} className="bg-card border border-border rounded-lg p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-foreground">{s.session_name}</h3>
                  <StatusBadge status={s.is_active ? 'active' : 'suspended'} />
                </div>
                <dl className="space-y-2 text-sm">
                  <div>
                    <dt className="text-xs text-muted-foreground">Start date</dt>
                    <dd className="font-medium text-foreground">{new Date(s.start_date).toLocaleDateString('en-IN')}</dd>
                  </div>
                  {s.end_date && (
                    <div>
                      <dt className="text-xs text-muted-foreground">End date</dt>
                      <dd className="font-medium text-foreground">{new Date(s.end_date).toLocaleDateString('en-IN')}</dd>
                    </div>
                  )}
                  <div>
                    <dt className="text-xs text-muted-foreground">Fresh candidates</dt>
                    <dd>
                      {s.is_fresh_allowed ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-emerald-50 text-emerald-700 border-emerald-200">
                          Allowed
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border bg-amber-50 text-amber-700 border-amber-200">
                          Blocked
                        </span>
                      )}
                    </dd>
                  </div>
                </dl>
              </div>

              {canUpdate && (
                <div className="mt-4 pt-3 border-t border-border flex gap-3">
                  <button
                    onClick={() => handleEditSession(s)}
                    className="text-xs text-primary hover:underline font-semibold"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleToggleActive(s)}
                    className="text-xs text-primary hover:underline font-semibold"
                  >
                    {s.is_active ? 'Suspend' : 'Activate'}
                  </button>
                  <button
                    onClick={() => handleToggleFresh(s)}
                    className="text-xs text-primary hover:underline font-semibold"
                  >
                    {s.is_fresh_allowed ? 'Block Fresh' : 'Allow Fresh'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
