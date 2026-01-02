"""Management command to scrape GitHub Issues for job opportunities"""
from django.core.management.base import BaseCommand
from jobs.scraper_poller import ScraperPollerJob


class Command(BaseCommand):
    help = 'Scrape GitHub Issues for paid job opportunities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of issues to scrape (default: 20)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting GitHub Issues scraping...'))

        try:
            ScraperPollerJob.poll_github(limit=options['limit'])
            self.stdout.write(self.style.SUCCESS('✅ GitHub scraping complete'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ GitHub scraping failed: {str(e)}'))
            raise
