# GitHub Issues scraper for finding freelance/contract opportunities

import logging
import re
from datetime import datetime

import requests

from utils.exceptions import APIConnectionError, MissingAPIKeyError
from utils.validators import validate_github_credentials

logger = logging.getLogger(__name__)


class GitHubScraper:
    # Scrapes GitHub Issues for paid work opportunities using Search API

    PAID_KEYWORDS = [
        'paid',
        'contract',
        'freelancer',
        'freelance',
        'hire',
        'hiring',
        'bounty',
        'looking for developer',
        'looking for a developer',
        'need a developer',
        'compensation',
        'budget',
        'rate',
        'payment',
    ]

    # Keywords that indicate unpaid work (filter out)
    UNPAID_KEYWORDS = [
        'volunteer',
        'unpaid',
        'no budget',
        'free',
        'open source contributor',
        'looking for contributors',
    ]

    def __init__(self, github_token=None):
        self.github_token = github_token

        if github_token:
            validate_github_credentials(github_token)

        self.base_url = 'https://api.github.com'
        self.session = requests.Session()

        if github_token:
            self.session.headers.update({
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json',
            })
        else:
            self.session.headers.update({
                'Accept': 'application/vnd.github.v3+json',
            })
            logger.warning("No GitHub token provided. Rate limited to 60 requests/hour.")

    def search_issues(self, keywords=None, max_age_days=14, limit=30):
        # Search GitHub issues for job opportunities
        if keywords is None:
            keywords = self.PAID_KEYWORDS[:5]  # Use top 5 to avoid query length issues

        results = []

        for keyword in keywords:
            try:
                created_after = datetime.now().replace(
                    day=datetime.now().day - max_age_days
                ).strftime('%Y-%m-%d')

                query = f'"{keyword}" in:title,body created:>{created_after}'

                url = f"{self.base_url}/search/issues"
                params = {
                    'q': query,
                    'sort': 'created',
                    'order': 'desc',
                    'per_page': min(limit, 30),  # API max is 100
                }

                response = self.session.get(url, params=params, timeout=15)

                if response.status_code == 403:
                    logger.error("GitHub API rate limit exceeded. Wait 1 hour or add token.")
                    break

                response.raise_for_status()
                data = response.json()

                for issue in data.get('items', []):
                    if self._is_unpaid(issue):
                        continue

                    job = self._parse_issue(issue)
                    if job and job not in results:
                        results.append(job)

                    if len(results) >= limit:
                        break

                logger.info(f"Found {len(data.get('items', []))} issues for keyword: {keyword}")

            except requests.RequestException as e:
                logger.error(f"Failed to search GitHub for '{keyword}': {e}")
                raise APIConnectionError(service='GitHub API', original_error=e)

            if len(results) >= limit:
                break

        return results[:limit]

    def _is_unpaid(self, issue):
        text = f"{issue.get('title', '')} {issue.get('body', '')}".lower()

        for keyword in self.UNPAID_KEYWORDS:
            if keyword in text:
                return True

        return False

    def _parse_issue(self, issue):
        # Parse GitHub issue into standardized job dict
        repo_url = issue.get('repository_url', '')
        repo_name = repo_url.split('/')[-1] if repo_url else 'Unknown'
        labels = [label['name'] for label in issue.get('labels', [])]
        tech_stack = self._extract_tech_stack(issue.get('body', ''), labels)
        created_at = issue.get('created_at')
        timestamp = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ') if created_at else datetime.now()

        return {
            'id': f"github_{issue['id']}",
            'title': issue.get('title', 'No Title'),
            'company_name': repo_name,
            'job_type': 'Contract',  # Assume contract for GitHub issues
            'location': 'Remote',  # GitHub issues are typically remote
            'skills_tags': tech_stack,
            'body': issue.get('body', '')[:5000],  # Truncate long descriptions
            'url': issue.get('html_url', ''),
            'application_link': issue.get('html_url', ''),  # Apply via GitHub comment
            'timestamp': timestamp,
            'author': issue.get('user', {}).get('login', 'Unknown'),
        }

    def _extract_tech_stack(self, body, labels):
        # Extract technology keywords from issue body and labels
        tech_keywords = [
            'python', 'django', 'fastapi',
            'sql', 'postgresql', 'mysql', 'mongodb',
            'gcp', 'docker',
        ]

        found_tech = set()

        for label in labels:
            label_lower = label.lower()
            for tech in tech_keywords:
                if tech in label_lower:
                    found_tech.add(tech)

        if body:
            body_lower = body.lower()
            for tech in tech_keywords:
                if re.search(rf'\b{re.escape(tech)}\b', body_lower):
                    found_tech.add(tech)

        return ','.join(sorted(found_tech))

    def get_repository_tech_stack(self, repo_url):
        # Get programming languages used in a repository
        try:
            languages_url = f"{repo_url}/languages"
            response = self.session.get(languages_url, timeout=10)
            response.raise_for_status()

            languages = response.json()
            return ','.join(languages.keys())

        except Exception as e:
            logger.debug(f"Could not fetch languages for {repo_url}: {e}")
            return ''
