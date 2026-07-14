/**
 * RIMIT RBAC — Centralized Permission Matrix (Frontend)
 *
 * Mirrors the backend PERMISSION_MATRIX in apps/common/rbac.py.
 * Any change here MUST be reflected in the backend and vice versa.
 */

// ─── Role Constants ─────────────────────────────────────────────
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ACADEMIC_HEAD: 'academic_head',
  COUNSELOR: 'counselor',
  FINANCE: 'finance',
  SUBCENTER: 'subcenter',
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];

const SA = ROLES.SUPER_ADMIN;
const AH = ROLES.ACADEMIC_HEAD;
const C  = ROLES.COUNSELOR;
const F  = ROLES.FINANCE;
const SC = ROLES.SUBCENTER;

const ALL: Role[] = [SA, AH, C, F, SC];

// ─── CRUD Actions ────────────────────────────────────────────────
export type CrudAction = 'create' | 'read' | 'update' | 'delete';
export type SpecialAction = 'verify' | 'reject' | 'transition' | 'export' | 'breakdown';

type Action = CrudAction | SpecialAction;

// ─── Permission Matrix ───────────────────────────────────────────
// Each resource maps to {action: allowedRoles[]}
const PERMISSION_MATRIX: Record<string, Partial<Record<Action, readonly Role[]>>> = {
  university:       { create: [SA],        read: ALL,        update: [SA],        delete: [SA] },
  course:           { create: [SA],        read: ALL,        update: [SA],        delete: [SA] },
  fee_structure:    { create: [SA],        read: [SA, AH, C, F], update: [SA],        delete: [SA] },
  university_doc:   { create: [SA],        read: ALL,        update: [SA],        delete: [SA] },
  sub_center:       { create: [SA],        read: [SA, AH, C, F], update: [SA],        delete: [SA] },
  system_user:      { create: [SA],        read: [SA],        update: [SA],        delete: [SA] },
  student:          { create: [SA, AH, C, SC], read: ALL,        update: [SA, AH, C, SC], delete: [SA, AH, C, SC] },
  student_doc:      { create: [SA, AH, C, SC], read: [SA, AH, C, SC], update: [SA, AH, C, SC], delete: [SA, AH, C, SC],
                      verify: [SA, AH, SC],    reject: [SA, AH, SC] },
  academic_history: { create: [SA, AH, C, SC], read: [SA, AH, C, SC], update: [SA, AH, C, SC], delete: [SA, AH, C, SC] },
  enrollment:       { create: [SA, AH, C, SC], read: [SA, AH, C, SC], update: [SA, AH, C, SC], delete: [SA, AH, C, SC],
                      transition: [SA, AH, C, SC] },
  intake_session:   { create: [SA],        read: ALL,        update: [SA],        delete: [SA] },
  rules_config:     { create: [SA],        read: [SA],        update: [SA],        delete: [SA] },
  payment:          { create: [],          read: [SA, AH, F], update: [],          delete: [],
                      breakdown: [SA, AH], export: [SA, AH, F] },
  checkout:         { create: ALL,         read: ALL,        update: [],          delete: [] },
  ticket:           { create: ALL,         read: ALL,        update: ALL,         delete: [] },
  notification:     { create: [SA],        read: [SA, AH, F], update: [],          delete: [] },
  lead_ingestion:   { create: [],          read: [SA, AH],    update: [],          delete: [] },
};

// ─── Permission Check Function ───────────────────────────────────
/**
 * Check if a role has permission for a specific action on a resource.
 *
 * @example
 *   can('super_admin', 'university', 'create') // true
 *   can('counselor', 'university', 'create')    // false
 *   can('finance', 'student', 'read')           // true
 *   can('finance', 'student', 'update')         // false
 */
export function can(role: string | undefined, resource: string, action: Action): boolean {
  if (!role) return false;
  const perms = PERMISSION_MATRIX[resource];
  if (!perms) return false;
  const allowed = perms[action];
  if (!allowed) return false;
  return (allowed as readonly string[]).includes(role);
}

// ─── usePermissions Hook ─────────────────────────────────────────
/**
 * Returns a permissions object for the given role and resource.
 *
 * @example
 *   const { canCreate, canUpdate, canDelete } = usePermissions(profile.role, 'university');
 *   {canCreate && <button>Add University</button>}
 */
export function usePermissions(role: string | undefined, resource: string) {
  return {
    canCreate: can(role, resource, 'create'),
    canRead:   can(role, resource, 'read'),
    canUpdate: can(role, resource, 'update'),
    canDelete: can(role, resource, 'delete'),
  };
}

/**
 * Extended permissions for resources with custom actions.
 */
export function useExtendedPermissions(role: string | undefined, resource: string) {
  return {
    ...usePermissions(role, resource),
    canVerify:     can(role, resource, 'verify'),
    canReject:     can(role, resource, 'reject'),
    canTransition: can(role, resource, 'transition'),
    canExport:     can(role, resource, 'export'),
    canBreakdown:  can(role, resource, 'breakdown'),
  };
}
