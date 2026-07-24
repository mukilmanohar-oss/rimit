"""
Module 1: Centralized University Aggregator Hub.

Models: universities, courses, fee_structures, university_doc_vault.

Search uses PostgreSQL tsvector + GIN in prod (via SearchVector field);
falls back to standard Django SearchFilter + trigram for SQLite in dev.
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from apps.common.models import UUIDModel, TimeStampedModel


from django.db.models.functions import Lower


class University(UUIDModel, TimeStampedModel):
    """
    Partner university profile.

    Per dbschema.md:
      - id (UUID, PK)
      - name (VARCHAR, UNIQUE)
      - state (VARCHAR)
      - accreditation (VARCHAR)  e.g., 'NAAC A+', 'UGC'
      - created_at (TIMESTAMP)
    """
    name = models.CharField(max_length=300, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    accreditation = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo_uri = models.URLField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Net Remittance Model:
    # Default university share percentage of the Total_Fee.
    # Can be overridden per Course (Course.university_share_percent).
    default_university_share_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Default university share % of total fee (0-100). Used if course override is NULL.',
    )

    class Meta:
        db_table = 'universities'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                Lower('state'),
                name='unique_university_name_state'
            )
        ]

    def __str__(self):
        return self.name


class Course(UUIDModel, TimeStampedModel):
    """
    Course offered by a university.

    Per dbschema.md:
      - id (UUID, PK)
      - university_id (FK)
      - name (VARCHAR)
      - stream (VARCHAR)         e.g., 'Engineering', 'Management', 'Open Schooling'
      - duration_months (INT)
      - is_active (BOOLEAN)
    """
    STREAM_UG = 'Undergraduate'
    STREAM_PG = 'Postgraduate'
    STREAM_DIPLOMA = 'Diploma'
    STREAM_OPEN = 'Open Schooling'
    STREAM_CHOICES = [
        (STREAM_UG, 'Undergraduate'),
        (STREAM_PG, 'Postgraduate'),
        (STREAM_DIPLOMA, 'Diploma'),
        (STREAM_OPEN, 'Open Schooling'),
    ]

    university = models.ForeignKey(
        University, on_delete=models.CASCADE, related_name='courses'
    )
    name = models.CharField(max_length=300, db_index=True)
    stream = models.CharField(max_length=50, choices=STREAM_CHOICES, db_index=True)
    duration_months = models.PositiveIntegerField()
    eligibility_text = models.TextField(blank=True)
    eligibility_criteria_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Net Remittance Model (optional override):
    # If set, this percentage overrides University.default_university_share_percent.
    university_share_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Optional override: university share % of total fee (0-100). NULL = inherit from university.',
    )

    # In prod (PostgreSQL): add a generated tsvector column + GIN index
    search_vector = SearchVectorField(null=True, blank=True)
    # For SQLite dev: use DRF SearchFilter on name + stream + eligibility_text

    class Meta:
        db_table = 'courses'
        indexes = [
            GinIndex(fields=['search_vector']),
            models.Index(fields=['university', 'is_active']),
            models.Index(fields=['stream', 'is_active']),
        ]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.university.name})"


class FeeStructure(UUIDModel, TimeStampedModel):
    """
    Fee structure for a course (one-to-many).

    Per dbschema.md:
      - id (UUID, PK)
      - course_id (FK)
      - fee_type (VARCHAR)    admission | tuition | exam | library
      - amount (DECIMAL)
    """
    FEE_ADMISSION = 'admission'
    FEE_TUITION = 'tuition'
    FEE_EXAM = 'exam'
    FEE_LIBRARY = 'library'
    FEE_LAB = 'lab'
    FEE_OTHER = 'other'
    FEE_TYPE_CHOICES = [
        (FEE_ADMISSION, 'Admission Fee'),
        (FEE_TUITION, 'Tuition Fee'),
        (FEE_EXAM, 'Examination Fee'),
        (FEE_LIBRARY, 'Library Fee'),
        (FEE_LAB, 'Lab Fee'),
        (FEE_OTHER, 'Other'),
        ('', 'Unspecified'),
    ]

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='fees'
    )
    fee_type = models.CharField(max_length=30, choices=FEE_TYPE_CHOICES, db_index=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'fee_structures'
        unique_together = [('course', 'fee_type', 'is_active')]
        ordering = ['fee_type']

    def __str__(self):
        return f"{self.course.name} - {self.fee_type}: {self.amount}"


class UniversityDocVault(UUIDModel, TimeStampedModel):
    """
    Document vault for university prospectuses, calendars, syllabi.

    Per dbschema.md:
      - id (UUID, PK)
      - university_id (FK)
      - doc_type (VARCHAR)    prospectus | calendar | syllabus | notification
      - s3_object_uri (TEXT)
    """
    DOC_PROSPECTUS = 'prospectus'
    DOC_CALENDAR = 'calendar'
    DOC_SYLLABUS = 'syllabus'
    DOC_NOTIFICATION = 'notification'
    DOC_TYPE_CHOICES = [
        (DOC_PROSPECTUS, 'Prospectus'),
        (DOC_CALENDAR, 'Academic Calendar'),
        (DOC_SYLLABUS, 'Syllabus'),
        (DOC_NOTIFICATION, 'Official Notification'),
    ]

    university = models.ForeignKey(
        University, on_delete=models.CASCADE, related_name='documents'
    )
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=300)
    s3_object_uri = models.TextField()
    file_size_bytes = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, default='application/pdf')
    is_public = models.BooleanField(default=True, db_index=True)
    uploaded_by = models.ForeignKey(
        'partners.SystemUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='uploaded_university_docs',
    )

    # Optional: map the document directly to a course (e.g., course-specific prospectus).
    course = models.ForeignKey(
        'aggregator.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text='Optional course mapping for course-specific prospectus/library tiles.',
    )

    class Meta:
        db_table = 'university_doc_vault'
        indexes = [
            models.Index(fields=['university', 'doc_type']),
                models.Index(fields=['course', 'doc_type']),
            models.Index(fields=['is_public']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.university.name} - {self.doc_type}: {self.title}"
