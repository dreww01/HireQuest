"""
Test email polling with a sample job email

Interactive test that guides you through sending a test email
and verifies the full email polling pipeline works.

Usage: python manage.py test_email_with_sample
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from integrations.email_client import EmailClient
from core.models import Source, JobPost
from jobs.email_poller import EmailPollerJob
import time


class Command(BaseCommand):
    help = 'Interactive email polling test with sample job email'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('EMAIL POLLING TEST WITH SAMPLE EMAIL'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Check email configuration
        email_address = getattr(settings, 'EMAIL_ADDRESS', None)

        if not email_address:
            self.stdout.write(self.style.ERROR('❌ EMAIL_ADDRESS not configured in .env'))
            return

        self.stdout.write(self.style.WARNING('\n📧 STEP 1: Send yourself a test job email'))
        self.stdout.write(self.style.WARNING('-' * 70))
        self.stdout.write(f'\nFrom: Any email account (Gmail, Yahoo, etc.)')
        self.stdout.write(f'To: {email_address}')
        self.stdout.write(f'\nSubject: Python Developer Needed - Remote Work')
        self.stdout.write(f'\nBody:')
        self.stdout.write(self.style.WARNING('''
Hi there,

We're looking for a Python developer to help with a Django project.

Requirements:
- 3+ years Python experience
- Django framework knowledge
- REST API development
- Good communication skills

Budget: $75/hour
Timeline: Start immediately
Duration: 3-month project

If interested, please reply with your portfolio and availability.

Thanks!
John Smith
Tech Startup Inc.
'''))

        self.stdout.write(self.style.WARNING('\n' + '=' * 70))

        # Ask user if they've sent the email
        response = input('\n✅ Have you sent the test email? (yes/no): ')

        if response.lower() not in ['yes', 'y']:
            self.stdout.write(self.style.WARNING('\n⏸️  Test paused. Send the email and run this command again.'))
            return

        # Wait for email to arrive
        self.stdout.write(self.style.WARNING('\n⏳ Waiting 5 seconds for email to arrive...'))
        time.sleep(5)

        self.stdout.write(self.style.SUCCESS('\n\n📥 STEP 2: Fetching emails from inbox'))
        self.stdout.write(self.style.SUCCESS('-' * 70))

        # Test email connection
        try:
            client = EmailClient()
            emails = client.fetch_recent_emails(limit=5)

            if not emails:
                self.stdout.write(self.style.WARNING('⚠️  No unread emails found'))
                self.stdout.write(self.style.WARNING('\nPossible reasons:'))
                self.stdout.write('  1. Email hasn\'t arrived yet (wait a minute and try again)')
                self.stdout.write('  2. Email was already marked as read')
                self.stdout.write('  3. Email went to spam folder')
                return

            self.stdout.write(self.style.SUCCESS(f'\n✅ Found {len(emails)} unread email(s):\n'))

            for i, email_data in enumerate(emails, 1):
                self.stdout.write(f'{i}. Subject: {email_data["subject"]}')
                self.stdout.write(f'   From: {email_data["from"]}')
                self.stdout.write(f'   Date: {email_data["date"]}')
                self.stdout.write(f'   Body preview: {email_data["body"][:100]}...\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error fetching emails: {str(e)}'))
            return

        self.stdout.write(self.style.SUCCESS('\n\n🔍 STEP 3: Testing full email polling pipeline'))
        self.stdout.write(self.style.SUCCESS('-' * 70))

        # Check if we have newsletter sources
        sources = Source.objects.filter(type=Source.NEWSLETTER, is_active=True)

        if not sources.exists():
            self.stdout.write(self.style.WARNING('\n⚠️  No newsletter sources configured!'))
            self.stdout.write(self.style.WARNING('Creating a test source for your email sender...'))

            # Create a generic test source
            test_source = Source.objects.create(
                type=Source.NEWSLETTER,
                identifier='test',
                name='Test Newsletter Source',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created test source: {test_source.name}'))

        # Show active sources
        self.stdout.write(f'\n📋 Active newsletter sources ({sources.count()}):')
        for source in sources:
            self.stdout.write(f'  - {source.name} ({source.identifier})')

        # Count current job posts
        initial_count = JobPost.objects.count()
        self.stdout.write(f'\n📊 Current job posts in database: {initial_count}')

        # Run the email poller
        self.stdout.write(self.style.WARNING('\n🤖 Running email poller...'))

        try:
            EmailPollerJob.poll()

            # Check if new posts were created
            new_count = JobPost.objects.count()
            created_count = new_count - initial_count

            self.stdout.write(self.style.SUCCESS(f'\n✅ Email polling complete!'))
            self.stdout.write(f'  - Job posts created: {created_count}')
            self.stdout.write(f'  - Total job posts: {new_count}')

            if created_count > 0:
                self.stdout.write(self.style.SUCCESS('\n\n🎉 SUCCESS! Email flow is working!'))

                # Show the created posts
                latest_posts = JobPost.objects.order_by('-created_at')[:created_count]
                self.stdout.write(self.style.SUCCESS('\n📝 Created job posts:'))
                for post in latest_posts:
                    self.stdout.write(f'\n  Title: {post.title}')
                    self.stdout.write(f'  Source: {post.source.name}')
                    self.stdout.write(f'  Status: {post.status}')
                    self.stdout.write(f'  Created: {post.created_at}')

                self.stdout.write(self.style.SUCCESS('\n\n✅ Next steps:'))
                self.stdout.write('  1. Check the admin panel to see the job post')
                self.stdout.write('  2. Run: python manage.py poll_and_alert')
                self.stdout.write('  3. This will trigger AI qualification and Telegram alerts')

            else:
                self.stdout.write(self.style.WARNING('\n⚠️  No new job posts created'))
                self.stdout.write(self.style.WARNING('\nPossible reasons:'))
                self.stdout.write('  1. Email sender doesn\'t match any newsletter source')
                self.stdout.write('  2. Email was already processed (deduplication)')
                self.stdout.write('\nTo fix: Run python manage.py setup_newsletter_sources')
                self.stdout.write('        and add a source matching your test email sender')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error during polling: {str(e)}'))
            import traceback
            traceback.print_exc()

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
