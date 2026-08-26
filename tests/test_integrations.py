# Integration tests for external API clients
# Run: python manage.py test tests.test_integrations
import os
from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, MagicMock
from datetime import datetime

from integrations.reddit_client import RedditClient
from integrations.email_client import EmailClient
from integrations.huggingface_client import HuggingFaceClient
from integrations.telegram_client import TelegramClient
from core.models import JobPost, Source


class RedditClientTest(TestCase):
    # Test Reddit API integration

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.REDDIT,
            identifier='forhire',
            is_active=True
        )

    @patch('praw.Reddit')
    def test_reddit_connection(self, mock_reddit):
        # Test Reddit client can connect and fetch posts
        # Mock PRAW response
        mock_submission = MagicMock()
        mock_submission.id = 'test123'
        mock_submission.title = 'Test Job Post'
        mock_submission.selftext = 'Job description'
        mock_submission.author.name = 'testuser'
        mock_submission.url = 'https://reddit.com/test'
        mock_submission.created_utc = datetime.now().timestamp()

        mock_subreddit = MagicMock()
        mock_subreddit.new.return_value = [mock_submission]
        mock_reddit.return_value.subreddit.return_value = mock_subreddit

        client = RedditClient()
        posts = client.fetch_recent_posts('forhire', limit=1)

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['title'], 'Test Job Post')
        self.assertEqual(posts[0]['id'], 'test123')


class EmailClientTest(TestCase):
    # Test Email IMAP integration

    @patch('imaplib.IMAP4_SSL')
    def test_email_connection(self, mock_imap):
        # Test email client can connect to IMAP server
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.select.return_value = ('OK', [b'1'])
        mock_mail.search.return_value = ('OK', [b''])

        client = EmailClient()
        emails = client.fetch_recent_emails(limit=1)

        self.assertIsInstance(emails, list)
        mock_mail.login.assert_called_once()


class HuggingFaceClientTest(TestCase):
    # Test HuggingFace AI API integration

    @patch('requests.post')
    def test_huggingface_connection(self, mock_post):
        # Test HuggingFace API can classify job quality
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'generated_text': 'Classification: HIGH\nConfidence: 0.95\nReasoning: Test reasoning'
        }]
        mock_post.return_value = mock_response

        client = HuggingFaceClient()
        result = client.classify_job_quality('Test job post', 'Test description')

        self.assertIn('classification', result)
        self.assertIn('confidence', result)


class TelegramClientTest(TestCase):
    # Test Telegram Bot API integration

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.REDDIT,
            identifier='test',
            is_active=True
        )
        self.job = JobPost.objects.create(
            source=self.source,
            external_id='test_telegram_001',
            title='Test Job',
            body='Test body',
            author='testuser',
            url='https://example.com',
            timestamp=datetime.now()
        )

    @patch('requests.post')
    def test_telegram_send_message(self, mock_post):
        # Test Telegram bot can send alerts
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True, 'result': {'message_id': 123}}
        mock_post.return_value = mock_response

        client = TelegramClient()
        message_id = client.send_simple_alert(self.job)

        self.assertEqual(message_id, 123)
        mock_post.assert_called_once()
