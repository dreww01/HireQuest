from django.core.management.base import BaseCommand
from jobs.scraper_poller import ScraperPollerJob
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Poll all configured sources, qualify leads, and send alerts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of posts to fetch per source (default: 20)'
        )

    def handle(self, *args, **options):
        limit = options['limit']

        self.stdout.write(self.style.SUCCESS('Starting polling and alerting pipeline...'))

        try:
            ScraperPollerJob.poll_github(limit=limit)
            ScraperPollerJob.poll_rss_feeds(limit=limit)
            ScraperPollerJob.poll_job_boards(limit=limit)

            self.stdout.write(self.style.SUCCESS('Polling and alerting complete!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in polling and alerting pipeline: {str(e)}'))
            raise
