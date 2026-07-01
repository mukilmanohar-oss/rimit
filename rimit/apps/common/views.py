"""
TenantAwareViewMixin — resolves tenant context AFTER DRF authentication.

DRF's TokenAuthentication runs in `perform_authentication()`, which is
called AFTER middleware. This mixin hooks into `perform_authentication`
to set the thread-local tenant context based on the now-authenticated user.
"""
from apps.common.middleware import set_tenant_context, clear_tenant_context


class TenantAwareViewMixin:
    """Mixin that resolves tenant context after DRF authentication."""

    def perform_authentication(self, request):
        super().perform_authentication(request)
        # Now request.user is resolved (TokenAuthentication has run)
        set_tenant_context(request.user)
