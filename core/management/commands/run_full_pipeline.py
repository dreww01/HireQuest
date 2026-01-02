from django.core.management.base import BaseCommand
from jobs.scraper_poller import ScraperPollerJob
from utils.exceptions import MissingAPIKeyError, InvalidAPIKeyError, APIConnectionError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the complete job hunting pipeline (GitHub + RSS + Job Boards + AI + Alerts)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of jobs to scrape per source (default: 20)'
        )
        parser.add_argument(
            '--skip-github',
            action='store_true',
            help='Skip GitHub Issues scraping'
        )
        parser.add_argument(
            '--skip-rss',
            action='store_true',
            help='Skip RSS feed scraping'
        )
        parser.add_argument(
            '--skip-boards',
            action='store_true',
            help='Skip job board scraping'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🤖 JOB HUNT BOT - FULL PIPELINE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        total_errors = 0
        limit = options['limit']

        # Step 1: GitHub Issues Scraping
        if not options['skip_github']:
            self.stdout.write(self.style.WARNING('🐙 STEP 1: GitHub Issues Scraping'))
            self.stdout.write('-' * 70)
            try:
                ScraperPollerJob.poll_github(limit=limit)
                self.stdout.write(self.style.SUCCESS('✅ GitHub scraping complete'))
            except MissingAPIKeyError as e:
                self.stdout.write(self.style.ERROR(f'❌ GitHub scraping failed - missing credentials'))
                self.stdout.write(self.style.ERROR(f'   {str(e)}'))
                total_errors += 1
            except (InvalidAPIKeyError, APIConnectionError) as e:
                self.stdout.write(self.style.ERROR(f'❌ GitHub scraping failed'))
                self.stdout.write(self.style.ERROR(f'   {str(e)}'))
                total_errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ GitHub scraping failed: {str(e)}'))
                total_errors += 1
            self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('🐙 GitHub scraping skipped (--skip-github)'))
            self.stdout.write('')

        # Step 2: RSS Feed Scraping
        if not options['skip_rss']:
            self.stdout.write(self.style.WARNING('📡 STEP 2: RSS Feed Scraping'))
            self.stdout.write('-' * 70)
            try:
                ScraperPollerJob.poll_rss_feeds(limit=limit)
                self.stdout.write(self.style.SUCCESS('✅ RSS scraping complete'))
            except (InvalidAPIKeyError, APIConnectionError) as e:
                self.stdout.write(self.style.ERROR(f'❌ RSS scraping failed'))
                self.stdout.write(self.style.ERROR(f'   {str(e)}'))
                total_errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ RSS scraping failed: {str(e)}'))
                total_errors += 1
            self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('📡 RSS scraping skipped (--skip-rss)'))
            self.stdout.write('')

        # Step 3: Job Board Scraping
        if not options['skip_boards']:
            self.stdout.write(self.style.WARNING('🌐 STEP 3: Job Board Scraping'))
            self.stdout.write('-' * 70)
            try:
                ScraperPollerJob.poll_job_boards(limit=limit)
                self.stdout.write(self.style.SUCCESS('✅ Job board scraping complete'))
            except (InvalidAPIKeyError, APIConnectionError) as e:
                self.stdout.write(self.style.ERROR(f'❌ Job board scraping failed'))
                self.stdout.write(self.style.ERROR(f'   {str(e)}'))
                total_errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Job board scraping failed: {str(e)}'))
                total_errors += 1
            self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('🌐 Job board scraping skipped (--skip-boards)'))
            self.stdout.write('')

        # Summary
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('📊 PIPELINE SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        from core.models import JobPost, QualificationScore, AlertStatus

        total_jobs = JobPost.objects.count()
        total_qualified = QualificationScore.objects.count()
        total_alerted = AlertStatus.objects.count()
        recent_jobs = JobPost.objects.order_by('-created_at')[:5]

        self.stdout.write(f'Total jobs in database: {total_jobs}')
        self.stdout.write(f'Total qualified: {total_qualified}')
        self.stdout.write(f'Total alerts sent: {total_alerted}')
        self.stdout.write(f'Errors encountered: {total_errors}')
        self.stdout.write('')

        if recent_jobs.exists():
            self.stdout.write(self.style.WARNING('📋 Recent jobs (last 5):'))
            for idx, job in enumerate(recent_jobs, 1):
                title = job.title[:60] + '...' if len(job.title) > 60 else job.title
                self.stdout.write(f'  {idx}. [{job.source.type}] {title}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))

        if total_errors == 0:
            self.stdout.write(self.style.SUCCESS('✅ Pipeline completed successfully!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Pipeline completed with {total_errors} error(s)'))

        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Run "python manage.py runserver" to view dashboard')
        self.stdout.write('  2. Visit http://localhost:8000/admin to manage jobs')
        self.stdout.write('  3. Check Telegram for high-quality job alerts')
        self.stdout.write(self.style.SUCCESS('=' * 70))


