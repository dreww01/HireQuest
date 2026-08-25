# Cron jobs for periodic job polling

import logging
from django_cron import CronJobBase, Schedule
from django.conf import settings
from jobs.scraper_poller import ScraperPollerJob

logger = logging.getLogger(__name__)


class PollJobsCronJob(CronJobBase):
    # Cron job that polls GitHub, RSS feeds, and job boards for new opportunities

    RUN_EVERY_MINS = getattr(settings, 'SCRAPE_INTERVAL_MINUTES', 60)

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'jobs.poll_jobs'

    def do(self):
        logger.info("=" * 60)
        logger.info("SCHEDULED JOB POLLING")
        logger.info("=" * 60)

        try:
            limit = getattr(settings, 'MAX_JOBS_PER_SOURCE', 20)
            ScraperPollerJob.poll_github(limit=limit)
            ScraperPollerJob.poll_rss_feeds(limit=limit)
            ScraperPollerJob.poll_job_boards(limit=limit)
            logger.info("All scheduled polling completed")

        except Exception as e:
            logger.error(f"Error during scheduled polling: {str(e)}", exc_info=True)
            raise
