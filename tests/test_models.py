# Unit tests for Django models
from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from core.models import Source, JobPost, QualificationScore, AlertStatus, DraftMessage


class SourceModelTest(TestCase):
    # Test Source model

    def test_create_job_board_source(self):
        # Test creating a Job Board source
        source = Source.objects.create(
            type=Source.JOB_BOARD,
            identifier='remoteok',
            name='RemoteOK',
            scraper_type='beautifulsoup',
            base_url='https://remoteok.com',
            rate_limit_seconds=5,
            is_active=True
        )
        self.assertEqual(source.type, Source.JOB_BOARD)
        self.assertEqual(source.identifier, 'remoteok')
        self.assertTrue(source.is_active)
        self.assertIn('Job Board', str(source))

    def test_create_github_issue_source(self):
        # Test creating a GitHub Issue source
        source = Source.objects.create(
            type=Source.GITHUB_ISSUE,
            identifier='github_search',
            name='GitHub Issues Search',
            scraper_type='api',
            base_url='https://api.github.com',
            is_active=True
        )
        self.assertEqual(source.type, Source.GITHUB_ISSUE)
        self.assertEqual(source.identifier, 'github_search')

    def test_create_rss_feed_source(self):
        # Test creating an RSS Feed source
        source = Source.objects.create(
            type=Source.RSS_FEED,
            identifier='weworkremotely',
            name='We Work Remotely RSS Feed',
            scraper_type='rss',
            base_url='https://weworkremotely.com/categories/remote-programming-jobs.rss',
            is_active=True
        )
        self.assertEqual(source.type, Source.RSS_FEED)
        self.assertEqual(source.identifier, 'weworkremotely')


class JobPostModelTest(TestCase):
    # Test JobPost model

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.JOB_BOARD,
            identifier='remoteok',
            name='RemoteOK',
            is_active=True
        )

    def test_create_job_post(self):
        # Test creating a job post
        job = JobPost.objects.create(
            source=self.source,
            external_id='remoteok_123',
            title='Django Developer Needed',
            company_name='TechCorp',
            job_type='Full-time',
            location='Remote',
            skills_tags='python,django',
            body='We need a senior Django developer',
            author='hiring_manager',
            url='https://remoteok.com/remote-jobs/123',
            application_link='https://remoteok.com/remote-jobs/123',
            timestamp=timezone.now()
        )
        self.assertEqual(job.status, JobPost.NEW)
        self.assertEqual(job.user_status, JobPost.PENDING)
        self.assertEqual(job.title, 'Django Developer Needed')
        self.assertEqual(str(job), 'Django Developer Needed')

    def test_job_post_status_transition(self):
        # Test job post status changes
        job = JobPost.objects.create(
            source=self.source,
            external_id='remoteok_456',
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

        # SENT -> CLOSED
        job.status = JobPost.CLOSED
        job.save()
        self.assertEqual(job.status, JobPost.CLOSED)


class QualificationScoreModelTest(TestCase):
    # Test QualificationScore model

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.JOB_BOARD,
            identifier='remoteok',
            name='RemoteOK',
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
        self.assertIn('High', str(qual))

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


class DraftMessageModelTest(TestCase):
    # Test DraftMessage model

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.GITHUB_ISSUE,
            identifier='github_search',
            name='GitHub Issues Search',
            is_active=True
        )
        self.job = JobPost.objects.create(
            source=self.source,
            external_id='test_draft_001',
            title='Python Bug Fix',
            body='Fix issue in repo',
            author='maintainer',
            url='https://github.com/org/repo/issues/1',
            timestamp=timezone.now()
        )

    def test_create_draft_message(self):
        draft = DraftMessage.objects.create(
            job_post=self.job,
            content='I can help fix this issue.',
            platform=DraftMessage.GITHUB_COMMENT,
            cover_letter=''
        )
        self.assertEqual(draft.platform, DraftMessage.GITHUB_COMMENT)
        self.assertIn('Draft for:', str(draft))


class AlertStatusModelTest(TestCase):
    # Test AlertStatus model

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.JOB_BOARD,
            identifier='remoteok',
            name='RemoteOK',
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
        self.assertIn('Alert for:', str(alert))
