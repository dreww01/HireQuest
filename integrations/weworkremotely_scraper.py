# We Work Remotely scraper

import logging
import re
from datetime import datetime

from integrations.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class WeWorkRemotelyScraper(BaseScraper):
    # Scrapes We Work Remotely job board

    def __init__(self):
        super().__init__(
            base_url='https://weworkremotely.com',
            rate_limit_seconds=3
        )

    def scrape_listings(self, limit=20):
        # Scrape job listings from programming category
        jobs = []
        category_url = f"{self.base_url}/remote-jobs/search?term=programming"

        try:
            soup = self.fetch_html(category_url)
            if not soup:
                return jobs

            job_elements = soup.find_all('li', class_='feature')

            for job_elem in job_elements[:limit]:
                try:
                    job = self._parse_listing(job_elem)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"Failed to parse WWR job listing: {e}")
                    continue

            logger.info(f"Scraped {len(jobs)} jobs from We Work Remotely")
            return jobs

        except Exception as e:
            logger.error(f"Failed to scrape We Work Remotely: {e}")
            return jobs

    def _parse_listing(self, job_elem):
        # Parse individual job listing element
        title_elem = job_elem.find('span', class_='title')
        if not title_elem:
            return None

        link_elem = job_elem.find('a')
        if not link_elem:
            return None

        job_url = self.base_url + link_elem.get('href', '')
        title = title_elem.get_text(strip=True)

        company_elem = job_elem.find('span', class_='company')
        company = company_elem.get_text(strip=True) if company_elem else 'Unknown'
        location = 'Remote'

        region_elem = job_elem.find('span', class_='region')
        region = region_elem.get_text(strip=True) if region_elem else ''

        job_details = self.scrape_job_detail(job_url)

        if not job_details:
            # Fallback if detail scrape fails
            job_details = {
                'body': '',
                'skills_tags': '',
                'timestamp': datetime.now(),
            }

        job_id = f"wwr_{re.search(r'/(\d+)', job_url).group(1) if re.search(r'/(\d+)', job_url) else hash(job_url) % 1000000}"

        return {
            'id': job_id,
            'title': title,
            'company_name': company,
            'job_type': 'Full-time',  # WWR is mostly full-time
            'location': location,
            'skills_tags': job_details['skills_tags'],
            'body': job_details['body'],
            'url': job_url,
            'application_link': job_url,
            'timestamp': job_details['timestamp'],
            'author': '',
        }

    def scrape_job_detail(self, job_url):
        # Scrape full job description from detail page
        try:
            soup = self.fetch_html(job_url)
            if not soup:
                return None

            desc_elem = soup.find('div', class_='listing-container')
            description = desc_elem.get_text(separator='\n', strip=True) if desc_elem else ''

            date_elem = soup.find('time')
            timestamp = datetime.now()
            if date_elem and date_elem.get('datetime'):
                try:
                    timestamp = datetime.fromisoformat(date_elem['datetime'].replace('Z', '+00:00'))
                except Exception:
                    pass

            skills = self._extract_skills(description)

            return {
                'body': description[:5000],
                'skills_tags': skills,
                'timestamp': timestamp,
            }

        except Exception as e:
            logger.warning(f"Failed to scrape job detail {job_url}: {e}")
            return None

    def _extract_skills(self, text):
        # Extract tech skills from job description
        tech_keywords = [
            'python', 'django', 'flask', 'fastapi',
            'wordpress', 'php',
            'javascript', 'typescript', 'react', 'vue', 'angular',
            'node', 'nodejs',
            'ruby', 'rails',
            'java', 'spring',
            'go', 'golang',
            'rust',
            'c#', '.net',
            'postgresql', 'mysql', 'mongodb',
            'aws', 'azure', 'docker', 'kubernetes',
        ]

        text_lower = text.lower()
        found_skills = set()

        for skill in tech_keywords:
            if re.search(rf'\b{re.escape(skill)}\b', text_lower):
                found_skills.add(skill)

        return ','.join(sorted(found_skills))
