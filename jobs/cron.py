# Cron jobs for periodic job polling

import logging
from django_cron import CronJobBase, Schedule
from django.conf import settings
from jobs.reddit_poller import RedditPollerCronJob
from jobs.email_poller import EmailPollerJob
from utils.validators import check_optional_service

logger = logging.getLogger(__name__)


class PollJobsCronJob(CronJobBase):
    # Cron job that polls Reddit and Email for new job opportunities

    RUN_EVERY_MINS = settings.REDDIT_POLL_INTERVAL_MINUTES

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'jobs.poll_jobs'

    def do(self):
        logger.info("=" * 60)
        logger.info("SCHEDULED JOB POLLING")
        logger.info("=" * 60)

        try:
            reddit_configured = check_optional_service('Reddit', {
                'REDDIT_CLIENT_ID': settings.REDDIT_CLIENT_ID,
                'REDDIT_CLIENT_SECRET': settings.REDDIT_CLIENT_SECRET,
                'REDDIT_USERNAME': settings.REDDIT_USERNAME,
                'REDDIT_PASSWORD': settings.REDDIT_PASSWORD,
            })

            if reddit_configured:
                reddit_job = RedditPollerCronJob()
                reddit_job.do()

            email_configured = check_optional_service('Email', {
                'EMAIL_ADDRESS': settings.EMAIL_ADDRESS,
                'EMAIL_PASSWORD': settings.EMAIL_PASSWORD,
            })

            if email_configured:
                EmailPollerJob.poll()

            logger.info("All scheduled polling completed")

        except Exception as e:
            logger.error(f"Error during scheduled polling: {str(e)}", exc_info=True)
            raise
