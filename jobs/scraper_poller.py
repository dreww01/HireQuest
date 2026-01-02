# Job scraper poller for all web scrapers

import logging
from datetime import datetime

from django.conf import settings

from core.models import Source, JobPost
from integrations.github_scraper import GitHubScraper
from integrations.rss_scraper import RSSJobScraper
from integrations.remoteok_scraper import RemoteOKScraper
# from integrations.weworkremotely_scraper import WeWorkRemotelyScraper  # Disabled: use RSS instead
from utils.ai_service import detect_job_signal, qualify_job, generate_draft_message
from utils.exceptions import APIConnectionError, MissingAPIKeyError
from utils.validators import check_optional_service

logger = logging.getLogger(__name__)


class ScraperPollerJob:
    # Polls all configured job scrapers and processes results

    @staticmethod
    def poll_github(limit=20):
        # Poll GitHub Issues for job opportunities
        logger.info("Starting GitHub Issues scraping...")

        # Check if GitHub scraping is enabled
        if not getattr(settings, 'GITHUB_SCRAPING_ENABLED', True):
            logger.info("GitHub scraping is disabled in settings")
            return

        github_token = getattr(settings, 'GITHUB_TOKEN', '')
        if not check_optional_service('GitHub', {'GITHUB_TOKEN': github_token}):
            logger.warning("Skipping GitHub scraping (not configured)")
            return

        try:
            source, _ = Source.objects.get_or_create(
                type=Source.GITHUB_ISSUE,
                identifier='github_search',
                defaults={
                    'name': 'GitHub Issues Search',
                    'scraper_type': 'api',
                    'base_url': 'https://api.github.com',
                    'is_active': True,
                }
            )

            if not source.is_active:
                logger.info("GitHub source is inactive, skipping")
                return

            scraper = GitHubScraper(github_token=github_token)
            job_keywords = getattr(settings, 'JOB_KEYWORDS', 'python,django,wordpress').split(',')
            job_keywords = [kw.strip() for kw in job_keywords]
            jobs = scraper.search_issues(keywords=['paid', 'contract'], max_age_days=14, limit=limit)

            new_count = 0
            high_count = 0

            for job_data in jobs:
                job_post, created = JobPost.objects.get_or_create(
                    external_id=job_data['id'],
                    defaults={
                        'source': source,
                        'title': job_data['title'],
                        'company_name': job_data['company_name'],
                        'job_type': job_data['job_type'],
                        'location': job_data['location'],
                        'skills_tags': job_data['skills_tags'],
                        'body': job_data['body'],
                        'url': job_data['url'],
                        'application_link': job_data['application_link'],
                        'timestamp': job_data['timestamp'],
                        'author': job_data.get('author', ''),
                    }
                )

                if not created:
                    logger.debug(f"Skipping duplicate job: {job_post.title}")
                    continue

                new_count += 1
                is_signal, confidence, reasoning = detect_job_signal(job_post)

                if not is_signal:
                    logger.info(f"Not a job signal: {job_post.title} (confidence: {confidence:.2f})")
                    continue

                qualification = qualify_job(job_post)

                if qualification.classification == 'high':
                    high_count += 1
                    generate_draft_message(job_post, qualification)

                logger.info(
                    f"Processed GitHub job: {job_post.title} | "
                    f"Classification: {qualification.classification} | "
                    f"Confidence: {qualification.confidence:.0%}"
                )

            logger.info(
                f"GitHub scraping complete: {new_count} new jobs, {high_count} high-quality"
            )

        except (APIConnectionError, MissingAPIKeyError) as e:
            logger.error(f"GitHub scraping failed: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in GitHub scraping: {e}")

    @staticmethod
    def poll_rss_feeds(limit=20):
        # Poll RSS feeds from various job boards
        logger.info("Starting RSS feed scraping...")

        try:
            rss_sources = Source.objects.filter(
                type=Source.RSS_FEED,
                is_active=True
            )

            if not rss_sources.exists():
                logger.info("No active RSS feed sources found")
                # Create default sources
                ScraperPollerJob._create_default_rss_sources()
                rss_sources = Source.objects.filter(type=Source.RSS_FEED, is_active=True)

            total_new = 0
            total_high = 0

            for source in rss_sources:
                logger.info(f"Scraping RSS feed: {source.name}")

                try:
                    scraper = RSSJobScraper(feed_url=source.base_url, board_name=source.identifier)
                    job_keywords = getattr(settings, 'JOB_KEYWORDS', 'python,django,wordpress').split(',')
                    job_keywords = [kw.strip() for kw in job_keywords]
                    jobs = scraper.scrape_listings(limit=limit, keywords=job_keywords)
                    new_count, high_count = ScraperPollerJob._process_jobs(jobs, source)

                    total_new += new_count
                    total_high += high_count

                    logger.info(f"RSS feed {source.name}: {new_count} new jobs, {high_count} high-quality")

                except Exception as e:
                    logger.error(f"Failed to scrape RSS feed {source.name}: {e}")
                    continue

            logger.info(f"RSS scraping complete: {total_new} new jobs, {total_high} high-quality")

        except Exception as e:
            logger.exception(f"Unexpected error in RSS scraping: {e}")

    @staticmethod
    def poll_job_boards(limit=20):
        # Poll job boards using BeautifulSoup scrapers
        logger.info("Starting job board scraping...")

        try:
            board_sources = Source.objects.filter(
                type=Source.JOB_BOARD,
                is_active=True
            )

            if not board_sources.exists():
                logger.info("No active job board sources found")
                ScraperPollerJob._create_default_board_sources()
                board_sources = Source.objects.filter(type=Source.JOB_BOARD, is_active=True)

            total_new = 0
            total_high = 0

            for source in board_sources:
                logger.info(f"Scraping job board: {source.name}")

                try:
                    scraper = ScraperPollerJob._get_board_scraper(source.identifier)

                    if not scraper:
                        logger.warning(f"No scraper found for {source.identifier}")
                        continue

                    jobs = scraper.scrape_listings(limit=limit)
                    new_count, high_count = ScraperPollerJob._process_jobs(jobs, source)

                    total_new += new_count
                    total_high += high_count

                    logger.info(f"Job board {source.name}: {new_count} new jobs, {high_count} high-quality")

                except Exception as e:
                    logger.error(f"Failed to scrape job board {source.name}: {e}")
                    continue

            logger.info(f"Job board scraping complete: {total_new} new jobs, {total_high} high-quality")

        except Exception as e:
            logger.exception(f"Unexpected error in job board scraping: {e}")

    @staticmethod
    def _get_board_scraper(identifier):
        scrapers = {
            'remoteok': RemoteOKScraper(),
            # 'weworkremotely': WeWorkRemotelyScraper(),  # Disabled: blocked by anti-bot, use RSS instead
        }
        return scrapers.get(identifier.lower())

    @staticmethod
    def _process_jobs(jobs, source):
        # Process scraped jobs: create records, qualify, generate drafts
        new_count = 0
        high_count = 0

        for job_data in jobs:
            try:
                job_post, created = JobPost.objects.get_or_create(
                    external_id=job_data['id'],
                    defaults={
                        'source': source,
                        'title': job_data['title'],
                        'company_name': job_data.get('company_name', ''),
                        'job_type': job_data.get('job_type', ''),
                        'location': job_data.get('location', ''),
                        'skills_tags': job_data.get('skills_tags', ''),
                        'body': job_data['body'],
                        'url': job_data['url'],
                        'application_link': job_data.get('application_link', job_data['url']),
                        'timestamp': job_data.get('timestamp', datetime.now()),
                        'author': job_data.get('author', ''),
                    }
                )

                if not created:
                    continue

                new_count += 1
                is_signal, confidence, reasoning = detect_job_signal(job_post)

                if not is_signal:
                    logger.info(f"Not a job signal: {job_post.title}")
                    continue

                qualification = qualify_job(job_post)

                if qualification.classification == 'high':
                    high_count += 1
                    generate_draft_message(job_post, qualification)

                logger.debug(
                    f"Processed: {job_post.title} | {qualification.classification} | "
                    f"{qualification.confidence:.0%}"
                )

            except Exception as e:
                logger.error(f"Failed to process job {job_data.get('title', 'Unknown')}: {e}")
                continue

        return new_count, high_count

    @staticmethod
    def _create_default_rss_sources():
        default_feeds = [
            {
                'identifier': 'remoteok',
                'name': 'RemoteOK RSS Feed',
                'base_url': 'https://remoteok.com/remote-jobs.rss',
            },
            {
                'identifier': 'weworkremotely',
                'name': 'We Work Remotely RSS Feed',
                'base_url': 'https://weworkremotely.com/categories/remote-programming-jobs.rss',
            },
        ]

        for feed in default_feeds:
            Source.objects.get_or_create(
                type=Source.RSS_FEED,
                identifier=feed['identifier'],
                defaults={
                    'name': feed['name'],
                    'base_url': feed['base_url'],
                    'scraper_type': 'rss',
                    'is_active': True,
                }
            )

        logger.info("Created default RSS feed sources")

    @staticmethod
    def _create_default_board_sources():
        default_boards = [
            {
                'identifier': 'remoteok',
                'name': 'RemoteOK',
                'base_url': 'https://remoteok.com',
            },
            # WeWorkRemotely disabled - blocked by anti-bot protection, use RSS feed instead
        ]

        for board in default_boards:
            Source.objects.get_or_create(
                type=Source.JOB_BOARD,
                identifier=board['identifier'],
                defaults={
                    'name': board['name'],
                    'base_url': board['base_url'],
                    'scraper_type': 'beautifulsoup',
                    'is_active': True,
                    'rate_limit_seconds': 5,
                }
            )

        logger.info("Created default job board sources")
