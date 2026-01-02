"""Management command to scrape job boards using BeautifulSoup"""
from django.core.management.base import BaseCommand
from jobs.scraper_poller import ScraperPollerJob


class Command(BaseCommand):
    help = 'Scrape job boards using BeautifulSoup (We Work Remotely, RemoteOK)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of jobs per board (default: 20)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting job board scraping...'))

        try:
            ScraperPollerJob.poll_job_boards(limit=options['limit'])
            self.stdout.write(self.style.SUCCESS('✅ Job board scraping complete'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Job board scraping failed: {str(e)}'))
            raise
