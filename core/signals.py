from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from core.models import QualificationScore, JobPost, AlertStatus
from integrations.telegram_client import TelegramClient
from utils.exceptions import MissingAPIKeyError, InvalidAPIKeyError, APIConnectionError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


# This signal receiver triggers after a QualificationScore is saved
@receiver(post_save, sender=QualificationScore)
def alert_high_quality_job(sender, instance, created, **kwargs):
    # Send Telegram alert when a HIGH or MEDIUM quality job is qualified
    if not created:
        return

    if instance.classification not in [QualificationScore.HIGH, QualificationScore.MEDIUM]:
        logger.info(f"Job qualified as {instance.classification.upper()}, skipping alert")
        return

    job_post = instance.job_post

    if hasattr(job_post, 'alert'):
        logger.warning(f"Alert already exists for job: {job_post.title}")
        return

    try:
        telegram = TelegramClient()
    except (MissingAPIKeyError, InvalidAPIKeyError, APIConnectionError) as e:
        logger.warning(f"Telegram not available for alert: {str(e)}")
        return

    try:
        draft = None
        if hasattr(job_post, 'draft'):
            draft = job_post.draft

        dashboard_path = reverse('job_detail', kwargs={'pk': job_post.pk})
        base_url = getattr(settings, 'SITE_BASE_URL', 'http://localhost:8000')
        dashboard_url = f"{base_url}{dashboard_path}"
        message_id = telegram.send_alert(job_post, instance, draft, dashboard_url)

        AlertStatus.objects.create(
            job_post=job_post,
            telegram_message_id=str(message_id)
        )

        job_post.status = JobPost.ALERTED
        job_post.save(update_fields=['status'])

        logger.info(f"Telegram alert sent for {instance.classification.upper()} quality job: {job_post.title}")

    except Exception as e:
        logger.error(f"Failed to send Telegram alert for {job_post.title}: {str(e)}")
