# Base scraper interface for job board scrapers

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from utils.exceptions import APIConnectionError

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    # Abstract base class for job scrapers with rate limiting and robots.txt compliance

    def __init__(self, base_url, rate_limit_seconds=5):
        self.base_url = base_url
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = None
        self.robot_parser = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'JobHuntBot/1.0 (Educational Project; +https://github.com/yourrepo)'
        })
        self._init_robots_parser()

    def _init_robots_parser(self):
        try:
            parsed_url = urlparse(self.base_url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            self.robot_parser = RobotFileParser()
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()

            logger.info(f"Loaded robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"Could not load robots.txt: {e}. Proceeding with caution.")
            self.robot_parser = None

    def can_fetch(self, url):
        if self.robot_parser is None:
            return True

        return self.robot_parser.can_fetch('*', url)

    def _rate_limit(self):
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.rate_limit_seconds:
                sleep_time = self.rate_limit_seconds - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self.last_request_time = time.time()

    def fetch_html(self, url, max_retries=3):
        # Fetch HTML with rate limiting and retries
        if not self.can_fetch(url):
            logger.warning(f"robots.txt disallows fetching {url}")
            return None

        self._rate_limit()

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                return BeautifulSoup(response.content, 'html.parser')

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")

                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise APIConnectionError(
                        service=self.__class__.__name__,
                        original_error=e
                    )

        return None

    def is_recent(self, post_date, max_days=7):
        if not post_date:
            return True  # Include if we can't determine age

        age = datetime.now() - post_date
        return age <= timedelta(days=max_days)

    @abstractmethod
    def scrape_listings(self, limit=10):
        # Scrape job listings - returns list of standardized job dicts
        pass

    @abstractmethod
    def scrape_job_detail(self, job_url):
        # Scrape full details from individual job page
        pass
