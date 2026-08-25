from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import JobPost, Source
from integrations.github_scraper import GitHubScraper
from integrations.huggingface_client import HuggingFaceClient
from integrations.telegram_client import TelegramClient


class Command(BaseCommand):
    help = 'Validate all API connections (GitHub, Telegram, Hugging Face)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each test',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)

        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('HIREQUEST - API VALIDATION'))
        self.stdout.write('=' * 70)
        self.stdout.write('')

        results = {
            'github': {'passed': False, 'error': None},
            'telegram': {'passed': False, 'error': None},
            'huggingface': {'passed': False, 'error': None},
        }

        # Test GitHub
        self.stdout.write(self.style.HTTP_INFO('[1/3] Testing GitHub API...'))
        try:
            github_token = getattr(settings, 'GITHUB_TOKEN', '')
            scraper = GitHubScraper(github_token=github_token)
            jobs = scraper.search_issues(keywords=['paid'], limit=1)

            if verbose and jobs:
                job = jobs[0]
                self.stdout.write(f"  -> Found issue: {job['title'][:50]}...")
                self.stdout.write(f"  -> Author: {job['author']}")

            self.stdout.write(self.style.SUCCESS('  [OK] GitHub: CONNECTED'))
            results['github']['passed'] = True

        except Exception as e:
            self.stdout.write(self.style.ERROR('  [FAIL] GitHub: FAILED'))
            results['github']['error'] = str(e)
            if verbose:
                self.stdout.write(self.style.WARNING(f'     Error: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'     {str(e)[:80]}...'))

        self.stdout.write('')

        # Test Telegram
        self.stdout.write(self.style.HTTP_INFO('[2/3] Testing Telegram Bot...'))
        try:
            client = TelegramClient()

            test_source = Source(type=Source.GITHUB_ISSUE, identifier='test')
            test_job = JobPost(
                source=test_source,
                title='API Validation Test',
                body='This is an automated test message from the HireQuest API validator.',
                author='ValidationBot',
                url='https://example.com/test',
                timestamp=timezone.now(),
            )

            message_id = client.send_simple_alert(test_job)

            if verbose:
                self.stdout.write(f'  -> Message sent with ID: {message_id}')
                self.stdout.write(f'  -> Chat ID: {client.chat_id}')

            self.stdout.write(self.style.SUCCESS('  [OK] Telegram: CONNECTED'))
            self.stdout.write('     Check your Telegram app for test message!')
            results['telegram']['passed'] = True

        except Exception as e:
            self.stdout.write(self.style.ERROR('  [FAIL] Telegram: FAILED'))
            results['telegram']['error'] = str(e)
            if verbose:
                self.stdout.write(self.style.WARNING(f'     Error: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'     {str(e)[:80]}...'))

        self.stdout.write('')

        # Test Hugging Face
        self.stdout.write(self.style.HTTP_INFO('[3/3] Testing Hugging Face AI...'))
        try:
            client = HuggingFaceClient()
            test_result = client.test_connection()

            if verbose:
                self.stdout.write(f'  -> Model: {client.model}')

            self.stdout.write(self.style.SUCCESS('  [OK] Hugging Face: CONNECTED'))
            results['huggingface']['passed'] = True

        except Exception as e:
            self.stdout.write(self.style.ERROR('  [FAIL] Hugging Face: FAILED'))
            results['huggingface']['error'] = str(e)
            if verbose:
                self.stdout.write(self.style.WARNING(f'     Error: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'     {str(e)[:80]}...'))

        self.stdout.write('')
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('VALIDATION SUMMARY'))
        self.stdout.write('=' * 70)

        # Summary
        total = len(results)
        passed = sum(1 for r in results.values() if r['passed'])
        failed = total - passed

        self.stdout.write(f'Total APIs Tested: {total}')
        self.stdout.write(self.style.SUCCESS(f'Passed: {passed}') if passed > 0 else 'Passed: 0')
        if failed > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed}'))

        self.stdout.write('')

        # Individual results
        for service, result in results.items():
            if result['passed']:
                self.stdout.write(self.style.SUCCESS(f'[OK] {service.upper()}: PASS'))
            else:
                self.stdout.write(self.style.ERROR(f'[FAIL] {service.upper()}: FAIL'))
                if result['error']:
                    error_msg = result['error'][:100] + ('...' if len(result['error']) > 100 else '')
                    self.stdout.write(self.style.WARNING(f'   > {error_msg}'))

        self.stdout.write('')
