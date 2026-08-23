# Tests for signal detection and AI qualification
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from core.models import Source, JobPost, QualificationScore, DraftMessage
from utils.signal_detection import SignalDetector
from utils.ai_service import detect_job_signal, qualify_job, generate_draft_message


class TestSignalDetector(TestCase):
    # Test suite for SignalDetector

    def setUp(self):
        self.detector = SignalDetector()

    def test_is_job_signal_empty(self):
        is_signal, conf = self.detector.is_job_signal("")
        self.assertFalse(is_signal)
        self.assertEqual(conf, 0.0)

    def test_is_job_signal_matching_keywords(self):
        text = "Looking for a Python and Django developer for full-time work."
        is_signal, conf = self.detector.is_job_signal(text)
        self.assertTrue(is_signal)
        self.assertGreater(conf, 0.5)

    def test_classify_job_high(self):
        source = Source.objects.create(type=Source.JOB_BOARD, identifier='test_board')
        job = JobPost.objects.create(
            source=source,
            external_id='test_sd_1',
            title='Senior Django Developer Full-time',
            body='Monthly $5000 budget for experienced developer',
            timestamp=timezone.now()
        )
        classification = self.detector.classify_job(job)
        self.assertEqual(classification, 'high')

    def test_classify_job_medium(self):
        source = Source.objects.create(type=Source.JOB_BOARD, identifier='test_board_2')
        job = JobPost.objects.create(
            source=source,
            external_id='test_sd_2',
            title='Python Script Support',
            body='Automation task using standard tools',
            timestamp=timezone.now()
        )
        classification = self.detector.classify_job(job)
        self.assertEqual(classification, 'medium')


class TestAIService(TestCase):
    # Test suite for utils.ai_service functions

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.GITHUB_ISSUE,
            identifier='github_search',
            name='GitHub Issues Search'
        )
        self.job = JobPost.objects.create(
            source=self.source,
            external_id='test_ai_job_1',
            title='Looking for Django developer for API project',
            body='We need someone experienced with Django, FastAPI, PostgreSQL, and Docker. Budget is $80/hr.',
            timestamp=timezone.now()
        )

    def test_qualify_job_high(self):
        qual = qualify_job(self.job)
        self.assertEqual(qual.classification, 'high')
        self.assertGreaterEqual(qual.confidence, 0.7)

    def test_qualify_job_senior_ignore(self):
        senior_job = JobPost.objects.create(
            source=self.source,
            external_id='test_ai_job_2',
            title='Senior Architect Needed',
            body='Requires senior level experience only',
            timestamp=timezone.now()
        )
        qual = qualify_job(senior_job)
        self.assertEqual(qual.classification, 'ignore')

    @patch('utils.ai_service.HuggingFaceClient')
    def test_generate_draft_message(self, mock_hf_client_class):
        mock_instance = MagicMock()
        mock_instance.query.return_value = 'Generated proposal text'
        mock_hf_client_class.return_value = mock_instance

        qual = QualificationScore.objects.create(
            job_post=self.job,
            is_job_signal=True,
            confidence=0.9,
            classification='high',
            reasoning='Good fit'
        )
        draft = generate_draft_message(self.job, qual)
        self.assertEqual(draft.platform, DraftMessage.GITHUB_COMMENT)
        self.assertEqual(draft.content, 'Generated proposal text')
