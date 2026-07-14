"""
Module 2 + 3: Student Registration, Academic Histories, Documents, Enrollments.

All tenant-scoped models inherit from TenantOwnedModel — TenantManager
auto-filters by current sub_center_id (app-layer RLS equivalent).
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.common.models import UUIDModel, TimeStampedModel, TenantOwnedModel, hash_aadhar
from apps.aggregator.models import Course


class Student(TenantOwnedModel):
    """
    Student demographic profile (tenant-scoped).

    Per dbschema.md:
      - id (UUID, PK)
      - sub_center_id (FK)
      - full_name (VARCHAR)
      - dob (DATE)
      - primary_phone (VARCHAR)
      - email (VARCHAR)
      - aadhar_number (VARCHAR, UNIQUE) — stored as SHA-256 hash
      - address_data (JSONB)
    """
    GENDER_MALE = 'M'
    GENDER_FEMALE = 'F'
    GENDER_OTHER = 'O'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_OTHER, 'Other'),
    ]

    full_name = models.CharField(max_length=300, db_index=True)
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    primary_phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    aadhar_hash = models.CharField(max_length=64, db_index=True,
                                    help_text='SHA-256 hash of salted Aadhar number')
    address_data = models.JSONField(default=dict, blank=True)
    data_subject_consent = models.JSONField(
        default=dict, blank=True,
        help_text='DPDP Act 2023: {consent_given: bool, timestamp: ISO8601, scope: [...]}'
    )
    parent_name = models.CharField(max_length=300, blank=True)  # legacy/generic
    father_name = models.CharField(max_length=300, blank=True)
    mother_name = models.CharField(max_length=300, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    alternate_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Demographic fields per new schema
    category = models.CharField(max_length=50, blank=True)
    employment_status = models.CharField(max_length=50, blank=True)
    marital_status = models.CharField(max_length=50, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    abc_id = models.CharField(max_length=12, blank=True)
    deb_id = models.CharField(max_length=50, blank=True)
    receipt_s3_url = models.URLField(max_length=500, blank=True)
    admission_type = models.CharField(max_length=50, blank=True)
    admission_semester = models.CharField(max_length=10, blank=True)

    # Lead specific enhancements
    LEAD_STATUS_PENDING = 'Pending Payment'
    LEAD_STATUS_ENROLLED = 'Enrolled'
    LEAD_STATUS_CHOICES = [
        (LEAD_STATUS_PENDING, 'Pending Payment'),
        (LEAD_STATUS_ENROLLED, 'Enrolled'),
    ]

    lead_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_leads')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_leads')
    session = models.ForeignKey('rules.IntakeSession', on_delete=models.SET_NULL, null=True, blank=True, related_name='student_leads')
    sub_course = models.CharField(max_length=200, blank=True)
    lead_status = models.CharField(max_length=50, choices=LEAD_STATUS_CHOICES, default=LEAD_STATUS_PENDING, db_index=True)

    class Meta:
        db_table = 'students'
        indexes = [
            models.Index(fields=['sub_center', 'is_active']),
            models.Index(fields=['primary_phone']),
            models.Index(fields=['full_name']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.primary_phone})"

    def set_aadhar(self, aadhar_number: str):
        """Hash and store Aadhar number (never store plaintext)."""
        self.aadhar_hash = hash_aadhar(aadhar_number)


class StudentAddress(UUIDModel, TimeStampedModel):
    """
    Student discrete localized address block (replaces JSON blob).
    """
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='address_block')
    perm_domicile_type = models.CharField(max_length=50)
    domicile_state = models.CharField(max_length=100, blank=True)
    perm_address = models.TextField()
    perm_country = models.CharField(max_length=100)
    perm_state = models.CharField(max_length=100)
    perm_district = models.CharField(max_length=100)
    perm_city = models.CharField(max_length=100)
    perm_pincode = models.CharField(max_length=6)

    corr_address = models.TextField()
    corr_country = models.CharField(max_length=100)
    corr_state = models.CharField(max_length=100)
    corr_district = models.CharField(max_length=100)
    corr_city = models.CharField(max_length=100)
    corr_pincode = models.CharField(max_length=6)

    class Meta:
        db_table = 'student_addresses'

    def __str__(self):
        return f"Address block for {self.student.full_name}"


class StudentAcademicHistory(UUIDModel, TimeStampedModel):
    """
    Academic qualification history (10th, 12th, UG, PG).

    Per dbschema.md:
      - id (UUID, PK)
      - student_id (FK)
      - qualification (VARCHAR)
      - institution (VARCHAR)
      - board_university (VARCHAR)
      - year_of_passing (INT)
      - score_type (VARCHAR)    percentage | cgpa | grade
      - score_value (DECIMAL)

    Note: NOT a TenantOwnedModel — derives tenant via student FK.
    TenantManager not applied; queries must always go via student.
    """
    QUAL_10TH = '10th'
    QUAL_12TH = '12th'
    QUAL_UG = 'UG'
    QUAL_PG = 'PG'
    QUAL_DIPLOMA = 'Diploma'
    QUAL_CHOICES = [
        (QUAL_10TH, '10th Standard'),
        (QUAL_12TH, '12th Standard'),
        (QUAL_UG, 'Undergraduate'),
        (QUAL_PG, 'Postgraduate'),
        (QUAL_DIPLOMA, 'Diploma'),
    ]

    SCORE_PERCENTAGE = 'percentage'
    SCORE_CGPA = 'cgpa'
    SCORE_GRADE = 'grade'
    SCORE_CHOICES = [
        (SCORE_PERCENTAGE, 'Percentage'),
        (SCORE_CGPA, 'CGPA'),
        (SCORE_GRADE, 'Grade'),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='academic_histories'
    )
    qualification = models.CharField(max_length=20, choices=QUAL_CHOICES, db_index=True)
    examination = models.CharField(max_length=100, blank=True)
    institution = models.CharField(max_length=300)
    board_university = models.CharField(max_length=300)
    year_of_passing = models.PositiveIntegerField()
    score_type = models.CharField(max_length=20, choices=SCORE_CHOICES)
    score_value = models.DecimalField(max_digits=5, decimal_places=2)
    percentage_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    result = models.CharField(max_length=50, blank=True)
    subject_stream = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'student_academic_histories'
        indexes = [
            models.Index(fields=['student', 'qualification']),
        ]
        ordering = ['-year_of_passing']

    def __str__(self):
        return f"{self.student.full_name} - {self.qualification} ({self.year_of_passing})"


class StudentDoc(UUIDModel, TimeStampedModel):
    """
    Student document upload (identity proofs, marklists, etc.).

    Per dbschema.md:
      - id (UUID, PK)
      - student_id (FK)
      - academic_id (FK, NULLABLE)
      - doc_category (VARCHAR)
      - s3_object_uri (TEXT)
      - status (VARCHAR)   pending | verified | rejected
    """
    CATEGORY_IDENTITY = 'identity'
    CATEGORY_MARKLIST = 'marklist'
    CATEGORY_MIGRATION = 'migration'
    CATEGORY_EXPERIENCE = 'experience'
    CATEGORY_PHOTO = 'photo'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_IDENTITY, 'Identity Proof'),
        (CATEGORY_MARKLIST, 'Marklist / Certificate'),
        (CATEGORY_MIGRATION, 'Migration Certificate'),
        (CATEGORY_EXPERIENCE, 'Experience Certificate'),
        (CATEGORY_PHOTO, 'Passport Photo'),
        (CATEGORY_OTHER, 'Other'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Verification'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='documents'
    )
    academic_history = models.ForeignKey(
        StudentAcademicHistory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents'
    )
    doc_category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, db_index=True)
    title = models.CharField(max_length=300, blank=True)
    s3_object_uri = models.TextField()
    file_size_bytes = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, default='application/pdf')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    rejection_reason = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        'partners.SystemUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verified_student_docs',
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'student_docs'
        indexes = [
            models.Index(fields=['student', 'doc_category']),
            models.Index(fields=['status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.doc_category} ({self.status})"


class Enrollment(TenantOwnedModel):
    """
    Student enrollment in a course for a specific intake session.

    Per dbschema.md:
      - id (UUID, PK)
      - student_id (FK)
      - course_id (FK)
      - session_id (FK)
      - status (VARCHAR)
      - created_at (TIMESTAMP)

    Status transitions (RFP Module 2):
      Applied → Document Verified → Fee Pending → Fee Paid → Enrolled → Enrollment Generated

    Session Enforcement Matrix (RFP Module 3):
      Validated on create via rules_configurations.
    """
    STATUS_APPLIED = 'Applied'
    STATUS_DOC_VERIFIED = 'Document Verified'
    STATUS_FEE_PENDING = 'Fee Pending'
    STATUS_FEE_PAID = 'Fee Paid'
    STATUS_ENROLLED = 'Enrolled'
    STATUS_ENROLLMENT_GENERATED = 'Enrollment Generated'
    STATUS_CANCELLED = 'Cancelled'
    STATUS_CHOICES = [
        (STATUS_APPLIED, 'Applied'),
        (STATUS_DOC_VERIFIED, 'Document Verified'),
        (STATUS_FEE_PENDING, 'Fee Pending'),
        (STATUS_FEE_PAID, 'Fee Paid'),
        (STATUS_ENROLLED, 'Enrolled'),
        (STATUS_ENROLLMENT_GENERATED, 'Enrollment Generated'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # Valid status transitions (state machine)
    TRANSITIONS = {
        STATUS_APPLIED: [STATUS_DOC_VERIFIED, STATUS_CANCELLED],
        STATUS_DOC_VERIFIED: [STATUS_FEE_PENDING, STATUS_CANCELLED],
        STATUS_FEE_PENDING: [STATUS_FEE_PAID, STATUS_CANCELLED],
        STATUS_FEE_PAID: [STATUS_ENROLLED],
        STATUS_ENROLLED: [STATUS_ENROLLMENT_GENERATED],
        STATUS_ENROLLMENT_GENERATED: [],
        STATUS_CANCELLED: [],
    }

    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name='enrollments'
    )
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name='enrollments'
    )
    session = models.ForeignKey(
        'rules.IntakeSession', on_delete=models.PROTECT, related_name='enrollments'
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_APPLIED, db_index=True)
    enrollment_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    notes = models.TextField(blank=True)
    rejected_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = [['student', 'course', 'session']]
        indexes = [
            models.Index(fields=['sub_center', 'status']),
            models.Index(fields=['session', 'status']),
            models.Index(fields=['student', 'course', 'session']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} → {self.course.name} ({self.status})"

    def clean(self):
        """Validate status transitions and business logic."""
        if not self._state.adding:
            old = Enrollment.all_objects.get(pk=self.pk)
            if old.status != self.status:
                allowed = self.TRANSITIONS.get(old.status, [])
                if self.status not in allowed:
                    raise ValidationError({
                        'status': f'Invalid transition: {old.status} → {self.status}. '
                                  f'Allowed: {allowed}'
                    })
                
                # Business Logic: Enforce Enrollment-to-Document linkage
                if self.status == self.STATUS_DOC_VERIFIED:
                    docs = self.student.documents.all()
                    if not docs.exists():
                        raise ValidationError({'status': 'Cannot verify documents: Student has no documents uploaded.'})
                    if docs.filter(status='rejected').exists():
                        raise ValidationError({'status': 'Cannot verify documents: Student has rejected documents.'})
                    if docs.filter(status='pending').exists():
                        raise ValidationError({'status': 'Cannot verify documents: Student has pending documents to be reviewed.'})

                # Business Logic: Enforce Fee Validation
                if self.status == self.STATUS_FEE_PAID:
                    # check if the sum of captured payments >= required fees
                    from django.db.models import Sum
                    from apps.finance.models import PaymentLedger
                    # sum of course fees
                    required_fee = self.course.fees.filter(is_active=True).aggregate(Sum('amount'))['amount__sum'] or 0
                    paid = PaymentLedger.all_objects.filter(enrollment=self, status='captured').aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
                    if paid < required_fee:
                        raise ValidationError({
                            'status': f'Cannot transition to Fee Paid: Total fee required is ₹{required_fee}, but only ₹{paid} has been captured.'
                        })

    def save(self, *args, **kwargs):
        self.clean()
        if self.status == self.STATUS_ENROLLMENT_GENERATED and not self.enrollment_number:
            import datetime
            year = datetime.date.today().year
            # simple auto-increment logic or random UUID slice for uniqueness
            import random
            rand_suffix = str(random.randint(10000, 99999))
            self.enrollment_number = f"ENR/{year}/{self.sub_center_id}/{rand_suffix}"
        super().save(*args, **kwargs)

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.TRANSITIONS.get(self.status, [])
