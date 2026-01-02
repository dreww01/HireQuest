# RemoteOK scraper using JSON API

import logging
import re
from datetime import datetime
from html import unescape

import requests
from bs4 import BeautifulSoup

from integrations.base_scraper import BaseScraper
from utils.exceptions import APIConnectionError

logger = logging.getLogger(__name__)


class RemoteOKScraper(BaseScraper):
    # Scrapes RemoteOK job board using their JSON API

    def __init__(self):
        super().__init__(
            base_url='https://remoteok.com',
            rate_limit_seconds=5
        )

    def scrape_listings(self, limit=20, keywords=None):
        # Scrape job listings from RemoteOK JSON API
        jobs = []
        api_url = 'https://remoteok.com/api'

        try:
            # Apply rate limiting before making the API request
            self._rate_limit()

            logger.debug(f"Fetching RemoteOK API: {api_url}")
            response = self.session.get(api_url, timeout=30)
            
            # Log response status for debugging
            logger.debug(f"RemoteOK API response status: {response.status_code}")
            
            # Check for HTTP errors
            if response.status_code != 200:
                logger.error(
                    f"RemoteOK API returned non-200 status: {response.status_code}. "
                    f"Response: {response.text[:200]}"
                )
                raise APIConnectionError(
                    service='RemoteOK API',
                    original_error=f"HTTP {response.status_code}: {response.reason}"
                )

            response.raise_for_status()

            # Validate response structure
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"RemoteOK API returned invalid JSON: {e}. Response: {response.text[:200]}")
                raise APIConnectionError(
                    service='RemoteOK API',
                    original_error=f"Invalid JSON response: {str(e)}"
                )

            # Validate that data is a list
            if not isinstance(data, list):
                logger.error(
                    f"RemoteOK API returned unexpected data type: {type(data)}. "
                    f"Expected list. Response preview: {str(data)[:200]}"
                )
                raise APIConnectionError(
                    service='RemoteOK API',
                    original_error=f"Unexpected response format: expected list, got {type(data).__name__}"
                )

            # RemoteOK API returns metadata as first element, jobs start from index 1
            job_listings = data[1:] if len(data) > 1 else []
            
            if not job_listings:
                logger.warning("RemoteOK API returned no job listings")
                return jobs

            logger.info(f"RemoteOK API returned {len(job_listings)} job listings, processing up to {limit}")

            for job_data in job_listings[:limit]:
                try:
                    # Validate job_data is a dict before parsing
                    if not isinstance(job_data, dict):
                        logger.warning(f"Skipping invalid job data (not a dict): {type(job_data)}")
                        continue

                    job = self._parse_api_listing(job_data, keywords)
                    if job:
                        jobs.append(job)
                except KeyError as e:
                    logger.warning(f"Failed to parse RemoteOK job listing (missing key): {e}. Data: {job_data}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to parse RemoteOK job listing: {e}. Data keys: {list(job_data.keys()) if isinstance(job_data, dict) else 'N/A'}")
                    continue

            logger.info(f"Scraped {len(jobs)} jobs from RemoteOK")
            return jobs

        except requests.RequestException as e:
            logger.error(
                f"Network error while scraping RemoteOK: {e}. "
                f"URL: {api_url}, Status: {getattr(e.response, 'status_code', 'N/A')}"
            )
            raise APIConnectionError(
                service='RemoteOK API',
                original_error=e
            )
        except APIConnectionError:
            # Re-raise APIConnectionError as-is
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while scraping RemoteOK: {e}")
            raise APIConnectionError(
                service='RemoteOK API',
                original_error=e
            )

    def _parse_api_listing(self, job_data, keywords=None):
        # Parse job from RemoteOK JSON API response
        try:
            job_id = job_data.get('id')
            if not job_id:
                return None

            title = job_data.get('position', '')
            company = job_data.get('company', 'Unknown')
            location = job_data.get('location', 'Remote')
            tags = job_data.get('tags', [])
            skills = ','.join([tag.lower() for tag in tags if tag])

            if keywords:
                if not any(kw.lower() in skills.lower() for kw in keywords):
                    return None

            description = job_data.get('description', '')
            # Clean HTML from description
            description = self._clean_html(description)
            
            timestamp = datetime.now()
            if job_data.get('date'):
                try:
                    from datetime import datetime as dt
                    timestamp = dt.fromisoformat(job_data['date'].replace('Z', '+00:00'))
                except Exception:
                    pass

            slug = job_data.get('slug', '')
            job_url = f"{self.base_url}/remote-jobs/{slug}" if slug else f"{self.base_url}/remote-jobs/{job_id}"

            return {
                'id': f"remoteok_{job_id}",
                'title': title,
                'company_name': company,
                'job_type': 'Full-time',
                'location': location,
                'skills_tags': skills,
                'body': description[:5000],
                'url': job_url,
                'application_link': job_data.get('apply_url', job_url),
                'timestamp': timestamp,
                'author': '',
            }
        except Exception as e:
            logger.warning(f"Failed to parse RemoteOK API job: {e}")
            return None

    def _parse_listing(self, job_elem):
        # Parse individual job listing row (HTML fallback)
        job_id = job_elem.get('data-id')
        if not job_id:
            return None

        title_elem = job_elem.find('h2', itemprop='title')
        if not title_elem:
            return None
        title = title_elem.get_text(strip=True)

        company_elem = job_elem.find('h3', itemprop='name')
        company = company_elem.get_text(strip=True) if company_elem else 'Unknown'

        location_elem = job_elem.find('div', class_='location')
        location = location_elem.get_text(strip=True) if location_elem else 'Remote'

        tag_elements = job_elem.find_all('div', class_='tag')
        skills = ','.join([tag.get_text(strip=True).lower() for tag in tag_elements])

        time_elem = job_elem.find('time')
        timestamp = datetime.now()
        if time_elem and time_elem.get('datetime'):
            try:
                timestamp = datetime.fromisoformat(time_elem['datetime'].replace('Z', '+00:00'))
            except Exception:
                pass

        job_url = f"{self.base_url}/remote-jobs/{job_id}"
        desc_elem = job_elem.find('div', class_='description')
        description = desc_elem.get_text(separator='\n', strip=True) if desc_elem else ''

        if len(description) < 100:
            details = self.scrape_job_detail(job_url)
            if details:
                description = details.get('body', description)

        return {
            'id': f"remoteok_{job_id}",
            'title': title,
            'company_name': company,
            'job_type': 'Full-time',  # Most RemoteOK jobs are full-time
            'location': location,
            'skills_tags': skills,
            'body': description[:5000],
            'url': job_url,
            'application_link': job_url,
            'timestamp': timestamp,
            'author': '',
        }

    def scrape_job_detail(self, job_url):
        # Scrape full job description from detail page
        try:
            soup = self.fetch_html(job_url)
            if not soup:
                return None

            desc_elem = soup.find('div', class_='description')
            if not desc_elem:
                desc_elem = soup.find('div', itemprop='description')

            description = desc_elem.get_text(separator='\n', strip=True) if desc_elem else ''

            return {
                'body': description[:5000],
            }

        except Exception as e:
            logger.warning(f"Failed to scrape job detail {job_url}: {e}")
            return None

    def _clean_html(self, html_content):
        # Strip HTML tags and clean text, preserving line breaks
        if not html_content:
            return ''
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style tags
            for tag in soup(['script', 'style']):
                tag.decompose()
            
            # Get text with line breaks preserved
            # Replace <br> and <p> tags with newlines
            for br in soup.find_all('br'):
                br.replace_with('\n')
            for p in soup.find_all('p'):
                p.append('\n')
            
            # Get text and clean up whitespace
            text = soup.get_text(separator='\n')
            
            # Clean up excessive whitespace while preserving paragraph breaks
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join([line for line in lines if line])
            
            # Unescape HTML entities
            text = unescape(text)
            
            return text
        except Exception as e:
            logger.warning(f"Failed to clean HTML content: {e}")
            # Fallback: basic HTML tag removal using regex
            import re
            text = re.sub(r'<[^>]+>', '', html_content)
            text = unescape(text)
            return ' '.join(text.split())
