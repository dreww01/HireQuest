# RSS feed scraper for job boards

import logging
from datetime import datetime
from html import unescape

import feedparser
import requests
from bs4 import BeautifulSoup

from utils.exceptions import APIConnectionError

logger = logging.getLogger(__name__)


class RSSJobScraper:
    # Scrapes job boards via RSS feeds

    KNOWN_FEEDS = {
        'remoteok': 'https://remoteok.com/remote-jobs.rss',
        'weworkremotely': 'https://weworkremotely.com/categories/remote-programming-jobs.rss',
        'remotive': 'https://remotive.com/api/remote-jobs/feed',
        'stackoverflow': 'https://stackoverflow.com/jobs/feed',
    }

    def __init__(self, feed_url=None, board_name=None):
        if feed_url:
            self.feed_url = feed_url
            self.board_name = board_name or 'rss_feed'
        elif board_name and board_name.lower() in self.KNOWN_FEEDS:
            self.feed_url = self.KNOWN_FEEDS[board_name.lower()]
            self.board_name = board_name.lower()
        else:
            raise ValueError("Must provide either feed_url or valid board_name")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'JobHuntBot/1.0 (Educational Project)'
        })

    def scrape_listings(self, limit=20, keywords=None):
        # Scrape job listings from RSS feed
        try:
            response = self.session.get(self.feed_url, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {self.feed_url}")
                return []

            jobs = []

            for entry in feed.entries[:limit * 2]:
                job = self._parse_entry(entry)

                if keywords:
                    if not self._matches_keywords(job, keywords):
                        continue

                jobs.append(job)

                if len(jobs) >= limit:
                    break

            logger.info(f"Scraped {len(jobs)} jobs from {self.board_name} RSS feed")
            return jobs

        except requests.RequestException as e:
            logger.error(f"Failed to fetch RSS feed {self.feed_url}: {e}")
            raise APIConnectionError(service=f'RSS Feed ({self.board_name})', original_error=e)

    def _parse_entry(self, entry):
        # Parse RSS entry into standardized job dict
        title = entry.get('title', 'No Title')
        link = entry.get('link', '')
        description = entry.get('summary', entry.get('description', ''))
        published = entry.get('published_parsed') or entry.get('updated_parsed')
        if published:
            timestamp = datetime(*published[:6])
        else:
            timestamp = datetime.now()

        company, location, job_type, skills = self._extract_metadata(description, entry)
        description_text = self._clean_html(description)
        job_id = entry.get('id', entry.get('guid', link))
        unique_id = f"{self.board_name}_{hash(job_id) % 1000000}"

        return {
            'id': unique_id,
            'title': unescape(title),
            'company_name': company,
            'job_type': job_type,
            'location': location,
            'skills_tags': skills,
            'body': description_text[:5000],
            'url': link,
            'application_link': link,
            'timestamp': timestamp,
            'author': '',
        }

    def _extract_metadata(self, description, entry):
        # Extract company, location, job type, skills from RSS entry
        company = 'Unknown'
        location = 'Remote'
        job_type = 'Full-time'
        skills = ''

        if self.board_name == 'remoteok':
            tags = entry.get('tags', [])
            if tags:
                company = tags[0].get('term', 'Unknown')
                skills = ','.join([tag.get('term', '') for tag in tags[1:] if tag.get('term')])

        elif self.board_name == 'weworkremotely':
            title = entry.get('title', '')
            if ':' in title:
                company = title.split(':')[0].strip()

        soup = BeautifulSoup(description, 'html.parser')
        text = soup.get_text().lower()

        if 'remote' in text:
            location = 'Remote'
        elif 'worldwide' in text:
            location = 'Worldwide'

        if 'contract' in text or 'contractor' in text:
            job_type = 'Contract'
        elif 'part-time' in text or 'part time' in text:
            job_type = 'Part-time'
        elif 'full-time' in text or 'full time' in text:
            job_type = 'Full-time'

        tech_keywords = [
            'python', 'django', 'flask', 'wordpress', 'php',
            'javascript', 'react', 'vue', 'node', 'typescript',
            'ruby', 'rails', 'java', 'go', 'rust'
        ]

        found_skills = [kw for kw in tech_keywords if kw in text]
        if found_skills and not skills:
            skills = ','.join(found_skills)

        return company, location, job_type, skills

    def _clean_html(self, html_content):
        # Strip HTML tags and clean text
        soup = BeautifulSoup(html_content, 'html.parser')

        for tag in soup(['script', 'style']):
            tag.decompose()

        text = soup.get_text(separator=' ')
        text = ' '.join(text.split())

        return unescape(text)

    def _matches_keywords(self, job, keywords):
        # Check if job matches any of the provided keywords
        searchable_text = f"{job['title']} {job['body']} {job['skills_tags']}".lower()

        for keyword in keywords:
            if keyword.lower() in searchable_text:
                return True

        return False
