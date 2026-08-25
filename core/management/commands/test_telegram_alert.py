"""
Test Telegram integration by sending a test alert

Usage: python manage.py test_telegram_alert
"""
from django.core.management.base import BaseCommand
from integrations.telegram_client import TelegramClient
from core.models import JobPost, Source
from datetime import datetime


class Command(BaseCommand):
    help = 'Send a test Telegram alert to verify bot configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Telegram bot integration...'))

        try:
            client = TelegramClient()

            # Create test job (not persisted to DB)
            test_source = Source(type=Source.GITHUB_ISSUE, identifier='test')
            test_job = JobPost(
                source=test_source,
                title='Test Job: Python Developer Needed',
                body='This is a test job posting to verify Telegram integration.',
                author='TestBot',
                url='https://example.com',
                timestamp=datetime.now()
            )

            message_id = client.send_simple_alert(test_job)

            self.stdout.write(self.style.SUCCESS(f'\n✅ Test alert sent! Message ID: {message_id}'))
            self.stdout.write('Check your Telegram app to verify.')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            self.stdout.write(self.style.WARNING('\nTroubleshooting:'))
            self.stdout.write('  • Verify TELEGRAM_BOT_TOKEN in .env')
            self.stdout.write('  • Verify TELEGRAM_CHAT_ID in .env')
            self.stdout.write('  • Ensure you started a chat with your bot')
            self.stdout.write('  • Get chat ID: https://api.telegram.org/bot<TOKEN>/getUpdates')
            raise
