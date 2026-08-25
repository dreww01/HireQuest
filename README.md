# HireQuest 🤖

> **Automated Job Hunting & AI Qualification System**  
> HireQuest continuously monitors multiple job platforms, GitHub repositories, and RSS feeds, qualifies opportunities using AI against your preferences, and delivers instant notifications straight to your Telegram.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Automated Setup (Recommended)](#2-automated-setup-recommended)
  - [3. Manual Setup](#3-manual-setup)
  - [4. API Credentials Configuration](#4-api-credentials-configuration)
  - [5. Initialize Database](#5-initialize-database)
- [CLI & Management Commands](#-cli--management-commands)
  - [Full Pipeline Execution](#full-pipeline-execution)
  - [Individual Scrapers](#individual-scrapers)
  - [Pipeline Customization Options](#pipeline-customization-options)
  - [Development & Web Server Commands](#development--web-server-commands)
- [How It Works](#-how-it-works)
  - [Scraping Pipeline Workflow](#scraping-pipeline-workflow)
  - [Data Sources & Risk Matrix](#data-sources--risk-matrix)
  - [Scraping Best Practices & Compliance](#scraping-best-practices--compliance)
- [Adding New Scrapers](#-adding-new-scrapers)
- [Architecture & Design Decisions](#-architecture--design-decisions)
  - [Hybrid Scraping Methodology](#hybrid-scraping-methodology)
  - [Component & Library Choices](#why-this-stack)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🌟 Overview

HireQuest automates the tedious aspects of job hunting. Instead of manually checking multiple boards every day, HireQuest acts as your 24/7 background agent:
1. Aggregates listings across GitHub Issues, RSS feeds, and HTML job boards.
2. Applies heuristics and AI (via Hugging Face Llama models) to classify match relevance.
3. Automatically generates tailored outreach drafts for top-tier matches.
4. Delivers actionable alerts directly to Telegram in real time.

---

## 🚀 Key Features

| Feature | Description |
| :--- | :--- |
| 🔍 **Multi-Source Scraping** | Seamlessly ingests opportunities from GitHub Issues, RemoteOK, We Work Remotely, and RSS feeds. |
| 🤖 **AI-Powered Qualification** | Employs Hugging Face Llama models to analyze job requirements, match skills, and filter non-jobs. |
| 📱 **Instant Telegram Alerts** | Receive immediate push notifications with job summaries and application links for high-quality leads. |
| 🛡️ **Polite & Compliant Scraping** | Built-in robots.txt compliance checking, exponential backoff, and configurable per-domain rate limiting. |
| 📊 **Management Dashboard** | Clean web UI to view, filter, review qualification scores, and track application statuses. |
| 🔄 **Deduplication Engine** | Prevents redundant alerts and duplicate records using persistent external identifiers. |
| ⚡ **Modular Architecture** | Extensible scraper base classes make integrating new job portals straightforward. |

---

## 🛠️ Tech Stack

- **Backend Framework:** Django 5.0 (Python 3.12+)
- **Database:** SQLite (default / development), PostgreSQL-compatible
- **AI & Classification:** Hugging Face Inference API (`meta-llama/Llama-3.2-1B-Instruct`)
- **Scraping & Ingestion:** BeautifulSoup4, Feedparser, Requests, GitHub REST API, Selenium (optional)
- **Notifications:** Telegram Bot API

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Data Ingestion Sources                        │
│   GitHub Issues API   │   Public RSS Feeds   │   Job Board Scrapers    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Data Pipeline & Storage                         │
│   • Duplicate Filtering (external_id)                                  │
│   • Rate Limiting & robots.txt Compliance                              │
│   • Source Management & JobPost Database Persistence                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        AI Qualification Engine                         │
│   • Signal Detection (Filters non-job announcements)                   │
│   • Classification (HIGH / MEDIUM / IGNORE)                            │
│   • Match Scoring & Reasoning Generation                               │
│   • Personalized Outreach / Cover Letter Draft Generation              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Notification & UI Layer                        │
│   • Instant Telegram Push Notifications (HIGH match leads)             │
│   • Django Web Management Dashboard & Admin Interface                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
hirequest/
├── config/                          # Django project configuration
│   ├── settings.py                  # Environment and application settings
│   ├── urls.py                      # Root URL routing
│   ├── wsgi.py                      # WSGI entry point
│   └── asgi.py                      # ASGI entry point
├── core/                            # Core application
│   ├── models.py                    # Data models (Source, JobPost, QualificationScore, etc.)
│   ├── views.py                     # Dashboard views and controllers
│   ├── admin.py                     # Django Admin customizations
│   ├── urls.py                      # App route definitions
│   ├── templates/                   # UI HTML templates
│   │   ├── admin/                   # Custom admin templates
│   │   └── core/                    # Dashboard and job detail views
│   └── management/commands/         # Django CLI management commands
│       ├── run_full_pipeline.py     # Orchestrates all scrapers end-to-end
│       ├── scrape_github.py         # GitHub Issues scraper command
│       ├── scrape_rss.py            # RSS feed scraper command
│       ├── scrape_boards.py         # Job board scraper command
│       ├── poll_and_alert.py        # Background poller & notifier
│       └── validate_all_apis.py     # Health checks for third-party APIs
├── integrations/                    # Scrapers & external API clients
│   ├── base_scraper.py              # Abstract base scraper with rate limiting
│   ├── github_scraper.py            # GitHub Issues API integration
│   ├── rss_scraper.py               # RSS feed parser
│   ├── remoteok_scraper.py          # RemoteOK HTML scraper
│   ├── weworkremotely_scraper.py    # We Work Remotely HTML scraper
│   ├── huggingface_client.py        # Hugging Face AI qualification client
│   └── telegram_client.py           # Telegram notification client
├── jobs/                            # Scheduling & background polling
│   ├── cron.py                      # Cron task definitions
│   └── scraper_poller.py            # Polling orchestrator
├── utils/                           # Shared utility modules
│   ├── ai_service.py                # AI qualification and signal logic
│   ├── signal_detection.py          # Job posting signal rules
│   ├── validators.py                # Credential and input validators
│   └── exceptions.py                # Domain-specific exception definitions
├── docs/                            # In-depth guides
│   ├── ARCHITECTURE.md              # Detailed system architecture and design specification
│   ├── PRODUCTION.md                # Production setup and operations guide
│   └── TESTING.md                   # Comprehensive testing guide
├── requirements.txt                 # Python dependencies
├── manage.py                        # Django CLI entrypoint
└── README.md                        # Project documentation
```

---

## ⚡ Quick Start

### 1. Prerequisites

- Python 3.10+ (Python 3.12 recommended)
- Git
- Active internet connection for API requests and scraping

---

### 2. Automated Setup (Recommended)

Run the automated initialization script to prepare the environment:

```bash
python setup.py
```

This automated helper will:
- Create a Python virtual environment.
- Initialize the required directory tree.
- Generate `.env` from `.env.example`.
- Install all package dependencies from `requirements.txt`.
- Set up initial `.gitignore` rules.

---

### 3. Manual Setup

If you prefer to configure the environment manually:

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment
# On macOS / Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment configuration template
cp .env.example .env
```

---

### 4. API Credentials Configuration

Edit your `.env` file with the required service credentials:

```ini
# --- Django Settings ---
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# --- GitHub API (Optional: increases rate limit from 60 to 5,000 req/hr) ---
GITHUB_TOKEN=ghp_yourGitHubPersonalAccessTokenHere

# --- Telegram Bot (Required for real-time alert notifications) ---
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=your_numeric_telegram_chat_id

# --- Hugging Face API (Required for AI job qualification & drafts) ---
HUGGINGFACE_API_KEY=hf_yourHuggingFaceApiKeyHere
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-1B-Instruct

# --- Pipeline Configuration ---
SCRAPE_INTERVAL_MINUTES=60
MAX_JOBS_PER_SOURCE=20
JOB_MAX_AGE_DAYS=7
JOB_KEYWORDS=python,django,remote,backend,api
```

#### Step-by-Step API Key Setup:

1. **GitHub Personal Access Token (Optional):**
   - Navigate to [GitHub Developer Settings](https://github.com/settings/tokens).
   - Generate a classic or fine-grained token with `public_repo` scope.
   - Saves you from unauthenticated rate limit caps (60/hr vs 5,000/hr).

2. **Telegram Bot Token & Chat ID (Required for alerts):**
   - Open Telegram and search for [@BotFather](https://t.me/botfather).
   - Send `/newbot` and follow prompts to name your bot and receive the token.
   - Start a conversation with your bot by clicking **Start** or sending a message.
   - Obtain your chat ID by querying `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` or messaging [@userinfobot](https://t.me/userinfobot).

3. **Hugging Face API Token (Required for AI features):**
   - Visit [Hugging Face Access Tokens](https://huggingface.co/settings/tokens).
   - Create a read-access token and assign it to `HUGGINGFACE_API_KEY`.

---

### 5. Initialize Database

Run Django migrations and create your administrative user:

```bash
# Apply migrations to initialize SQLite database
python manage.py migrate

# Create an administrator account for dashboard login
python manage.py createsuperuser
```

---

## 💻 CLI & Management Commands

### Full Pipeline Execution

Run the complete pipeline across all configured ingestion channels with qualification and alerting:

```bash
# Run full scraping and qualification pipeline with default limits
python manage.py run_full_pipeline

# Run full pipeline with custom result limits
python manage.py run_full_pipeline --limit 30
```

---

### Individual Scrapers

Target specific sources independently for testing or focused scraping:

```bash
# Scrape only GitHub Issues
python manage.py scrape_github --limit 20

# Scrape only RSS feeds (RemoteOK, WeWorkRemotely)
python manage.py scrape_rss --limit 20

# Scrape only HTML Job Boards (BeautifulSoup)
python manage.py scrape_boards --limit 20
```

---

### Pipeline Customization Options

Fine-tune the pipeline to skip specific providers or optimize throughput:

```bash
# Skip GitHub scraping (useful to avoid consuming API limits)
python manage.py run_full_pipeline --skip-github

# Skip RSS feed parsing
python manage.py run_full_pipeline --skip-rss

# Skip HTML job board scrapers
python manage.py run_full_pipeline --skip-boards

# Combine flags: scrape only GitHub
python manage.py run_full_pipeline --skip-rss --skip-boards
```

---

### Development & Web Server Commands

```bash
# Start the local development web server
python manage.py runserver

# Run Django test suite
python manage.py test

# Verify all external API connections and credentials
python manage.py validate_all_apis

# Send a test alert to Telegram
python manage.py test_telegram_alert

# Create a sample test job to verify end-to-end AI qualification
python manage.py create_test_job
```

---

## 🔍 How It Works

### Scraping Pipeline Workflow

```
1. Ingest Listings ──────► 2. Filter & Deduplicate ──────► 3. AI Qualification ──────► 4. Alert & Archive
   (GitHub, RSS, HTML)        (Check external_id)             (Classify: HIGH/MED)        (Telegram & DB)
```

1. **GitHub Issues Ingestion (API-based):**
   - Queries GitHub's issue search API for keywords: `"paid"`, `"contract"`, `"freelance"`, `"hire"`, `"bounty"`.
   - Filters out non-paid / volunteer postings.
   - Extracts programming languages and repository metadata.

2. **RSS Feed Ingestion (RemoteOK & We Work Remotely):**
   - Parses official, structured RSS/XML feeds.
   - Filters entries matching defined `JOB_KEYWORDS` (e.g., Python, Django).
   - Zero scraping overhead or rate limit penalties.

3. **Job Board Ingestion (HTML & BeautifulSoup):**
   - Scrapes listing pages and follows detail links for complete descriptions.
   - Checks `robots.txt` before fetching and enforces polite delays between requests.

4. **AI Qualification & Signal Engine:**
   - **Signal Detection:** Determines if an item is a genuine job posting versus news/promotions.
   - **Relevance Scoring:** Classifies jobs as `HIGH`, `MEDIUM`, or `IGNORE` based on criteria match.
   - **Drafting:** Automatically writes personalized application pitch drafts for `HIGH` score postings.
   - **Notification:** Dispatches formatted Telegram alerts immediately for high-match opportunities.

---

### Data Sources & Risk Matrix

| Source | Ingestion Type | Risk Level | Rate Limits | Notes & Handling |
| :--- | :--- | :--- | :--- | :--- |
| **GitHub Issues** | REST API | None | 60/hr (5,000/hr with token) | Official API; safe, structured JSON. |
| **RemoteOK RSS** | RSS / XML | None | None | Public feed; fast and reliable. |
| **We Work Remotely RSS** | RSS / XML | None | None | Public feed; fast and reliable. |
| **RemoteOK HTML** | BeautifulSoup | Low | 5 seconds delay per request | Tolerated polite crawling; parses detail HTML. |
| **We Work Remotely HTML** | BeautifulSoup | Low | 3 seconds delay per request | Permissive `robots.txt`; parses detail HTML. |

---

### Scraping Best Practices & Compliance

HireQuest adheres to strict automated scraping ethics and compliance standards:

- ✅ **`robots.txt` Verification:** Verifies permissions before issuing requests to any HTML domain.
- ✅ **Dynamic Rate Limiting:** Enforces configurable inter-request cooldowns (default 3–5 seconds).
- ✅ **Exponential Backoff:** Automatically retries transient failures with progressive backoff delays.
- ✅ **Transparent User-Agent:** Identifies requests with standard, identifiable user-agent headers.
- ✅ **Database Deduplication:** Tracks `external_id` and unique URLs to prevent redundant processing.

```ini
# Recommended .env production tuning:
SCRAPE_INTERVAL_MINUTES=60   # Frequency of scheduled runs
MAX_JOBS_PER_SOURCE=20       # Cap results per source per cycle
JOB_MAX_AGE_DAYS=7           # Ignore postings older than 7 days
```

---

## 🧩 Adding New Scrapers

HireQuest's modular architecture makes adding new job boards straightforward:

### Step 1: Create Scraper Class
Create a new file in `integrations/` inheriting from `BaseScraper`:

```python
# integrations/custom_board_scraper.py
from integrations.base_scraper import BaseScraper

class CustomBoardScraper(BaseScraper):
    def __init__(self):
        super().__init__(base_url='https://customboard.example.com', delay=5.0)

    def scrape_listings(self, limit=20):
        # 1. Fetch listing page
        # 2. Extract job data dictionaries
        # 3. Return structured list of job dicts:
        #    [{ 'title': ..., 'company': ..., 'url': ..., 'external_id': ... }]
        return []
```

### Step 2: Register in Poller
Add the new scraper instance to `jobs/scraper_poller.py`:

```python
from integrations.custom_board_scraper import CustomBoardScraper

scrapers = {
    'custom_board': CustomBoardScraper(),
}
```

### Step 3: Register Source in Database
Add the source via Django Admin or shell:

```python
from core.models import Source

Source.objects.create(
    type=Source.JOB_BOARD,
    identifier='custom_board',
    name='Custom Job Board',
    scraper_type='beautifulsoup',
    base_url='https://customboard.example.com',
    is_active=True,
)
```

---

## 🏛️ Architecture & Design Decisions

> 📖 **Full Specification:** For complete architectural diagrams, ERD schemas, data pipeline specifications, and design patterns, see the [HireQuest Architecture Guide](docs/ARCHITECTURE.md).

### Hybrid Scraping Methodology

| Approach | Advantages | Tradeoffs & Mitigations |
| :--- | :--- | :--- |
| **API + RSS + HTML Hybrid** | Multi-channel coverage, fast ingestion via RSS/API, rich descriptions via HTML. | HTML layouts can change over time; handled via isolated scrapers and robust exception logging. |

### Why This Stack?

- **Django 5.0:** Provides a battle-tested ORM, admin dashboard out of the box, CLI management command framework, and secure authentication.
- **BeautifulSoup4:** Lightweight, fast, and resource-efficient for static HTML parsing without the overhead of a headless browser.
- **Hugging Face API:** Offers cost-effective, high-accuracy inference with state-of-the-art open models (Llama 3.2) without requiring local GPU infrastructure.
- **Feedparser:** Robust XML/RSS parsing resilient against malformed feed schemas.

---

## ❓ Troubleshooting & FAQ

### 1. GitHub API Rate Limit Exceeded
- **Symptom:** `403 API rate limit exceeded` in scraper logs.
- **Solution:** Add a valid `GITHUB_TOKEN` to `.env`. This raises your limit from 60 requests/hr to 5,000 requests/hr.

### 2. Hugging Face Inference Latency on First Call
- **Symptom:** First qualification request takes 30–60 seconds.
- **Solution:** This is normal cold-start behavior while the Hugging Face serverless container loads the model weights. Subsequent requests respond within seconds.

### 3. Telegram Alerts Not Received
- **Symptom:** No messages appear in your Telegram chat.
- **Solution:**
  1. Ensure you have pressed **Start** or sent a message to your bot first.
  2. Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`.
  3. Execute `python manage.py test_telegram_alert` to isolate connectivity.

### 4. Scrapers Return 0 Jobs
- **Symptom:** Scraper runs successfully but finds no listings.
- **Solution:**
  1. Verify the remote site's HTML layout has not changed.
  2. Check your `JOB_KEYWORDS` filter in `.env` (too strict keywords may filter all results).
  3. Run with verbose output: `python manage.py scrape_boards --verbosity 2`.

---

## 🗺️ Roadmap

### Version 1.0 (Current)
- [x] GitHub Issues API scraper
- [x] RSS feed integration (RemoteOK, We Work Remotely)
- [x] HTML scrapers with rate limiting & `robots.txt` compliance
- [x] AI job qualification and signal detection (Llama 3.2)
- [x] Automated cover letter / outreach draft generation
- [x] Real-time Telegram alert delivery
- [x] Django Admin and Dashboard interface

### Version 2.0 (Planned)
- [ ] Headless browser support (Playwright / Selenium) for JavaScript-rendered sites (Wellfound, LinkedIn)
- [ ] PostgreSQL / vector database integration for semantic resume matching
- [ ] Celery + Redis automated task scheduling
- [ ] One-click application submission helpers
- [ ] Analytics dashboard for application tracking and response rates

---

## 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).

---

**HireQuest** — Built with Django, BeautifulSoup, and AI.
