"""
Common abstract models, managers, and utilities used across all apps.

All tenant-scoped models inherit from TenantOwnedModel, which:
1. Adds a `sub_center` FK
2. Routes queries through TenantManager which auto-filters by current tenant
   (set by TenantContextMiddleware) — this is the app-layer equivalent of
   PostgreSQL RLS, which is the production enforcement mechanism.
"""
import hashlib
import uuid
from django.db import models
from django.conf import settings


def generate_uuid():
    """Generate UUID4 as string (used as default for UUID PKs)."""
    return uuid.uuid4()


def hash_aadhar(aadhar_number: str) -> str:
    """
    Hash Aadhar number with salt using SHA-256.
    Production uses pgcrypto; this app-layer hash is the dev equivalent.
    Never store Aadhar in plaintext.
    """
    if not aadhar_number:
        return ''
    salted = f"{settings.AADHAR_HASH_SALT}:{aadhar_number.strip()}"
    return hashlib.sha256(salted.encode()).hexdigest()


class TimeStampedModel(models.Model):
    """Abstract base with created_at / updated_at."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base with UUID PK (per dbschema.md)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TenantManager(models.Manager):
    """
    Manager that auto-filters by current tenant when accessed via the ORM.

    Reads the current sub_center_id from a thread-local set by
    TenantContextMiddleware. If the user has 'super_admin' role, no filter
    is applied (mirrors PostgreSQL BYPASSRLS).

    This is the app-layer safety net. In production with PostgreSQL,
    Row-Level Security policies provide the authoritative enforcement —
    this manager prevents accidental N+1 leaks even before RLS is hit.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        from apps.common.middleware import _current_tenant_id, _current_user_role
        tenant_id = _current_tenant_id()
        role = _current_user_role()

        # Super Admin / Academic Head bypass tenant filter
        if role in ('super_admin', 'academic_head'):
            return qs

        # Apply tenant filter if a tenant is set
        if tenant_id is not None:
            # 'sub_center_id' is the FK column on all TenantOwnedModel subclasses
            return qs.filter(sub_center_id=tenant_id)

        # No tenant context (e.g., unauthenticated request) → empty queryset
        return qs.none()


class TenantOwnedModel(TimeStampedModel, UUIDModel):
    """
    Abstract base for all tenant-scoped tables.

    All student, enrollment, document, payment records inherit from this.
    The `sub_center` FK + TenantManager provides app-layer RLS-equivalent.
    """
    sub_center = models.ForeignKey(
        'partners.SubCenter',
        on_delete=models.PROTECT,
        related_name='+',
        help_text='Owning sub-center (tenant). Filtered by TenantManager.',
    )

    objects = TenantManager()
    all_objects = models.Manager()  # Unfiltered, for super_admin / migrations only

    class Meta:
        abstract = True
