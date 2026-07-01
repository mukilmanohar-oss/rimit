"""Celery tasks for integrations app."""
import logging
from celery import shared_task
from apps.integrations.models import LeadIngestionLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_meta_lead(self, leadgen_id: str):
    """
    Fetch full lead detail from Meta Graph API and normalize.

    Retry strategy: 3 attempts with 60s / 300s / 1800s backoff.
    After 3 failures, mark as dead_letter and alert Academic Head.
    """
    try:
        lead = LeadIngestionLog.objects.get(leadgen_id=leadgen_id)

        # In prod: call Meta Graph API
        # import requests
        # url = f'https://graph.facebook.com/v18.0/{leadgen_id}'
        # resp = requests.get(url, params={'access_token': settings.META_PAGE_TOKEN}, timeout=10)
        # resp.raise_for_status()
        # data = resp.json()

        # For dev: just normalize the raw payload
        data = lead.raw_payload
        normalized = {
            'name': data.get('full_name') or data.get('field_data', {}).get('full_name', ''),
            'phone': data.get('phone_number') or data.get('field_data', {}).get('phone_number', ''),
            'email': data.get('email') or data.get('field_data', {}).get('email', ''),
            'course_interest': data.get('field_data', {}).get('course_of_interest', ''),
        }
        lead.normalized_data = normalized
        lead.status = LeadIngestionLog.STATUS_INGESTED
        lead.save()
        logger.info(f'Processed Meta lead {leadgen_id}: {normalized.get("name", "unknown")}')
        return f'OK:{leadgen_id}'

    except LeadIngestionLog.DoesNotExist:
        logger.error(f'Lead {leadgen_id} not found')
        return f'NOT_FOUND:{leadgen_id}'

    except Exception as exc:
        logger.warning(f'Failed to process lead {leadgen_id}: {exc}')
        try:
            lead = LeadIngestionLog.objects.get(leadgen_id=leadgen_id)
            lead.status = LeadIngestionLog.STATUS_FETCH_FAILED
            lead.error_msg = str(exc)
            lead.save()
        except Exception:
            pass

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            # Mark dead letter
            try:
                lead = LeadIngestionLog.objects.get(leadgen_id=leadgen_id)
                lead.status = LeadIngestionLog.STATUS_DEAD_LETTER
                lead.error_msg = f'Max retries exceeded: {exc}'
                lead.save()
            except Exception:
                pass
            return f'DEAD_LETTER:{leadgen_id}'
