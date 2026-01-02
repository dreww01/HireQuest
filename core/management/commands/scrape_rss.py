"""Management command to scrape RSS feeds from job boards"""
from django.core.management.base import BaseCommand
from jobs.scraper_poller import ScraperPollerJob


class Command(BaseCommand):
    help = 'Scrape RSS feeds from job boards (RemoteOK, We Work Remotely, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of jobs per feed (default: 20)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting RSS feed scraping...'))

        try:
            ScraperPollerJob.poll_rss_feeds(limit=options['limit'])
            self.stdout.write(self.style.SUCCESS('✅ RSS scraping complete'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ RSS scraping failed: {str(e)}'))
            raise
