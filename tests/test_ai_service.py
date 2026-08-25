# Tests for AI service and signal detection
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from core.models import DraftMessage, JobPost, QualificationScore, Source
from utils.ai_service import detect_job_signal, generate_draft_message, qualify_job


class TestAIService(TestCase):
    # Test suite for AI service functions

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.GITHUB_ISSUE,
            identifier='github_search',
            is_active=True,
        )
        self.job_post = JobPost.objects.create(
            source=self.source,
            external_id='test_ai_job_1',
            title='Django Backend Developer Needed for SaaS',
            body='We need a full-time Django and Python developer with PostgreSQL and Docker experience. Budget is $80/hr.',
            author='recruiter',
            url='https://example.com/job/1',
            timestamp=timezone.now(),
        )

    def test_qualify_job_high(self):
        # Should qualify high score for strong keyword match with budget & django
        qualification = qualify_job(self.job_post)
        self.assertEqual(qualification.classification, QualificationScore.HIGH)
        self.assertTrue(qualification.is_job_signal)
        self.assertGreaterEqual(qualification.confidence, 0.7)

    def test_qualify_job_senior_ignore(self):
        # Should ignore senior level roles
        senior_job = JobPost.objects.create(
            source=self.source,
            external_id='test_senior_job',
            title='Senior Principal Architect',
            body='Looking for a Senior developer with 10+ years experience.',
            author='recruiter',
            url='https://example.com/job/2',
            timestamp=timezone.now(),
        )
        qualification = qualify_job(senior_job)
        self.assertEqual(qualification.classification, QualificationScore.IGNORE)

    def test_qualify_job_spam_ignore(self):
        # Should ignore spam posts
        spam_job = JobPost.objects.create(
            source=self.source,
            external_id='test_spam_job',
            title='Make money fast with pyramid scheme',
            body='Work from home mom get rich quick click here now for multi-level marketing.',
            author='spammer',
            url='https://example.com/spam',
            timestamp=timezone.now(),
        )
        qualification = qualify_job(spam_job)
        self.assertEqual(qualification.classification, QualificationScore.IGNORE)

    @patch('utils.ai_service.HuggingFaceClient')
    def test_detect_job_signal_ai_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.query.return_value = 'IS_JOB_SIGNAL: YES\nCONFIDENCE: 95\nREASONING: Legitimate contract role'
        mock_client_cls.return_value = mock_client

        is_signal, confidence, reasoning = detect_job_signal(self.job_post)
        self.assertTrue(is_signal)
        self.assertAlmostEqual(confidence, 0.95)
        self.assertIn('Legitimate contract role', reasoning)

    def test_detect_job_signal_fallback(self):
        # When HuggingFaceClient fails or is unconfigured, fallback to keyword matching
        is_signal, confidence, reasoning = detect_job_signal(self.job_post)
        self.assertTrue(is_signal)
        self.assertGreater(confidence, 0.0)

    def test_generate_draft_message_fallback(self):
        # Fallback draft generation when HF client is unconfigured
        qual = QualificationScore.objects.create(
            job_post=self.job_post,
            is_job_signal=True,
            confidence=0.85,
            classification=QualificationScore.HIGH,
            reasoning='Good match',
        )
        draft = generate_draft_message(self.job_post, qual)
        self.assertIsNotNone(draft)
        self.assertEqual(draft.job_post, self.job_post)
        self.assertEqual(draft.platform, DraftMessage.GITHUB_COMMENT)
        self.assertIn('Python/Django', draft.content)
