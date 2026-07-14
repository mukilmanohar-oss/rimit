"""
Module 2 (B2B Partner & User Governance) - foundational models.

SubCenter = the root tenant entity. Every student, enrollment, document
is scoped to exactly one sub_center.

SystemUser = the link between Django's auth User and the tenant + role.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
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

    # Net Remittance Model:
    # This is the sub-center's commission percentage of the Gross Commission Pool.
    # e.g., 75.00 means the sub-center keeps 75% of (Total_Fee - University_Share).
    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Sub-center commission % of gross pool (0-100). Deducted upfront at checkout.',
    )

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
    ROLE_SUBCENTER = 'subcenter'
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, 'Super Admin (MD)'),
        (ROLE_ACADEMIC_HEAD, 'Academic Head / Manager'),
        (ROLE_COUNSELOR, 'Counselor / Admission Officer'),
        (ROLE_FINANCE, 'Finance / Accounts Officer'),
        (ROLE_SUBCENTER, 'Sub-Center Admin'),
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


class SubCenterUniversityMapping(UUIDModel, TimeStampedModel):
    """Explicit allow-list: which universities a sub-center can access."""

    sub_center = models.ForeignKey(
        SubCenter,
        on_delete=models.CASCADE,
        related_name='university_mappings',
    )
    university = models.ForeignKey(
        'aggregator.University',
        on_delete=models.CASCADE,
        related_name='sub_center_mappings',
    )

    class Meta:
        db_table = 'sub_center_university_mappings'
        unique_together = [('sub_center', 'university')]
        indexes = [
            models.Index(fields=['sub_center', 'university']),
            models.Index(fields=['university']),
        ]

    def __str__(self):
        return f"{self.sub_center.center_code} → {self.university.name}"
