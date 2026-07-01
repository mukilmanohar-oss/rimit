"""
Module 2 (B2B Partner & User Governance) - foundational models.

SubCenter = the root tenant entity. Every student, enrollment, document
is scoped to exactly one sub_center.

SystemUser = the link between Django's auth User and the tenant + role.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.common.models import UUIDModel, TimeStampedModel


class SubCenter(UUIDModel, TimeStampedModel):
    """
    B2B partner institution. Root tenant.

    Per dbschema.md:
      - id (UUID, PK)
      - center_code (VARCHAR, UNIQUE)  e.g., 'KL-KOC-001'
      - location (VARCHAR)              e.g., 'Kochi, Kerala'
      - status (VARCHAR)                active | suspended | terminated
    """
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_TERMINATED = 'terminated'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_TERMINATED, 'Terminated'),
    ]

    center_code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    state = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, db_index=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)

    class Meta:
        db_table = 'sub_centers'
        ordering = ['center_code']

    def __str__(self):
        return f"{self.center_code} ({self.name})"


class SystemUser(UUIDModel, TimeStampedModel):
    """
    Links Django auth.User to SubCenter + role.

    Per dbschema.md:
      - id (UUID, PK)
      - sub_center_id (FK)
      - role (VARCHAR)   super_admin | academic_head | counselor | finance
      - email (VARCHAR, UNIQUE)

    The 'role' column duplicates Keycloak's role claim for application-layer
    optimization (avoids a Keycloak API call per request).
    """
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_ACADEMIC_HEAD = 'academic_head'
    ROLE_COUNSELOR = 'counselor'
    ROLE_FINANCE = 'finance'
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin (MD)'),
        (ROLE_ACADEMIC_HEAD, 'Academic Head / Manager'),
        (ROLE_COUNSELOR, 'Counselor / Admission Officer'),
        (ROLE_FINANCE, 'Finance / Accounts Officer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='systemuser')
    sub_center = models.ForeignKey(
        SubCenter,
        on_delete=models.PROTECT,
        related_name='users',
        null=True,  # super_admin may not be tied to a specific center
        blank=True,
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, db_index=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    is_mfa_verified = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'system_users'

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_super_admin(self):
        return self.role == self.ROLE_SUPER_ADMIN

    @property
    def can_bypass_tenant(self):
        """Super Admin and Academic Head bypass tenant scoping."""
        return self.role in (self.ROLE_SUPER_ADMIN, self.ROLE_ACADEMIC_HEAD)
