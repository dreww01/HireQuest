from django.core.management.base import BaseCommand
from integrations.reddit_client import RedditClient
from core.models import Source, JobPost, QualificationScore
from utils.signal_detection import SignalDetector
from utils.exceptions import MissingAPIKeyError, InvalidAPIKeyError, APIConnectionError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Poll Reddit, detect signals, and send alerts (end-to-end test)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--subreddit',
            type=str,
            default='forhire',
            help='Subreddit to poll (default: forhire)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of posts to fetch (default: 10)'
        )

    def handle(self, *args, **options):
        subreddit = options['subreddit']
        limit = options['limit']

        self.stdout.write(self.style.SUCCESS(f'Starting end-to-end pipeline for r/{subreddit}...'))

        try:
            # Initialize Reddit client
            try:
                reddit = RedditClient()
            except MissingAPIKeyError as e:
                self.stdout.write(self.style.ERROR('\n❌ REDDIT CONFIGURATION ERROR'))
                self.stdout.write(self.style.ERROR('='*60))
                self.stdout.write(self.style.ERROR(str(e)))
                self.stdout.write(self.style.ERROR('='*60))
                return
            except InvalidAPIKeyError as e:
                self.stdout.write(self.style.ERROR('\n❌ REDDIT AUTHENTICATION ERROR'))
                self.stdout.write(self.style.ERROR('='*60))
                self.stdout.write(self.style.ERROR(str(e)))
                self.stdout.write(self.style.ERROR('='*60))
                return
            except APIConnectionError as e:
                self.stdout.write(self.style.ERROR('\n❌ REDDIT CONNECTION ERROR'))
                self.stdout.write(self.style.ERROR('='*60))
                self.stdout.write(self.style.ERROR(str(e)))
                self.stdout.write(self.style.ERROR('='*60))
                return

            detector = SignalDetector()

            # Get or create source
            source, created = Source.objects.get_or_create(
                type=Source.REDDIT,
                identifier=subreddit,
                defaults={'is_active': True}
            )

            if created:
                self.stdout.write(f"Created source: {source}")

            # Fetch posts
            self.stdout.write(f"\nFetching {limit} posts from r/{subreddit}...")
            posts = reddit.fetch_recent_posts(subreddit, limit=limit)

            total_new = 0
            total_ignored = 0

            for post_data in posts:
                # Create or get job post
                job_post, created = JobPost.objects.get_or_create(
                    external_id=post_data['id'],
                    defaults={
                        'source': source,
                        'title': post_data['title'],
                        'body': post_data['body'],
                        'author': post_data['author'],
                        'url': post_data['url'],
                        'timestamp': post_data['timestamp']
                    }
                )

                if not created:
                    continue

                total_new += 1
                self.stdout.write(f"\n[NEW] {job_post.title[:60]}...")

                # Detect signal
                text = f"{job_post.title} {job_post.body}"
                is_signal, confidence = detector.is_job_signal(text)

                if not is_signal:
                    total_ignored += 1
                    self.stdout.write(self.style.WARNING("  ⏩ No job signal detected, skipping"))
                    continue

                # Classify job
                classification = detector.classify_job(job_post)

                # Create qualification score
                qual = QualificationScore.objects.create(
                    job_post=job_post,
                    is_job_signal=is_signal,
                    confidence=confidence,
                    classification=classification,
                    reasoning=f"Keyword match with {confidence:.0%} confidence"
                )

                self.stdout.write(f"  ✅ Signal detected: {classification.upper()} ({confidence:.0%})")

                # Signal will handle alerting for high classification jobs
                if classification == 'high':
                    self.stdout.write(self.style.SUCCESS(f"  📱 HIGH quality job - signal will handle alert"))
                else:
                    self.stdout.write(f"  ℹ️  Classification '{classification}' - no alert")

            # Summary
            self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
            self.stdout.write(self.style.SUCCESS(f"PIPELINE COMPLETE"))
            self.stdout.write(self.style.SUCCESS(f"{'='*60}"))
            self.stdout.write(f"New posts found: {total_new}")
            self.stdout.write(f"Ignored (no signal): {total_ignored}")
            self.stdout.write(f"Total jobs in database: {JobPost.objects.count()}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError in pipeline: {str(e)}'))
            raise
