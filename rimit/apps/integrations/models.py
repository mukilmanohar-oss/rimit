"""
Module 4: Marketing & Communication integrations.

Models: lead_ingestion_logs (partitioned in prod).
Webhooks: Meta Lead Ads, Razorpay.
"""
import uuid
from django.db import models
from apps.common.models import UUIDModel, TimeStampedModel


class LeadIngestionLog(UUIDModel, TimeStampedModel):
    """
    Inbound lead from Meta Ads (or other sources).

    Per dbschema.md (partitioned by created_at in prod):
      - id (UUID, PK)
      - source (VARCHAR)        meta | google | referral
      - raw_payload (JSONB)
      - status (VARCHAR)        ingested | fetch_failed | dead_letter | converted
      - error_msg (TEXT)
      - created_at (TIMESTAMP)
    """
    SOURCE_META = 'meta'
    SOURCE_GOOGLE = 'google'
    SOURCE_REFERRAL = 'referral'
    SOURCE_CHOICES = [
        (SOURCE_META, 'Meta Ads (FB/Instagram)'),
        (SOURCE_GOOGLE, 'Google Ads'),
        (SOURCE_REFERRAL, 'Referral'),
    ]

    STATUS_INGESTED = 'ingested'
    STATUS_FETCH_FAILED = 'fetch_failed'
    STATUS_DEAD_LETTER = 'dead_letter'
    STATUS_CONVERTED = 'converted'
    STATUS_CHOICES = [
        (STATUS_INGESTED, 'Ingested'),
        (STATUS_FETCH_FAILED, 'Fetch Failed'),
        (STATUS_DEAD_LETTER, 'Dead Letter'),
        (STATUS_CONVERTED, 'Converted to Student'),
    ]

    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, db_index=True)
    leadgen_id = models.CharField(max_length=200, unique=True, db_index=True,
                                   help_text='Source-system lead ID for dedup')
    raw_payload = models.JSONField(default=dict)
    normalized_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_INGESTED, db_index=True)
    error_msg = models.TextField(blank=True)
    campaign_id = models.CharField(max_length=200, blank=True, db_index=True)
    assigned_sub_center = models.ForeignKey(
        'partners.SubCenter', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_leads',
    )
    converted_student = models.ForeignKey(
        'admissions.Student', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='source_leads',
    )

    class Meta:
        db_table = 'lead_ingestion_logs'
        indexes = [
            models.Index(fields=['source', 'status']),
            models.Index(fields=['campaign_id']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source}:{self.leadgen_id} ({self.status})"
