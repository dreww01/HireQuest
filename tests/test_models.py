# Unit tests for Django models
# Run: python manage.py test tests.test_models
from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from core.models import Source, JobPost, QualificationScore, AlertStatus, DraftMessage


class SourceModelTest(TestCase):
    # Test Source model

    def test_create_reddit_source(self):
        # Test creating a Reddit source
        source = Source.objects.create(
            type=Source.REDDIT,
            identifier='forhire',
            name='ForHire Subreddit',
            is_active=True
        )
        self.assertEqual(source.type, Source.REDDIT)
        self.assertEqual(source.identifier, 'forhire')
        self.assertTrue(source.is_active)

    def test_create_newsletter_source(self):
        # Test creating a newsletter source
        source = Source.objects.create(
            type=Source.NEWSLETTER,
            identifier='noreply@job-board.com',
            name='Job Board Newsletter',
            is_active=True
        )
        self.assertEqual(source.type, Source.NEWSLETTER)


class JobPostModelTest(TestCase):
    # Test JobPost model

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.REDDIT,
            identifier='forhire',
            is_active=True
        )

    def test_create_job_post(self):
        # Test creating a job post
        job = JobPost.objects.create(
            source=self.source,
            external_id='reddit_123',
            title='Django Developer Needed',
            body='We need a Django developer',
            author='hiring_manager',
            url='https://reddit.com/r/forhire/123',
            timestamp=timezone.now()
        )
        self.assertEqual(job.status, JobPost.NEW)
        self.assertEqual(job.title, 'Django Developer Needed')

    def test_job_post_status_transition(self):
        # Test job post status changes
        job = JobPost.objects.create(
            source=self.source,
            external_id='reddit_456',
            title='Test Job',
            body='Test',
            author='test',
            url='https://example.com',
            timestamp=timezone.now()
        )

        # NEW -> ALERTED
        job.status = JobPost.ALERTED
        job.save()
        self.assertEqual(job.status, JobPost.ALERTED)

        # ALERTED -> SENT
        job.status = JobPost.SENT
        job.save()
        self.assertEqual(job.status, JobPost.SENT)


class QualificationScoreModelTest(TestCase):
    # Test QualificationScore model

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.REDDIT,
            identifier='forhire',
            is_active=True
        )
        self.job = JobPost.objects.create(
            source=self.source,
            external_id='test_qual_001',
            title='Test Job',
            body='Test',
            author='test',
            url='https://example.com',
            timestamp=timezone.now()
        )

    def test_create_high_qualification(self):
        # Test creating HIGH quality qualification
        qual = QualificationScore.objects.create(
            job_post=self.job,
            is_job_signal=True,
            confidence=0.95,
            classification=QualificationScore.HIGH,
            reasoning='Strong technical match'
        )
        self.assertEqual(qual.classification, QualificationScore.HIGH)
        self.assertEqual(qual.confidence, 0.95)
        self.assertTrue(qual.is_job_signal)

    def test_create_ignore_qualification(self):
        # Test creating IGNORE quality qualification
        qual = QualificationScore.objects.create(
            job_post=self.job,
            is_job_signal=False,
            confidence=0.30,
            classification=QualificationScore.IGNORE,
            reasoning='Not a match'
        )
        self.assertEqual(qual.classification, QualificationScore.IGNORE)


class AlertStatusModelTest(TestCase):
    # Test AlertStatus model

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.REDDIT,
            identifier='forhire',
            is_active=True
        )
        self.job = JobPost.objects.create(
            source=self.source,
            external_id='test_alert_001',
            title='Test Job',
            body='Test',
            author='test',
            url='https://example.com',
            timestamp=timezone.now()
        )

    def test_create_alert(self):
        # Test creating an alert
        alert = AlertStatus.objects.create(
            job_post=self.job,
            telegram_message_id='12345',
            acknowledged=False
        )
        self.assertEqual(alert.telegram_message_id, '12345')
        self.assertEqual(alert.job_post, self.job)
        self.assertFalse(alert.acknowledged)
