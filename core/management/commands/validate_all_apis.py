from django.core.management.base import BaseCommand
from django.conf import settings
from integrations.email_client import EmailClient
from integrations.telegram_client import TelegramClient
from integrations.huggingface_client import HuggingFaceClient
from integrations.reddit_client import RedditClient
from core.models import JobPost, Source
from datetime import datetime
import sys


class Command(BaseCommand):
    help = 'Validate all API connections (Reddit, Email, Telegram, Hugging Face)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each test',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)

        self.stdout.write('=' * 70)
        self.stdout.write(self.style.HTTP_INFO('JOB HUNT BOT - API VALIDATION'))
        self.stdout.write('=' * 70)
        self.stdout.write('')

        results = {
            'reddit': {'passed': False, 'error': None},
            'email': {'passed': False, 'error': None},
            'telegram': {'passed': False, 'error': None},
            'huggingface': {'passed': False, 'error': None},
        }

        # Test Reddit
        self.stdout.write(self.style.HTTP_INFO('[1/4] Testing Reddit API...'))
        try:
            client = RedditClient()
            posts = client.fetch_recent_posts('forhire', limit=1)

            if verbose and posts:
                post = posts[0]
                self.stdout.write(f"  -> Found post: {post['title'][:50]}...")
                self.stdout.write(f"  -> Author: {post['author']}")

            self.stdout.write(self.style.SUCCESS('  [OK] Reddit: CONNECTED'))
            results['reddit']['passed'] = True

        except Exception as e:
            self.stdout.write(self.style.ERROR('  [FAIL] Reddit: FAILED'))
            results['reddit']['error'] = str(e)
            if verbose:
                self.stdout.write(self.style.WARNING(f'     Error: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'     {str(e)[:80]}...'))

        self.stdout.write('')

        # Test Email
        self.stdout.write(self.style.HTTP_INFO('[2/4] Testing Email Connection...'))
        try:
            client = EmailClient()
            emails = client.fetch_recent_emails(limit=1)

            if verbose and emails:
                email_data = emails[0]
                self.stdout.write(f"  -> Found unread email from: {email_data['from']}")
                self.stdout.write(f"  -> Subject: {email_data['subject']}")

            self.stdout.write(self.style.SUCCESS('  [OK] Email: CONNECTED'))
            if not emails:
                self.stdout.write(self.style.WARNING('     (No unread emails, but connection works)'))
            results['email']['passed'] = True

        except Exception as e:
            self.stdout.write(self.style.ERROR('  [FAIL] Email: FAILED'))
            results['email']['error'] = str(e)
            if verbose:
                self.stdout.write(self.style.WARNING(f'     Error: {str(e)}'))
            else:
                self.stdout.write(self.style.WARNING(f'     {str(e)[:80]}...'))

        self.stdout.write('')

        # Test Telegram
        self.stdout.write(self.style.HTTP_INFO('[3/4] Testing Telegram Bot...'))
        try:
            client = TelegramClient()

            # Create a test job post
            test_source = Source(type=Source.NEWSLETTER, identifier='test')
            test_job = JobPost(
                source=test_source,
                title='API Validation Test',
                body='This is an automated test message from the Job Hunt Bot API validator.',
                author='ValidationBot',
                url='https://example.com/test',
                timestamp=datetime.now()
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
        self.stdout.write(self.style.HTTP_INFO('[4/4] Testing Hugging Face AI...'))
        try:
            client = HuggingFaceClient()
            test_result = client.test_connection()

            if verbose:
                self.stdout.write(f'  -> Model: {client.model}')
                self.stdout.write(f'  -> API URL: {client.api_url}')

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

        # Individual results with color coding
        for service, result in results.items():
            if result['passed']:
                self.stdout.write(self.style.SUCCESS(f'[OK] {service.upper()}: PASS'))
            else:
                self.stdout.write(self.style.ERROR(f'[FAIL] {service.upper()}: FAIL'))
                if result['error']:
                    # Show first 100 chars of error
                    error_msg = result['error'][:100] + ('...' if len(result['error']) > 100 else '')
                    self.stdout.write(self.style.WARNING(f'   > {error_msg}'))

        self.stdout.write('')

        # Recommendations
        if failed > 0:
            self.stdout.write(self.style.WARNING('=== TROUBLESHOOTING GUIDE ==='))
            self.stdout.write('')

            if not results['reddit']['passed']:
                self.stdout.write(self.style.ERROR('[REDDIT] Reddit API Configuration:'))
                self.stdout.write('   1. Check REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env')
                self.stdout.write('   2. Check REDDIT_USERNAME and REDDIT_PASSWORD in .env')
                self.stdout.write('   3. Create Reddit app at: https://www.reddit.com/prefs/apps')
                self.stdout.write('   4. Select "script" type application')
                self.stdout.write('')

            if not results['email']['passed']:
                self.stdout.write(self.style.ERROR('[EMAIL] Email Configuration:'))
                self.stdout.write('   1. Check EMAIL_ADDRESS and EMAIL_PASSWORD in .env')
                self.stdout.write('   2. For Gmail, use an App Password from:')
                self.stdout.write('      https://myaccount.google.com/apppasswords')
                self.stdout.write('')

            if not results['telegram']['passed']:
                self.stdout.write(self.style.ERROR('[TELEGRAM] Telegram Configuration:'))
                self.stdout.write('   1. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env')
                self.stdout.write('   2. Create a bot via @BotFather on Telegram')
                self.stdout.write('   3. Get chat ID from:')
                self.stdout.write('      https://api.telegram.org/bot<TOKEN>/getUpdates')
                self.stdout.write('')

            if not results['huggingface']['passed']:
                self.stdout.write(self.style.ERROR('[AI] Hugging Face Configuration:'))
                self.stdout.write('   1. Check HUGGINGFACE_API_KEY in .env')
                self.stdout.write('   2. Get API key from:')
                self.stdout.write('      https://huggingface.co/settings/tokens')
                self.stdout.write('   3. Verify model name in settings')
                self.stdout.write('')

            self.stdout.write(self.style.WARNING('TIP: Run with --verbose flag for detailed error messages'))
            self.stdout.write('')

        else:
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write(self.style.SUCCESS('[SUCCESS] ALL APIS CONFIGURED CORRECTLY!'))
            self.stdout.write(self.style.SUCCESS('=' * 70))
            self.stdout.write('')
            self.stdout.write('You can now:')
            self.stdout.write('  - Run job polling: python manage.py runcrons --force')
            self.stdout.write('  - Test full pipeline: python manage.py run_full_pipeline')
            self.stdout.write('  - Monitor cron jobs: check job_hunt_bot.log')
            self.stdout.write('')

        self.stdout.write('=' * 70)

        # Exit with appropriate code (don't exit with error, just return status)
        if failed > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'[WARNING] {failed}/{total} API(s) need configuration'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'[SUCCESS] All {total} APIs validated successfully'))
