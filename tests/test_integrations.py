# Integration tests for external API clients and scrapers
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import datetime

from integrations.github_scraper import GitHubScraper
from integrations.rss_scraper import RSSJobScraper
from integrations.remoteok_scraper import RemoteOKScraper
from integrations.weworkremotely_scraper import WeWorkRemotelyScraper
from integrations.huggingface_client import HuggingFaceClient
from integrations.telegram_client import TelegramClient
from core.models import JobPost, Source


class GitHubScraperTest(TestCase):
    # Test GitHub Issues scraper

    @patch('requests.Session.get')
    def test_search_issues(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'id': 101,
                    'title': 'Paid Django bug fix opportunity',
                    'body': 'Looking for a Django developer. Budget $500.',
                    'html_url': 'https://github.com/org/repo/issues/1',
                    'created_at': '2026-01-01T00:00:00Z',
                    'user': {'login': 'testdev'},
                    'labels': [{'name': 'help wanted'}, {'name': 'python'}],
                    'repository_url': 'https://api.github.com/repos/org/repo',
                }
            ]
        }
        mock_get.return_value = mock_response

        scraper = GitHubScraper(github_token=None)
        results = scraper.search_issues(keywords=['paid'], limit=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 'github_101')
        self.assertIn('Django', results[0]['title'])


class RSSJobScraperTest(TestCase):
    # Test RSS scraper

    @patch('requests.Session.get')
    @patch('feedparser.parse')
    def test_scrape_listings(self, mock_parse, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<rss></rss>'
        mock_get.return_value = mock_response

        mock_parse.return_value = MagicMock(
            bozo=0,
            entries=[
                {
                    'id': 'https://remoteok.com/remote-jobs/101',
                    'link': 'https://remoteok.com/remote-jobs/101',
                    'title': 'Remote Python Developer at TechCorp',
                    'summary': 'We need a remote Python/Django engineer.',
                    'published_parsed': (2026, 1, 1, 0, 0, 0, 3, 1, 0),
                    'tags': [{'term': 'python'}, {'term': 'django'}],
                }
            ]
        )

        scraper = RSSJobScraper(feed_url='https://remoteok.com/remote-jobs.rss', board_name='remoteok')
        results = scraper.scrape_listings(limit=1, keywords=['python'])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Remote Python Developer at TechCorp')


class HuggingFaceClientTest(TestCase):
    # Test HuggingFace AI API integration

    @patch.object(HuggingFaceClient, '__init__', lambda self: None)
    def test_huggingface_query(self):
        client = HuggingFaceClient()
        client.client = MagicMock()
        client.model = 'meta-llama/Llama-3.2-1B-Instruct'
        mock_choice = MagicMock()
        mock_choice.message.content = 'IS_JOB_SIGNAL: YES\nCONFIDENCE: 95\nREASONING: Legitimate Django post'
        client.client.chat_completion.return_value = MagicMock(choices=[mock_choice])

        response = client.query('Analyze this job')
        self.assertIn('IS_JOB_SIGNAL: YES', response)


class TelegramClientTest(TestCase):
    # Test Telegram Bot API integration

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.JOB_BOARD,
            identifier='remoteok',
            is_active=True
        )
        self.job = JobPost.objects.create(
            source=self.source,
            external_id='test_telegram_001',
            title='Test Job',
            body='Test body',
            author='testuser',
            url='https://example.com',
            timestamp=timezone.now()
        )

    @patch.object(TelegramClient, '__init__', lambda self: None)
    def test_telegram_escape_markdown(self):
        client = TelegramClient()
        escaped = client._escape_markdown('Test_message*with[markdown]')
        self.assertIn('\\_', escaped)
        self.assertIn('\\*', escaped)
        self.assertIn('\\[', escaped)
