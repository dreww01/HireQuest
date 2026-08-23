# HireQuest 🤖

Automated job hunting system that scrapes job boards and GitHub for opportunities, uses AI to qualify them, and sends Telegram alerts.

## Features

- 🔍 **Multi-Source Scraping**: GitHub Issues, RemoteOK, We Work Remotely, RSS feeds
- 🤖 **AI-Powered Qualification**: Uses HuggingFace Llama for intelligent job matching
- 📱 **Instant Telegram Alerts**: Get notified of high-quality matches immediately
- 🛡️ **Rate Limiting & robots.txt**: Respectful scraping with built-in compliance
- 📊 **Dashboard**: Clean UI to track and manage job opportunities
- 🔄 **Deduplication**: Prevents duplicate alerts
- ⚡ **Flexible Architecture**: Easy to add new scrapers

## Tech Stack

- **Backend**: Django 5.0
- **Database**: SQLite
- **AI**: Hugging Face API (Llama-3.2-1B-Instruct)
- **Scraping**: BeautifulSoup, feedparser, Selenium, GitHub API
- **Integrations**: GitHub API, Telegram Bot API

## Quick Start

### 1. Automated Setup (Recommended)

```bash
python setup.py
```

This will:
- Create virtual environment
- Set up directory structure
- Create .env file from template
- Install dependencies
- Set up .gitignore

### 2. Manual Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API credentials
```

### 3. Get API Credentials

**GitHub API (Optional):**
1. Go to https://github.com/settings/tokens
2. Create token with scopes: `public_repo`, `read:org`
3. Copy to .env (without token: 60 req/hr, with token: 5,000 req/hr)

**Telegram Bot (Required for alerts):**
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the token to .env
4. Message your bot, then visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Copy your chat_id to .env

**HuggingFace (Required for AI):**
1. Go to https://huggingface.co/settings/tokens
2. Create a new token
3. Copy to .env

### 4. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

## Scraping Commands

```bash
# Run full pipeline (all scrapers)
python manage.py run_full_pipeline

# Run individual scrapers
python manage.py scrape_github --limit 20
python manage.py scrape_rss --limit 20
python manage.py scrape_boards --limit 20

# Customize pipeline
python manage.py run_full_pipeline --limit 30        # More jobs per source
python manage.py run_full_pipeline --skip-github     # Skip GitHub
python manage.py run_full_pipeline --skip-rss        # Skip RSS feeds
python manage.py run_full_pipeline --skip-boards     # Skip job boards
```

## Development Commands

```bash
# Run server
python manage.py runserver

# Run tests (recommended)
uv run pytest -v
# or via Django test runner
python manage.py test

# Database
python manage.py makemigrations
python manage.py migrate
```

For full contribution guidelines and test details, see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) and [docs/TESTING.md](docs/TESTING.md).

## Project Structure

```
hirequest/
├── config/                        # Django project settings
├── core/                          # Main application
│   ├── models.py                 # Data models (Source, JobPost, etc.)
│   ├── views.py                  # Dashboard views
│   ├── admin.py                  # Admin configuration
│   ├── management/commands/      # CLI commands
│   │   ├── run_full_pipeline.py  # Run all scrapers
│   │   ├── scrape_github.py      # GitHub Issues scraper
│   │   ├── scrape_rss.py         # RSS feed scraper
│   │   └── scrape_boards.py      # Job board scraper
│   └── templates/                # UI templates
├── integrations/                  # Scrapers & API clients
│   ├── base_scraper.py           # Base scraper class
│   ├── github_scraper.py         # GitHub Issues API
│   ├── rss_scraper.py            # RSS feed parser
│   ├── weworkremotely_scraper.py # WeWorkRemotely scraper
│   ├── remoteok_scraper.py       # RemoteOK scraper
│   ├── huggingface_client.py     # AI client
│   └── telegram_client.py        # Telegram alerts
├── jobs/                          # Background jobs
│   └── scraper_poller.py         # Polling orchestrator
├── utils/                         # Helper utilities
│   ├── ai_service.py             # AI qualification logic
│   ├── signal_detection.py       # Job signal detection
│   ├── validators.py             # Credential validation
│   └── exceptions.py             # Custom exceptions
├── .env                           # Environment variables (not in git)
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## How It Works

### Scraping Flow

1. **GitHub Issues Scraper** (API-based)
   - Searches for issues mentioning "paid", "contract", "freelance", "hire", "bounty"
   - Filters out unpaid/volunteer posts
   - Extracts tech stack from repo languages and issue labels
   - Zero web scraping risk (official API)

2. **RSS Feed Scraper** (RemoteOK, WeWorkRemotely)
   - Parses public RSS feeds
   - Filters by keywords (Python, Django, WordPress, etc.)
   - Extracts company, location, job type, skills
   - No rate limiting issues (intended for consumption)

3. **BeautifulSoup Scrapers** (Job boards)
   - Scrapes We Work Remotely and RemoteOK HTML
   - Respects robots.txt and rate limits (5s between requests)
   - Extracts full job descriptions from detail pages
   - Low-risk permissive sites

4. **AI Qualification Pipeline**
   - Detects job signals (filters out non-jobs)
   - Classifies: HIGH / MEDIUM / IGNORE
   - Generates personalized drafts for HIGH jobs
   - Sends Telegram alerts automatically

### Data Sources

| Source | Type | Risk | Rate Limit | Notes |
|--------|------|------|------------|-------|
| GitHub Issues | API | None | 60/hr (5k with token) | Official API, safe |
| RemoteOK RSS | RSS | None | None | Public feed |
| WeWorkRemotely RSS | RSS | None | None | Public feed |
| RemoteOK HTML | BeautifulSoup | Low | 5s per request | Tolerated scraping |
| WeWorkRemotely HTML | BeautifulSoup | Low | 3s per request | Permissive robots.txt |

## Scraping Best Practices

**Built-in Safeguards:**
- ✅ robots.txt compliance checking
- ✅ Configurable rate limiting (default 5s between requests)
- ✅ Exponential backoff on failures
- ✅ User-agent identification
- ✅ Respectful request patterns

**Recommended Settings:**
```env
SCRAPE_INTERVAL_MINUTES=60  # Don't scrape too frequently
MAX_JOBS_PER_SOURCE=20      # Limit results per scrape
JOB_MAX_AGE_DAYS=7          # Only recent jobs
```

## Common Issues

**GitHub rate limit exceeded:**
- Add GITHUB_TOKEN to .env for 5,000 req/hr (vs 60 without)
- Reduce scraping frequency

**HuggingFace first request slow:**
- Normal behavior (model loading takes 30-60s)
- Subsequent requests are faster

**Telegram not receiving messages:**
- Message your bot first before getting chat_id
- Verify token and chat_id are correct
- Check bot isn't blocked

**Scraper returns no jobs:**
- Job boards may have changed their HTML structure
- Check console logs for specific errors
- Verify internet connection and rate limits

## Adding New Scrapers

The architecture makes it easy to add new sources:

1. **Create scraper class** in `integrations/`:
```python
from integrations.base_scraper import BaseScraper

class NewBoardScraper(BaseScraper):
    def scrape_listings(self, limit=20):
        # Return list of job dicts
        pass
```

2. **Add to poller** in `jobs/scraper_poller.py`:
```python
scrapers = {
    'newboard': NewBoardScraper(),
}
```

3. **Create Source** in database or code:
```python
Source.objects.create(
    type=Source.JOB_BOARD,
    identifier='newboard',
    name='New Job Board',
    scraper_type='beautifulsoup',
    base_url='https://newboard.com',
)
```

## Architecture Decisions

### Method: Hybrid scraping approach
**Tradeoffs:**
- **Pros**: Multiple sources, low risk, respectful scraping, flexible
- **Cons**: Job boards can change HTML, maintenance needed

**Industry Alternatives:**
- **Scrapy** (more powerful, heavier, overkill for this use case)
- **Puppeteer/Playwright** (handles JS, but slower and more resource-intensive)
- **Paid APIs** (Adzuna, Indeed API - expensive, limited free tiers)

### Why This Stack?
- **BeautifulSoup**: Simple, fast for static HTML
- **RSS feeds**: Zero scraping risk, intended for consumption
- **GitHub API**: Official, generous rate limits
- **Selenium**: Available for JS-heavy sites (not implemented yet)

## Contributing & Architecture Quick-Reference

For complete contribution workflows, branch naming conventions, commit standards, and architecture details, refer to [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

### Quick Reference
- **Branch Naming**: `dsh/<issue-id>` (e.g. `dsh/ORC-5`)
- **Commit Convention**: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`)
- **Run Tests**: `uv run pytest -v`
- **Documentation**:
  - [Contributing & Architecture Guide](docs/CONTRIBUTING.md)
  - [Testing Guide](docs/TESTING.md)
  - [Production Run Guide](docs/PRODUCTION.md)

## License

MIT License

## Roadmap

**v1.0 (Current):**
- ✅ GitHub Issues scraping
- ✅ RSS feed scraping
- ✅ Job board scraping (BeautifulSoup)
- ✅ AI qualification
- ✅ Telegram alerts
- ✅ Dashboard UI

**v2.0 (Future):**
- [ ] Selenium scrapers for JS-heavy sites (Wellfound, LinkedIn)
- [ ] PostgreSQL support
- [ ] Automated scheduling (Celery/cron)
- [ ] More job boards (Remotive, FlexJobs, etc.)
- [ ] Company career page scraping
- [ ] Advanced analytics

---

**Built with Django, BeautifulSoup, and AI**
