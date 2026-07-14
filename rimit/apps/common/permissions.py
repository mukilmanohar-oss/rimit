"""
Custom permission classes implementing the RFP's 4-role RBAC.

All permissions are now defined in apps.common.rbac (single source of truth).
This module re-exports them for backward compatibility.
"""
from apps.common.rbac import (
    _user_role,
    has_permission,
    SA, AH, C, F,
    ALL_ROLES, PRIVILEGED_ROLES,
    PERMISSION_MATRIX,
    ResourcePermission,
    IsSuperAdmin,
    IsSuperAdminOrReadOnly,
    IsTenantMember,
    IsCounselorOrAbove,
    IsFinanceOrAbove,
)

__all__ = [
    '_user_role',
    'has_permission',
    'SA', 'AH', 'C', 'F',
    'ALL_ROLES', 'PRIVILEGED_ROLES',
    'PERMISSION_MATRIX',
    'ResourcePermission',
    'IsSuperAdmin',
    'IsSuperAdminOrReadOnly',
    'IsTenantMember',
    'IsCounselorOrAbove',
    'IsFinanceOrAbove',
]
