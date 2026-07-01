"""
TenantContextMiddleware — sets the thread-local tenant context
used by TenantManager.

DRF's TokenAuthentication runs at view dispatch (after middleware),
so the tenant resolution happens via DRF's `perform_authentication` hook
on the view (see TenantAwareViewMixin in views.py).

For session-based auth (Django admin), the middleware resolves immediately.
"""
import threading
from django.contrib.auth.models import AnonymousUser

_thread_locals = threading.local()


def _current_tenant_id():
    return getattr(_thread_locals, 'tenant_id', None)


def _current_user_role():
    return getattr(_thread_locals, 'user_role', None)


def _current_user_id():
    return getattr(_thread_locals, 'user_id', None)


def set_tenant_context(user):
    """
    Set the thread-local tenant context from a User instance.

    Called by:
      1. TenantContextMiddleware (for session-authenticated requests)
      2. TenantAwareViewMixin.perform_authentication (for DRF TokenAuth)
    """
    _thread_locals.tenant_id = None
    _thread_locals.user_role = None
    _thread_locals.user_id = None

    if user is None or not user.is_authenticated:
        return

    _thread_locals.user_id = user.id

    try:
        from apps.partners.models import SystemUser
        su = SystemUser.objects.get(user=user)
        _thread_locals.tenant_id = str(su.sub_center_id) if su.sub_center_id else None
        _thread_locals.user_role = su.role
    except SystemUser.DoesNotExist:
        if user.is_superuser:
            _thread_locals.user_role = 'super_admin'
    except Exception:
        pass


def clear_tenant_context():
    """Clear thread-local tenant context (called after response)."""
    _thread_locals.tenant_id = None
    _thread_locals.user_role = None
    _thread_locals.user_id = None


class TenantContextMiddleware:
    """Resolve tenant for session-authenticated requests (e.g., Django admin)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Resolve immediately if user is already authenticated via session
        user = getattr(request, '_cached_user', None)
        if user and user.is_authenticated:
            set_tenant_context(user)

        response = self.get_response(request)

        # Clear after response
        clear_tenant_context()
        return response
