"""
Centralized Role-Based Access Control (RBAC) registry.

Single source of truth for the 4-role CRUD permission matrix.
Consumed by:
  - ResourcePermission (DRF permission class) in backend views
  - /src/lib/permissions.ts (mirrored) in frontend

Roles:
  SA = super_admin     (MD — full control, bypass RLS)
  AH = academic_head   (cross-tenant read, limited write)
  C  = counselor       (own-tenant CRUD on admissions)
  F  = finance         (own-tenant read on financial models)
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS

# ─── Role Constants ───────────────────────────────────────────────
SA = 'super_admin'
AH = 'academic_head'
C  = 'counselor'
F  = 'finance'
SC = 'subcenter'

ALL_ROLES = [SA, AH, C, F, SC]
PRIVILEGED_ROLES = [SA, AH]

# ─── CRUD Permission Matrix ──────────────────────────────────────
# Each resource maps to {action: [allowed_roles]}
PERMISSION_MATRIX = {
    'university':       {'create': [SA],         'read': ALL_ROLES,       'update': [SA],         'delete': [SA]},
    'course':           {'create': [SA],         'read': ALL_ROLES,       'update': [SA],         'delete': [SA]},
    'fee_structure':    {'create': [SA],         'read': [SA, AH, C, F],  'update': [SA],         'delete': [SA]},
    'university_doc':   {'create': [SA],         'read': ALL_ROLES,       'update': [SA],         'delete': [SA]},
    'sub_center':       {'create': [SA],         'read': [SA, AH, C, F],  'update': [SA],         'delete': [SA]},
    'system_user':      {'create': [SA],         'read': [SA],            'update': [SA],         'delete': [SA]},
    'sc_uni_mapping':   {'create': [SA],         'read': [SA],            'update': [SA],         'delete': [SA]},
    'student':          {'create': [SA, AH, C, SC],  'read': ALL_ROLES,       'update': [SA, AH, C, SC],  'delete': [SA, AH, C, SC]},
    'student_doc':      {'create': [SA, AH, C, SC],  'read': [SA, AH, C, SC],     'update': [SA, AH, C, SC],  'delete': [SA, AH, C, SC],
                         'verify': [SA, AH, SC],     'reject': [SA, AH, SC]},
    'academic_history': {'create': [SA, AH, C, SC],  'read': [SA, AH, C, SC],     'update': [SA, AH, C, SC],  'delete': [SA, AH, C, SC]},
    'enrollment':       {'create': [SA, AH, C, SC],  'read': [SA, AH, C, SC],     'update': [SA, AH, C, SC],  'delete': [SA, AH, C, SC],
                         'transition': [SA, AH, C, SC]},
    'intake_session':   {'create': [SA],         'read': ALL_ROLES,       'update': [SA],         'delete': [SA]},
    'rules_config':     {'create': [SA],         'read': [SA],            'update': [SA],         'delete': [SA]},
    'payment':          {'create': [],           'read': [SA, AH, F],     'update': [],           'delete': [],
                         'breakdown': [SA, AH],  'export': [SA, AH, F]},
    'checkout':         {'create': ALL_ROLES,    'read': ALL_ROLES,       'update': [],           'delete': []},
    'ticket':           {'create': ALL_ROLES,    'read': ALL_ROLES,       'update': ALL_ROLES,    'delete': []},
    'notification':     {'create': [SA],         'read': [SA, AH, F],     'update': [],           'delete': []},
    'lead_ingestion':   {'create': [],           'read': [SA, AH],        'update': [],           'delete': []},
}

# ─── HTTP Method → Action Mapping ─────────────────────────────────
_METHOD_ACTION = {
    'GET':     'read',
    'HEAD':    'read',
    'OPTIONS': 'read',
    'POST':    'create',
    'PUT':     'update',
    'PATCH':   'update',
    'DELETE':  'delete',
}


def has_permission(role, resource, action):
    """Check if a role has permission for a specific action on a resource."""
    perms = PERMISSION_MATRIX.get(resource)
    if not perms:
        return False
    allowed = perms.get(action, [])
    return role in allowed


def _user_role(request):
    """Extract role from request user's SystemUser profile."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return None
    try:
        from apps.partners.models import SystemUser
        su = SystemUser.objects.get(user=request.user)
        return su.role
    except Exception:
        if request.user.is_superuser:
            return SA
    return None


class ResourcePermission(BasePermission):
    """
    Generic DRF permission class driven by PERMISSION_MATRIX.

    Usage on a ViewSet:
        class UniversityViewSet(viewsets.ModelViewSet):
            resource_name = 'university'
            permission_classes = [ResourcePermission]

    For custom actions (e.g., 'verify', 'reject'), set the action name
    in the PERMISSION_MATRIX and DRF's `view.action` will be used.
    """

    def has_permission(self, request, view):
        role = _user_role(request)
        if role is None:
            return False

        resource = getattr(view, 'resource_name', None)
        if resource is None:
            return False

        # For DRF viewset custom actions (e.g., @action(detail=True, ...))
        action = getattr(view, 'action', None)
        if action and action in PERMISSION_MATRIX.get(resource, {}):
            return has_permission(role, resource, action)

        # Standard HTTP method → CRUD action
        crud_action = _METHOD_ACTION.get(request.method, 'read')
        return has_permission(role, resource, crud_action)


# ─── Legacy Permission Classes (kept for backward compat) ────────
# These delegate to the matrix so there's one source of truth.

class IsSuperAdmin(BasePermission):
    """Only Super Admin (MD) role."""
    def has_permission(self, request, view):
        return _user_role(request) == SA


class IsSuperAdminOrReadOnly(BasePermission):
    """Super Admin can write; all authenticated roles can read."""
    def has_permission(self, request, view):
        role = _user_role(request)
        if role == SA:
            return True
        if request.method in SAFE_METHODS:
            return role in ALL_ROLES
        return False


class IsTenantMember(BasePermission):
    """Any of the 4 authenticated roles."""
    def has_permission(self, request, view):
        return _user_role(request) in ALL_ROLES


class IsCounselorOrAbove(BasePermission):
    """Counselor, Academic Head, or Super Admin."""
    def has_permission(self, request, view):
        return _user_role(request) in [SA, AH, C]


class IsFinanceOrAbove(BasePermission):
    """Finance, Academic Head, or Super Admin."""
    def has_permission(self, request, view):
        return _user_role(request) in [SA, AH, F]
