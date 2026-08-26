# Integration tests for external API clients
# Run: python manage.py test tests.test_integrations
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from core.models import JobPost, Source
from integrations.github_scraper import GitHubScraper
from integrations.huggingface_client import HuggingFaceClient
from integrations.remoteok_scraper import RemoteOKScraper
from integrations.rss_scraper import RSSJobScraper
from integrations.telegram_client import TelegramClient


class GitHubScraperTest(TestCase):
    # Test GitHub Issues scraper integration

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.GITHUB_ISSUE,
            identifier='github_search',
            is_active=True,
        )

    @patch('requests.Session.get')
    def test_search_issues(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'id': 12345,
                    'title': 'Need Python Django Developer',
                    'body': 'Looking for a contract Django developer for web application',
                    'repository_url': 'https://api.github.com/repos/example/project',
                    'labels': [{'name': 'python'}, {'name': 'django'}],
                    'html_url': 'https://github.com/example/project/issues/1',
                    'created_at': '2025-01-01T00:00:00Z',
                    'user': {'login': 'client1'},
                }
            ]
        }
        mock_get.return_value = mock_response

        scraper = GitHubScraper()
        jobs = scraper.search_issues(keywords=['paid'], limit=1)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['title'], 'Need Python Django Developer')
        self.assertEqual(jobs[0]['id'], 'github_12345')
        self.assertIn('django', jobs[0]['skills_tags'])


class RSSJobScraperTest(TestCase):
    # Test RSS Feed scraper integration

    @patch('requests.Session.get')
    @patch('feedparser.parse')
    def test_scrape_listings(self, mock_feedparser, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<rss></rss>'
        mock_get.return_value = mock_response

        mock_entry = {
            'title': 'Senior Python Engineer',
            'link': 'https://example.com/job/1',
            'summary': '<p>We need a Python and Django developer for full-time remote role.</p>',
            'published_parsed': (2025, 1, 1, 12, 0, 0, 2, 1, 0),
            'id': 'job_1',
            'tags': [{'term': 'Acme Inc'}, {'term': 'python'}, {'term': 'django'}],
        }
        mock_feedparser.return_value = MagicMock(entries=[mock_entry])

        scraper = RSSJobScraper(feed_url='https://example.com/feed.rss', board_name='test_feed')
        jobs = scraper.scrape_listings(limit=5, keywords=['python'])

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['title'], 'Senior Python Engineer')
        self.assertEqual(jobs[0]['location'], 'Remote')


class RemoteOKScraperTest(TestCase):
    # Test RemoteOK scraper integration

    @patch('requests.Session.get')
    def test_scrape_listings(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'legal': 'metadata'},
            {
                'id': '99999',
                'position': 'Backend Django Developer',
                'company': 'Tech Corp',
                'location': 'Remote',
                'tags': ['python', 'django', 'postgresql'],
                'description': '<p>Awesome Django role</p>',
                'slug': 'backend-django-developer',
                'apply_url': 'https://techcorp.com/apply',
                'date': '2025-01-01T00:00:00Z',
            },
        ]
        mock_get.return_value = mock_response

        scraper = RemoteOKScraper()
        jobs = scraper.scrape_listings(limit=5, keywords=['python'])

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['title'], 'Backend Django Developer')
        self.assertEqual(jobs[0]['company_name'], 'Tech Corp')


class HuggingFaceClientTest(TestCase):
    # Test Hugging Face AI client integration

    @patch('integrations.huggingface_client.validate_huggingface_credentials')
    @patch('integrations.huggingface_client.InferenceClient')
    def test_query(self, mock_client_cls, mock_validate):
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = 'IS_JOB_SIGNAL: YES\nCONFIDENCE: 90\nREASONING: Legitimate posting'
        mock_response = MagicMock(choices=[mock_choice])
        mock_client.chat_completion.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch.object(settings, 'HUGGINGFACE_API_KEY', 'hf_test_key'):
            client = HuggingFaceClient()
            result = client.query('Test prompt')

        self.assertIn('IS_JOB_SIGNAL: YES', result)

    @patch('integrations.huggingface_client.validate_huggingface_credentials')
    @patch('integrations.huggingface_client.InferenceClient')
    def test_test_connection(self, mock_client_cls, mock_validate):
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = 'Connection successful'
        mock_response = MagicMock(choices=[mock_choice])
        mock_client.chat_completion.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with patch.object(settings, 'HUGGINGFACE_API_KEY', 'hf_test_key'):
            client = HuggingFaceClient()
            self.assertTrue(client.test_connection())

    @patch('integrations.huggingface_client.validate_huggingface_credentials')
    @patch('integrations.huggingface_client.InferenceClient')
    def test_analyze_job_relevance(self, mock_client_cls, mock_validate):
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = 'RELEVANT: YES\nCONFIDENCE: 85\nREASON: Matches Python stack'
        mock_response = MagicMock(choices=[mock_choice])
        mock_client.chat_completion.return_value = mock_response
        mock_client_cls.return_value = mock_client

        job = JobPost(
            title='Django Backend Developer',
            body='Python and Django expertise required',
            author='recruiter',
        )

        with patch.object(settings, 'HUGGINGFACE_API_KEY', 'hf_test_key'):
            client = HuggingFaceClient()
            analysis = client.analyze_job_relevance(job)

        self.assertTrue(analysis['is_relevant'])
        self.assertAlmostEqual(analysis['confidence'], 0.85)

    @patch('integrations.huggingface_client.validate_huggingface_credentials')
    @patch('integrations.huggingface_client.InferenceClient')
    def test_generate_draft_message(self, mock_client_cls, mock_validate):
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = 'Hello, I would love to work on this Django project.'
        mock_response = MagicMock(choices=[mock_choice])
        mock_client.chat_completion.return_value = mock_response
        mock_client_cls.return_value = mock_client

        job = JobPost(
            title='Django Backend Developer',
            body='Python and Django expertise required',
            author='recruiter',
        )

        with patch.object(settings, 'HUGGINGFACE_API_KEY', 'hf_test_key'):
            client = HuggingFaceClient()
            draft = client.generate_draft_message(job, {'skills': 'Python, Django'})

        self.assertIn('Django project', draft)


class WeWorkRemotelyScraperTest(TestCase):
    # Test We Work Remotely scraper integration

    @patch('integrations.base_scraper.BaseScraper.fetch_html')
    def test_scrape_listings(self, mock_fetch):
        from bs4 import BeautifulSoup
        from integrations.weworkremotely_scraper import WeWorkRemotelyScraper

        html_content = '''
        <ul>
            <li class="feature">
                <a href="/remote-jobs/123-django-developer">
                    <span class="company">Remote Corp</span>
                    <span class="title">Senior Django Dev</span>
                    <span class="region">USA Only</span>
                </a>
            </li>
        </ul>
        '''
        mock_fetch.return_value = BeautifulSoup(html_content, 'html.parser')

        scraper = WeWorkRemotelyScraper()
        with patch.object(scraper, 'scrape_job_detail') as mock_detail:
            mock_detail.return_value = {
                'body': 'Looking for Python and Django engineer',
                'skills_tags': 'python,django',
                'timestamp': timezone.now(),
            }
            jobs = scraper.scrape_listings(limit=1)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['title'], 'Senior Django Dev')
        self.assertEqual(jobs[0]['company_name'], 'Remote Corp')
        self.assertIn('django', jobs[0]['skills_tags'])


class TelegramClientTest(TestCase):
    # Test Telegram Bot API integration

    def setUp(self):
        self.source = Source.objects.create(
            type=Source.GITHUB_ISSUE,
            identifier='test',
            is_active=True,
        )
        self.job = JobPost.objects.create(
            source=self.source,
            external_id='test_telegram_001',
            title='Test Job',
            body='Test body',
            author='testuser',
            url='https://example.com',
            timestamp=timezone.now(),
        )

    @patch('integrations.telegram_client.validate_telegram_credentials')
    @patch('integrations.telegram_client.Bot')
    def test_send_alert(self, mock_bot_cls, mock_validate):
        mock_bot = MagicMock()
        mock_result = MagicMock(message_id=42)

        async def fake_send_message(*args, **kwargs):
            return mock_result

        mock_bot.send_message = fake_send_message
        mock_bot_cls.return_value = mock_bot

        with patch.object(settings, 'TELEGRAM_BOT_TOKEN', '123456:fake_token'), \
             patch.object(settings, 'TELEGRAM_CHAT_ID', '12345678'):
            client = TelegramClient()
            msg_id = client.send_simple_alert(self.job)

        self.assertEqual(msg_id, 42)
