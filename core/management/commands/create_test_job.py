"""
Management command to create a test job post and run the complete AI pipeline
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Source, JobPost
from utils.ai_service import detect_job_signal, qualify_job, generate_draft_message
from integrations.telegram_client import TelegramClient
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create a test job post and run it through the complete AI pipeline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-type',
            type=str,
            default='newsletter',
            choices=['newsletter', 'reddit'],
            help='Type of source to use (newsletter or reddit)'
        )
        parser.add_argument(
            '--skip-telegram',
            action='store_true',
            help='Skip sending Telegram alert'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('CREATE TEST JOB POST & RUN AI PIPELINE'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        source_type = options['source_type']

        # Get or create a test source
        if source_type == 'newsletter':
            source, created = Source.objects.get_or_create(
                type=Source.RSS_FEED,
                identifier='noreply@linkedin.com',
                defaults={
                    'name': 'LinkedIn Jobs (Test)',
                    'is_active': True
                }
            )
        else:
            source, created = Source.objects.get_or_create(
                type=Source.GITHUB_ISSUE,
                identifier='forhire',
                defaults={
                    'name': 'r/forhire (Test)',
                    'is_active': True
                }
            )

        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created test source: {source.name}'))
        else:
            self.stdout.write(f'[*] Using existing source: {source.name}')

        # Sample job posts with different qualities
        sample_jobs = [
            {
                'title': '[Hiring] Python/Django Developer for E-commerce Platform - $80-100/hr',
                'body': '''We are a fast-growing e-commerce company looking for an experienced Python/Django developer.

Requirements:
- 5+ years Python experience
- Strong Django knowledge
- PostgreSQL and Redis experience
- REST API development
- AWS deployment experience
- Good communication skills

Project Details:
- Build new features for our e-commerce platform
- Integrate payment gateways (Stripe, PayPal)
- Optimize database queries
- Write comprehensive tests

Budget: $80-100/hour
Duration: 3-6 months (potential for extension)
Start: Immediately
Work: 100% remote

Please respond with:
1. Your relevant experience
2. Portfolio/GitHub
3. Availability

Looking forward to working with you!''',
                'author': 'tech_recruiter_99',
                'url': 'https://example.com/job/12345',
                'expected_classification': 'high'
            },
            {
                'title': 'Need help with a small Python script',
                'body': '''Hi, I need someone to write a Python script that scrapes a website.
Budget is $20. Should be quick work.
Let me know if interested.''',
                'author': 'random_user',
                'url': 'https://example.com/job/67890',
                'expected_classification': 'medium'
            },
            {
                'title': 'Check out my new crypto platform!!!',
                'body': '''Join our revolutionary crypto trading platform!
Make $10,000 per day with our AI trading bot!
Limited spots available! Sign up now!''',
                'author': 'crypto_spam_bot',
                'url': 'https://example.com/spam',
                'expected_classification': 'ignore'
            }
        ]

        # Let user choose which job to create
        self.stdout.write(self.style.WARNING('\n[!] Select a test job to create:\n'))
        for i, job in enumerate(sample_jobs, 1):
            self.stdout.write(f'{i}. {job["title"]}')
            self.stdout.write(f'   Expected: {job["expected_classification"].upper()}')
            self.stdout.write('')

        choice = input('Enter choice (1-3) or press Enter for option 1: ').strip()

        if not choice:
            choice = '1'

        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(sample_jobs):
                self.stdout.write(self.style.ERROR('Invalid choice, using option 1'))
                choice_idx = 0
        except ValueError:
            self.stdout.write(self.style.ERROR('Invalid choice, using option 1'))
            choice_idx = 0

        selected_job = sample_jobs[choice_idx]

        # Create the job post
        self.stdout.write(self.style.SUCCESS('\n\n[STEP 1] Creating test job post'))
        self.stdout.write(self.style.SUCCESS('-' * 70))

        import uuid
        external_id = f'test_{source_type}_{uuid.uuid4().hex[:8]}'

        job_post = JobPost.objects.create(
            source=source,
            external_id=external_id,
            title=selected_job['title'],
            body=selected_job['body'],
            author=selected_job['author'],
            url=selected_job['url'],
            timestamp=timezone.now(),
            status='new'
        )

        self.stdout.write(self.style.SUCCESS(f'[OK] Created job post:'))
        self.stdout.write(f'   ID: {job_post.id}')
        self.stdout.write(f'   Title: {job_post.title}')
        self.stdout.write(f'   Source: {job_post.source.name}')
        self.stdout.write(f'   Expected Classification: {selected_job["expected_classification"].upper()}')

        # Step 2: Signal Detection
        self.stdout.write(self.style.SUCCESS('\n\n[STEP 2] Running AI Signal Detection'))
        self.stdout.write(self.style.SUCCESS('-' * 70))

        try:
            is_signal, confidence, reasoning = detect_job_signal(job_post)

            self.stdout.write(f'\n   Is Job Signal: {is_signal}')
            self.stdout.write(f'   Confidence: {confidence:.1%}')
            self.stdout.write(f'   Reasoning: {reasoning}')

            if is_signal:
                self.stdout.write(self.style.SUCCESS('\n[OK] Job signal detected!'))
            else:
                self.stdout.write(self.style.WARNING('\n[!] Not a job signal - pipeline will stop here'))
                self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
                return

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n[ERROR] Error in signal detection: {str(e)}'))
            import traceback
            traceback.print_exc()
            return

        # Step 3: Job Qualification
        self.stdout.write(self.style.SUCCESS('\n\n[STEP 3] Running AI Job Qualification'))
        self.stdout.write(self.style.SUCCESS('-' * 70))

        try:
            qualification = qualify_job(job_post)

            self.stdout.write(f'\n   Classification: {qualification.get_classification_display().upper()}')
            self.stdout.write(f'   Confidence: {qualification.confidence:.1%}')
            self.stdout.write(f'   Reasoning: {qualification.reasoning}')

            expected = selected_job['expected_classification']
            if qualification.classification == expected:
                self.stdout.write(self.style.SUCCESS(f'\n[OK] Classification matches expected ({expected.upper()})!'))
            else:
                self.stdout.write(self.style.WARNING(
                    f'\n[!] Classification mismatch: got {qualification.classification.upper()}, '
                    f'expected {expected.upper()}'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n[ERROR] Error in qualification: {str(e)}'))
            import traceback
            traceback.print_exc()
            return

        # Step 4: Draft Generation
        if qualification.classification in ['high', 'medium']:
            self.stdout.write(self.style.SUCCESS('\n\n[STEP 4] Generating Draft Message'))
            self.stdout.write(self.style.SUCCESS('-' * 70))

            try:
                draft = generate_draft_message(job_post, qualification)

                self.stdout.write(f'\n   Platform: {draft.get_platform_display()}')
                self.stdout.write(f'\n   Draft:\n')
                self.stdout.write(self.style.WARNING('-' * 70))
                self.stdout.write(draft.content)
                self.stdout.write(self.style.WARNING('-' * 70))

                self.stdout.write(self.style.SUCCESS('\n[OK] Draft generated successfully!'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n[ERROR] Error generating draft: {str(e)}'))
                import traceback
                traceback.print_exc()
                draft = None
        else:
            self.stdout.write(self.style.WARNING('\n\n[SKIP] STEP 4: Draft generation skipped (low quality job)'))
            draft = None

        # Step 5: Telegram Alert
        if qualification.classification == 'high' and not options['skip_telegram']:
            self.stdout.write(self.style.SUCCESS('\n\n[STEP 5] Sending Telegram Alert'))
            self.stdout.write(self.style.SUCCESS('-' * 70))

            try:
                telegram = TelegramClient()
                message_id = telegram.send_job_alert(job_post, qualification, draft)

                job_post.status = 'alerted'
                job_post.save()

                self.stdout.write(self.style.SUCCESS(f'\n[OK] Telegram alert sent! (Message ID: {message_id})'))
                self.stdout.write(self.style.SUCCESS('   Check your Telegram app!'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n[ERROR] Error sending Telegram alert: {str(e)}'))
                self.stdout.write(self.style.WARNING('   Note: This is expected if Telegram credentials are not configured'))
                import traceback
                traceback.print_exc()
        else:
            if options['skip_telegram']:
                self.stdout.write(self.style.WARNING('\n\n[SKIP] STEP 5: Telegram alert skipped (--skip-telegram flag)'))
            else:
                self.stdout.write(self.style.WARNING('\n\n[SKIP] STEP 5: Telegram alert skipped (not high priority)'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n\n[SUCCESS] PIPELINE COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'\n[OK] Test Results:')
        self.stdout.write(f'   Job Post ID: {job_post.id}')
        self.stdout.write(f'   Job Signal: {is_signal}')
        self.stdout.write(f'   Classification: {qualification.classification.upper()}')
        self.stdout.write(f'   Draft Created: {"Yes" if draft else "No"}')
        self.stdout.write(f'   Telegram Sent: {"Yes" if job_post.status == "alerted" else "No"}')

        self.stdout.write(self.style.SUCCESS('\n[INFO] View in admin panel:'))
        self.stdout.write(f'   http://localhost:8000/admin/core/jobpost/{job_post.id}/change/')

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
