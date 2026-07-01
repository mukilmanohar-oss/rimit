"""
Custom permission classes implementing the RFP's 4-role RBAC:
  - super_admin (MD): complete control, bypass RLS
  - academic_head: read-only across all tenants
  - counselor: write to own tenant only
  - finance: read/write financial models, own tenant only
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


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
            return 'super_admin'
    return None


class IsSuperAdmin(BasePermission):
    """Only Super Admin (MD) role."""
    def has_permission(self, request, view):
        return _user_role(request) == 'super_admin'


class IsSuperAdminOrReadOnly(BasePermission):
    """
    Super Admin can write; all authenticated tenant members can read.

    Used for University/Course/Fee models — these are reference data
    that every role needs to read (counselors need to pick courses for
    enrollments, finance needs to see fee structures).
    """
    def has_permission(self, request, view):
        role = _user_role(request)
        if role == 'super_admin':
            return True
        if request.method in SAFE_METHODS:
            return role in ('academic_head', 'counselor', 'finance')
        return False


class IsTenantMember(BasePermission):
    """
    Any authenticated user with a sub_center assignment.
    TenantManager handles scoping — this just checks authentication + role.
    """
    def has_permission(self, request, view):
        role = _user_role(request)
        return role in ('super_admin', 'academic_head', 'counselor', 'finance')


class IsCounselorOrAbove(BasePermission):
    """Counselor, Academic Head, or Super Admin."""
    def has_permission(self, request, view):
        role = _user_role(request)
        return role in ('super_admin', 'academic_head', 'counselor')


class IsFinanceOrAbove(BasePermission):
    """Finance, Academic Head, or Super Admin."""
    def has_permission(self, request, view):
        role = _user_role(request)
        return role in ('super_admin', 'academic_head', 'finance')
