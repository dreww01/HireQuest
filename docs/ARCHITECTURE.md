# System Architecture & Technical Design - HireQuest 🏛️

> **Comprehensive architectural specification of the HireQuest automated job hunting, qualification, and notification system.**

---

## 📑 Table of Contents

- [1. Executive Summary & Core Mission](#1-executive-summary--core-mission)
- [2. High-Level System Architecture](#2-high-level-system-architecture)
- [3. Core Architectural Patterns](#3-core-architectural-patterns)
- [4. Layered Component Decomposition](#4-layered-component-decomposition)
  - [4.1 Configuration & Application Shell (`config/`)](#41-configuration--application-shell-config)
  - [4.2 Domain Data Model & Persistence (`core/models.py`)](#42-domain-data-model--persistence-coremodelspy)
  - [4.3 Ingestion & Hybrid Scraping Engine (`integrations/`, `jobs/`)](#43-ingestion--hybrid-scraping-engine-integrations-jobs)
  - [4.4 AI Qualification & Signal Engine (`utils/ai_service.py`)](#44-ai-qualification--signal-engine-utilsai_servicepy)
  - [4.5 Event-Driven Signals & Alerting (`core/signals.py`, `integrations/telegram_client.py`)](#45-event-driven-signals--alerting-coresignalspy-integrationstelegram_clientpy)
  - [4.6 Web Presentation & API Layer (`core/views.py`, `core/templates/`)](#46-web-presentation--api-layer-coreviewspy-coretemplates)
  - [4.7 CLI & Automation Layer (`core/management/commands/`)](#47-cli--automation-layer-coremanagementcommands)
- [5. Detailed Data Model (ERD)](#5-detailed-data-model-erd)
- [6. End-to-End Data Processing Pipelines](#6-end-to-end-data-processing-pipelines)
  - [6.1 Full Ingestion to Notification Pipeline](#61-full-ingestion-to-notification-pipeline)
  - [6.2 AI Signal Detection & Qualification Logic](#62-ai-signal-detection--qualification-logic)
  - [6.3 Tailored Outreach & Cover Letter Generation](#63-tailored-outreach--cover-letter-generation)
- [7. Scraping Engine & Compliance Subsystem](#7-scraping-engine--compliance-subsystem)
  - [7.1 `robots.txt` Parsing & Compliance](#71-robotstxt-parsing--compliance)
  - [7.2 Dynamic Rate Limiting & Exponential Backoff](#72-dynamic-rate-limiting--exponential-backoff)
  - [7.3 Deduplication & Source Tracking](#73-deduplication--source-tracking)
- [8. Error Handling & Graceful Degradation](#8-error-handling--graceful-degradation)
- [9. Extensibility Architecture](#9-extensibility-architecture)
  - [9.1 Adding a New Ingestion Source](#91-adding-a-new-ingestion-source)
  - [9.2 Adding Alternative AI Models / Providers](#92-adding-alternative-ai-models--providers)
  - [9.3 Adding New Notification Channels](#93-adding-new-notification-channels)
- [10. Technology Stack Rationale](#10-technology-stack-rationale)

---

## 1. Executive Summary & Core Mission

**HireQuest** is an intelligent, automated background agent designed to eliminate manual job searching. The system autonomously aggregates freelance, contract, and full-time opportunities across disparate channels (GitHub Issues, RSS/XML feeds, and HTML job boards), filters noise through a multi-tier AI qualification engine, generates personalized application pitch drafts and cover letters, and delivers real-time actionable alerts via Telegram.

### Key Capabilities
- **Multi-Source Ingestion:** Ingests jobs from GitHub Issues REST API, structured RSS/XML feeds (RemoteOK, WeWorkRemotely, Remotive, StackOverflow), and static HTML scrapers.
- **Ethical & Polite Scraping:** Programmatic `robots.txt` enforcement, configurable inter-request rate limiting, exponential backoff retries, and user-agent attribution.
- **Multi-Tier AI Qualification:** Two-step evaluation (Job Signal Detection $\rightarrow$ Keyword/LLM Relevance Scoring) using Hugging Face serverless inference (`meta-llama/Llama-3.2-1B-Instruct`) with robust heuristic fallbacks.
- **Automated Outreach Generation:** Context-aware generation of GitHub issue comments, outreach pitches, and full formal cover letters customized to candidate profile attributes.
- **Event-Driven Alerting:** Django ORM post-save signals trigger instantaneous Telegram push notifications with deep links to the management dashboard.
- **Centralized Dashboard:** Modern Django web dashboard with Unfold Admin for pipeline monitoring, job application status tracking (`PENDING`, `APPLIED`, `IGNORED`), and full-text searching.

---

## 2. High-Level System Architecture

The following diagram illustrates the end-to-end data flow through HireQuest:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             DATA INGESTION SOURCES                               │
│  ┌────────────────────────┐ ┌────────────────────────┐ ┌──────────────────────┐  │
│  │   GitHub Issues API    │ │    Public RSS Feeds    │ │  HTML Job Boards     │  │
│  │   (REST / Search API)  │ │ (RemoteOK / WWR / etc) │ │   (BeautifulSoup)    │  │
│  └───────────┬────────────┘ └───────────┬────────────┘ └──────────┬───────────┘  │
└──────────────┼──────────────────────────┼─────────────────────────┼──────────────┘
               │                          │                         │
               ▼                          ▼                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         SCRAPING & INGESTION SUBSYSTEM                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ BaseScraper Interface                                                      │  │
│  │  • robots.txt Validation (`RobotFileParser`)                                │  │
│  │  • Dynamic Rate Limiting (`_rate_limit`)                                   │  │
│  │  • Exponential Backoff Retries (`fetch_html`)                              │  │
│  │  • HTML Sanitization & Tag Decomposition (`_clean_html`)                   │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────────┘
                                       │ Standardized Job Dictionaries
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        PERSISTENCE & DEDUPLICATION LAYER                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ Django ORM / SQLite / PostgreSQL                                           │  │
│  │  • Source Management (`Source` table)                                      │  │
│  │  • Deduplication by unique `external_id` and unique `[type, identifier]`   │  │
│  │  • Job persistence with lifecycle state (`status=NEW`, `user_status`)      │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────────┘
                                       │ New JobPost Instance
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           AI QUALIFICATION ENGINE                                │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ Stage 1: Signal Detection (`detect_job_signal`)                             │  │
│  │  • Hugging Face LLM binary classifier (or Heuristic Keyword Fallback)      │  │
│  │  • Filters out non-job announcements, spam, and promotional material       │  │
│  └───────────────────────────────────┬────────────────────────────────────────┘  │
│                                      │ Legitimate Job Signal
│                                      ▼
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ Stage 2: Match Qualification (`qualify_job`)                               │  │
│  │  • Negative filtering (Senior-level exclusion, scam heuristics)            │  │
│  │  • Positive scoring (High-value vs Medium-value tech & budget indicators)  │  │
│  │  • Outputs `QualificationScore` (`HIGH`, `MEDIUM`, `IGNORE`)               │  │
│  └───────────────────────────────────┬────────────────────────────────────────┘  │
│                                      │ HIGH / MEDIUM match
│                                      ▼
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ Stage 3: Outreach Draft Generation (`generate_draft_message`)              │  │
│  │  • Auto-generates tailored pitch & formal cover letter (`DraftMessage`)    │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────────┘
                                       │ Post-Save Signal Trigger
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          NOTIFICATION & SIGNAL LAYER                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ `core/signals.py` (`@receiver(post_save, sender=QualificationScore)`)      │  │
│  │  • Telegram Bot API Client (`TelegramClient`)                              │  │
│  │  • Dispatches formatted Markdown alert with job summary & dashboard URL    │  │
│  │  • Records `AlertStatus` (prevents re-alerts) & updates `status=ALERTED`   │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      MANAGEMENT DASHBOARD & USER INTERFACE                       │
│  ┌──────────────────────────────────────────┐ ┌───────────────────────────────┐  │
│  │ Web Dashboard (`core/views.py`)          │ │ Django Unfold Admin Panel     │  │
│  │  • Filter by status & qualification      │ │  • Full CRUD on Sources & Jobs│  │
│  │  • Review cover letter drafts            │ │  • Model admin customization  │  │
│  │  • Update user status (APPLIED/IGNORED)  │ │  • System status inspection   │  │
│  └──────────────────────────────────────────┘ └───────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Architectural Patterns

HireQuest utilizes established software architecture patterns to maintain separation of concerns, testability, and resilience:

1. **Layered (N-Tier) Architecture:** Clean separation between Ingestion, Persistence, Business Logic (AI qualification), Event Dispatching, and Presentation.
2. **Template Method & Strategy Pattern (`BaseScraper`):** Defines the invariant skeleton of polite web scraping (robots check, rate limiting, error retry) while delegating board-specific parsing to concrete subclasses.
3. **Event-Driven Observer Pattern (Django Signals):** Decouples qualification logic from alert dispatching. When a `QualificationScore` is persisted, decoupled receivers evaluate alert thresholds and dispatch notifications asynchronously.
4. **Adapter / Client Facade Pattern (`HuggingFaceClient`, `TelegramClient`, `GitHubScraper`):** Wraps external third-party SDKs and REST endpoints behind stable internal interfaces with unified error handling and validation.
5. **Graceful Degradation / Fallback Pattern:** When external AI inference services or notification APIs are unreachable or unconfigured, the system automatically falls back to deterministic rule-based keyword heuristics and local templating without interrupting pipeline execution.

---

## 4. Layered Component Decomposition

```
hirequest/
├── config/                          # Django project configuration & settings
│   ├── settings.py                  # Core configuration, environment loading, logging
│   ├── urls.py                      # Root URL dispatching
│   ├── wsgi.py                      # WSGI web server entrypoint
│   └── asgi.py                      # ASGI async server entrypoint
├── core/                            # Core domain application
│   ├── models.py                    # Domain models (Source, JobPost, QualificationScore, etc.)
│   ├── views.py                     # Dashboard views, CBVs, and AJAX endpoints
│   ├── signals.py                   # Event receivers for qualification & alerting
│   ├── admin.py                     # Unfold admin registration and customizations
│   ├── urls.py                      # Route definitions for web dashboard
│   ├── templates/                   # UI HTML templates (Tailwind-compatible)
│   └── management/commands/         # CLI pipeline commands
├── integrations/                    # External API integrations & scrapers
│   ├── base_scraper.py              # Abstract scraper with rate limiting and robots.txt
│   ├── github_scraper.py            # GitHub Issues search API scraper
│   ├── rss_scraper.py               # Feedparser RSS/XML ingestion
│   ├── remoteok_scraper.py          # RemoteOK API and HTML scraper
│   ├── weworkremotely_scraper.py    # We Work Remotely scraper
│   ├── huggingface_client.py        # Hugging Face AI inference client
│   └── telegram_client.py           # Telegram notification bot client
├── jobs/                            # Background processing and scheduling
│   ├── scraper_poller.py            # Master scraping poller orchestrator
│   └── cron.py                      # Django-cron task definitions
├── utils/                           # Shared utility services & domain logic
│   ├── ai_service.py                # AI qualification and signal logic
│   ├── signal_detection.py          # Job posting signal rules
│   ├── validators.py                # Credential and input validators
│   └── exceptions.py                # Domain exception hierarchy
└── docs/                            # In-depth technical guides
```

### 4.1 Configuration & Application Shell (`config/`)
- **`config/settings.py`:** Utilizes `django-environ` to load configuration from `.env`. Configures the database (SQLite for local/test, PostgreSQL-ready), installed apps (including `unfold` for modern UI), template paths, logging handlers (console and rotating file), and credentials validation on startup (`validate_api_credentials_on_startup`).
- **`config/urls.py`:** Routes top-level paths to `admin/` and includes `core.urls`.

### 4.2 Domain Data Model & Persistence (`core/models.py`)
Encapsulates the core entities, their lifecycle states, and relational constraints:
- **`Source`:** Represents an ingestion endpoint (GitHub search, RSS feed URL, or scraped job board). Enforces unique composite constraint `['type', 'identifier']`.
- **`JobPost`:** The canonical job listing record. Stores normalized fields (`title`, `company_name`, `job_type`, `location`, `skills_tags`, `body`, `url`, `application_link`, `timestamp`), raw HTML, lifecycle state (`status`: `NEW`, `ALERTED`, `SENT`, `CLOSED`), and user action state (`user_status`: `PENDING`, `APPLIED`, `IGNORED`).
- **`QualificationScore`:** 1-to-1 relationship with `JobPost`. Stores the AI signal flag (`is_job_signal`), confidence score ($0.0 \dots 1.0$), classification (`HIGH`, `MEDIUM`, `IGNORE`), and descriptive AI reasoning.
- **`DraftMessage`:** 1-to-1 relationship with `JobPost`. Stores generated short-form outreach messages and full-length formal cover letters for the specified target platform (`GITHUB_COMMENT`, `DIRECT_MESSAGE`, `COVER_LETTER`).
- **`AlertStatus`:** 1-to-1 relationship with `JobPost`. Records Telegram message ID, dispatch timestamp, and acknowledgment flag to ensure idempotency.

### 4.3 Ingestion & Hybrid Scraping Engine (`integrations/`, `jobs/`)
- **`BaseScraper` (`integrations/base_scraper.py`):** Abstract base class encapsulating:
  - `urllib.robotparser.RobotFileParser` integration.
  - Inter-request time tracking and rate limit delay sleeping.
  - Exponential backoff retry loops on transient HTTP failures.
  - HTML cleanup and text extraction.
- **`GitHubScraper` (`integrations/github_scraper.py`):** Scrapes GitHub Issues via the GitHub Search API (`/search/issues`). Queries with positive paid keywords (`paid`, `contract`, `freelance`, `bounty`), filters out unpaid/volunteer keywords (`volunteer`, `no budget`, `unpaid`), extracts tech stack keywords from bodies and labels, and parses repository metadata.
- **`RSSJobScraper` (`integrations/rss_scraper.py`):** Ingests structured XML feeds (RemoteOK, WeWorkRemotely, Remotive, StackOverflow) using `feedparser`. Normalizes unstructured feed tags, descriptions, and timestamps into canonical job dictionaries.
- **`RemoteOKScraper` (`integrations/remoteok_scraper.py`):** Directly queries the RemoteOK JSON endpoint (`https://remoteok.com/api`) with fallback HTML detail crawling.
- **`WeWorkRemotelyScraper` (`integrations/weworkremotely_scraper.py`):** Scrapes We Work Remotely programming listings and fetches full job descriptions from detail pages.
- **`ScraperPollerJob` (`jobs/scraper_poller.py`):** Static orchestrator methods (`poll_github`, `poll_rss_feeds`, `poll_job_boards`) that coordinate fetching, deduplicating against the database, triggering qualification, and generating outreach drafts.

### 4.4 AI Qualification & Signal Engine (`utils/ai_service.py`)
- **`detect_job_signal(job_post)`:** Determines if a scraped listing represents a genuine hiring opportunity versus spam, news, or promotional announcements. Calls Hugging Face Llama 3.2 model with a structured prompt, parsing `IS_JOB_SIGNAL`, `CONFIDENCE`, and `REASONING`. Falls back to keyword density heuristics if AI inference is unavailable.
- **`qualify_job(job_post)`:** Analyzes the listing content to score alignment with the user's target stack:
  - Immediately rejects postings requiring senior-level expertise (if configured) or containing spam indicators.
  - Scores high-value indicators (Django, FastAPI, PostgreSQL, long-term, competitive salary, budget mentions) and medium-value indicators (Python, REST, automation, remote).
  - Categorizes as `HIGH`, `MEDIUM`, or `IGNORE` with confidence and detailed reasoning.
- **`generate_draft_message(job_post, qualification)`:** Contextually drafts an application message tailored to the source platform (concise comment for GitHub, structured cover letter for job boards) using candidate profile settings (`USER_PROFILE`).

### 4.5 Event-Driven Signals & Alerting (`core/signals.py`, `integrations/telegram_client.py`)
- **`core/signals.py`:** Listens to `post_save` on `QualificationScore`. When a record is created with `classification` of `HIGH` or `MEDIUM`, it checks if an alert already exists, initializes `TelegramClient`, formats the message with deep links, sends the alert, records `AlertStatus`, and transitions `JobPost.status` to `ALERTED`.
- **`TelegramClient` (`integrations/telegram_client.py`):** Encapsulates `python-telegram-bot` asynchronous dispatch, markdown character escaping (`_escape_markdown`), and error classification.

### 4.6 Web Presentation & API Layer (`core/views.py`, `core/templates/`)
- **`JobListView`:** Class-based view displaying paginated job listings with multi-attribute filtering (by status, classification, search query), JSON serialization for dynamic frontend filtering, and custom context data.
- **`JobDetailView`:** Displays complete job description, source metadata, AI qualification score, confidence, reasoning, and pre-generated cover letter drafts.
- **AJAX Endpoints (`update_job_status`, `update_user_status`, `delete_job`):** Lightweight JSON endpoints for updating job workflow states directly from the web interface without page reloads.

### 4.7 CLI & Automation Layer (`core/management/commands/`)
- **`run_full_pipeline`:** Comprehensive CLI runner executing GitHub, RSS, and Job Board scrapers end-to-end with summary statistics.
- **`scrape_github`, `scrape_rss`, `scrape_boards`:** Granular scraper execution commands.
- **`poll_and_alert`:** Continuous poller daemon.
- **`validate_all_apis`:** Diagnostic tool validating credentials and connectivity for GitHub, Hugging Face, and Telegram.
- **`test_telegram_alert`:** Dispatches a test message to verify Telegram bot setup.
- **`create_test_job`:** Interactive CLI test harness that creates synthetic postings and executes the qualification pipeline step-by-step.

---

## 5. Detailed Data Model (ERD)

The database schema is organized around the `JobPost` entity:

```
┌────────────────────────────────────────────────────────┐
│                        Source                          │
├────────────────────────────────────────────────────────┤
│ id (PK)                 : BigAutoField                 │
│ type                    : CharField ('job_board', etc) │
│ identifier              : CharField                    │
│ name                    : CharField                    │
│ is_active               : BooleanField                 │
│ scraper_type            : CharField                    │
│ base_url                : URLField                     │
│ rate_limit_seconds      : IntegerField (default=5)     │
│ created_at              : DateTimeField                │
└───────────────────────────┬────────────────────────────┘
                            │ 1
                            │
                            │ N
┌───────────────────────────▼────────────────────────────┐
│                       JobPost                          │
├────────────────────────────────────────────────────────┤
│ id (PK)                 : BigAutoField                 │
│ source (FK)             : ForeignKey(Source)           │
│ external_id (UQ)        : CharField                    │
│ title                   : CharField(500)               │
│ company_name            : CharField(255)               │
│ job_type                : CharField(100)               │
│ location                : CharField(255)               │
│ skills_tags             : TextField                    │
│ body                    : TextField                    │
│ raw_html                : TextField                    │
│ author                  : CharField(255)               │
│ url                     : URLField(500)                │
│ application_link        : URLField(1000)               │
│ timestamp               : DateTimeField                │
│ status                  : CharField (NEW/ALERTED/etc)  │
│ user_status             : CharField (PENDING/APPLIED)  │
│ created_at              : DateTimeField                │
│ updated_at              : DateTimeField                │
└───────┬───────────────────┬────────────────────┬───────┘
        │ 1                 │ 1                  │ 1
        │                   │                    │
        │ 1 (OneToOne)      │ 1 (OneToOne)       │ 1 (OneToOne)
┌───────▼──────────────┐ ┌──▼──────────────────┐ ┌▼─────────────────────┐
│  QualificationScore  │ │    DraftMessage     │ │     AlertStatus      │
├──────────────────────┤ ├─────────────────────┤ ├──────────────────────┤
│ id (PK)              │ │ id (PK)             │ │ id (PK)              │
│ job_post (FK, UQ)    │ │ job_post (FK, UQ)   │ │ job_post (FK, UQ)    │
│ is_job_signal (Bool) │ │ content (TextField) │ │ sent_at (DateTime)   │
│ confidence (Float)   │ │ platform (CharField) │ │ telegram_message_id  │
│ classification (Enum)│ │ cover_letter (Text) │ │ acknowledged (Bool)  │
│ reasoning (TextField)│ │ created_at (Date)   │ └──────────────────────┘
│ created_at (DateTime)│ └─────────────────────┘
└──────────────────────┘
```

---

## 6. End-to-End Data Processing Pipelines

### 6.1 Full Ingestion to Notification Pipeline

```
[CLI / Cron Poller]
       │
       ▼
[ScraperPollerJob]
       │
       ├─► 1. Query Sources (GitHub / RSS / HTML Boards)
       │         │
       │         ▼
       ├─► 2. Ingest & Normalize Listing Data Dictionary
       │         │
       │         ▼
       ├─► 3. JobPost.objects.get_or_create(external_id=...)
       │         │
       │         ├── If exists ──► Skip (Deduplication)
       │         └── If new ────► Persist with status='new'
       │                                 │
       │                                 ▼
       ├─► 4. Signal Detection (detect_job_signal)
       │         │
       │         ├── If NOT signal ──► Skip further processing
       │         └── If IS signal ───► Proceed to Qualification
       │                                 │
       │                                 ▼
       ├─► 5. AI Qualification (qualify_job)
       │         │
       │         ▼
       │   Create QualificationScore record
       │         │
       │         ├── If 'high' ──────► generate_draft_message() ──► Create DraftMessage
       │         └── If 'medium' ────► (Optional draft creation)
       │
       ▼
[Django Signal: post_save on QualificationScore]
       │
       ▼
[alert_high_quality_job receiver]
       │
       ├── Check if alert already sent
       ├── Format markdown message with job summary & dashboard link
       ├── TelegramClient.send_alert()
       ├── Create AlertStatus record
       └── Update JobPost.status = 'alerted'
```

### 6.2 AI Signal Detection & Qualification Logic

The qualification subsystem enforces strict filtering through a multi-stage funnel:

```
                             [Scraped Raw Text]
                                     │
                                     ▼
                      ┌──────────────────────────────┐
                      │    Stage 1: Signal Check     │
                      │  (LLM Prompt / HF Inference) │
                      └──────────────┬───────────────┘
                                     │
                    Is Genuine Job Hiring Opportunity?
                                     │
                       ┌─────────────┴─────────────┐
                       ▼                           ▼
                     [NO]                        [YES]
                   Discard                         │
                                                   ▼
                                    ┌──────────────────────────────┐
                                    │    Stage 2: Negative Gate    │
                                    │  • Check 'senior' exclusion  │
                                    │  • Check spam indicator list │
                                    └──────────────┬───────────────┘
                                                   │
                                      Passes Negative Checks?
                                                   │
                                     ┌─────────────┴─────────────┐
                                     ▼                           ▼
                                   [NO]                        [YES]
                            Score as 'IGNORE'                    │
                                                                 ▼
                                                  ┌──────────────────────────────┐
                                                  │   Stage 3: Weighted Match    │
                                                  │ • High indicators (Django,   │
                                                  │   FastAPI, Postgres, budget) │
                                                  │ • Medium indicators (Python, │
                                                  │   API, automation, remote)   │
                                                  └──────────────┬───────────────┘
                                                                 │
                                     ┌───────────────────────────┼───────────────────────────┐
                                     ▼                           ▼                           ▼
                                ┌─────────┐                 ┌──────────┐                ┌─────────┐
                                │  HIGH   │                 │  MEDIUM  │                │ IGNORE  │
                                └─────────┘                 └──────────┘                └─────────┘
```

### 6.3 Tailored Outreach & Cover Letter Generation

When a job receives a qualifying score (`HIGH` or `MEDIUM`), `generate_draft_message` constructs customized responses:

1. **Context Extraction:** Combines job title, description extract, source channel, and candidate profile attributes (defined in `settings.USER_PROFILE`).
2. **Platform Specialization:**
   - **GitHub Issues:** Produces concise, direct technical comments addressing the repository owner directly.
   - **RSS / Job Boards:** Produces a formal 300–400 word structured cover letter including formal greeting, technical alignment, and call-to-action.
3. **Fallback Generation:** If LLM inference is disabled or errors occur, deterministic templates populate the `DraftMessage` record so the user never faces empty outreach drafts.

---

## 7. Scraping Engine & Compliance Subsystem

HireQuest incorporates industry-standard defensive scraping mechanisms within `integrations/base_scraper.py`.

### 7.1 `robots.txt` Parsing & Compliance
Before any HTML request is dispatched, `BaseScraper._init_robots_parser` loads and parses the target domain's `/robots.txt` via Python's `urllib.robotparser.RobotFileParser`. The `can_fetch(url)` method verifies permission for User-Agent `*`. If disallowed, the request is aborted and logged.

### 7.2 Dynamic Rate Limiting & Exponential Backoff
- **Inter-Request Cooldown:** `BaseScraper._rate_limit()` tracks `self.last_request_time`. If elapsed time is less than `rate_limit_seconds` (default: 3–5 seconds), execution sleeps for the exact remaining duration.
- **Exponential Backoff:** If an HTTP request fails (`4xx`, `5xx`, connection error), `BaseScraper.fetch_html()` retries up to `max_retries` (default: 3) with backoff delays of $2^{\text{attempt}}$ seconds ($1s, 2s, 4s$).

### 7.3 Deduplication & Source Tracking
Every scraper assigns a deterministic, platform-prefixed `id` (e.g., `github_123456`, `remoteok_98765`, `wwr_45678`). Before executing heavy operations (AI analysis or detail page fetching), `JobPost.objects.get_or_create(external_id=...)` checks the database. Existing records are skipped immediately, preventing redundant AI inference costs and duplicate alerts.

---

## 8. Error Handling & Graceful Degradation

HireQuest implements a centralized exception hierarchy in `utils/exceptions.py`:

```
HireQuestException (Base)
├── ConfigurationError
│   ├── MissingAPIKeyError
│   └── InvalidAPIKeyError
├── IngestionError
│   ├── ScraperError
│   └── RSSFeedError
├── APIConnectionError
└── QualificationError
```

### Fault Tolerance Invariants
- **Missing API Credentials:** When `GITHUB_TOKEN`, `HUGGINGFACE_API_KEY`, or `TELEGRAM_BOT_TOKEN` are omitted in `.env`, the startup validator (`validate_api_credentials_on_startup`) logs actionable setup instructions. The pipeline continues running, utilizing unauthenticated public access or fallback heuristics.
- **AI Service Outages / Cold Starts:** Serverless LLM timeouts or 503 cold-start errors are caught within `detect_job_signal` and `qualify_job`, triggering local rule-based keyword matchers with descriptive fallback logs.
- **Scraping Failures:** If a single job board changes its DOM structure or returns 500 errors, the exception is isolated to that source loop, allowing all other scrapers to complete successfully.

---

## 9. Extensibility Architecture

HireQuest is architected for modular extension without modifying existing core logic:

### 9.1 Adding a New Ingestion Source
1. **Subclass `BaseScraper`:** Create `integrations/newboard_scraper.py` implementing `scrape_listings(limit)` and returning standardized job dictionaries.
2. **Register in Poller:** Add the scraper instance to `ScraperPollerJob.poll_job_boards()` in `jobs/scraper_poller.py`.
3. **Register Source Entity:** Add the source record to `Source.objects` with appropriate `rate_limit_seconds` and `base_url`.

### 9.2 Adding Alternative AI Models / Providers
To switch from Hugging Face to OpenAI, Anthropic, or local Ollama:
1. Create a client wrapper in `integrations/` adhering to the `query(prompt, max_tokens, temperature)` signature.
2. Update `utils/ai_service.py` to instantiate the new client based on configuration settings.

### 9.3 Adding New Notification Channels
To dispatch alerts to Discord, Slack, or Email in addition to Telegram:
1. Implement the client in `integrations/` (e.g. `discord_client.py`).
2. Attach a new receiver function in `core/signals.py` listening to `post_save` on `QualificationScore`.

---

## 10. Technology Stack Rationale

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | Django 5.0 (Python 3.12+) | Provides a mature ORM, built-in admin dashboard, CLI management commands, robust migration framework, and security protections out of the box. |
| **Admin Interface** | Django Unfold | Modern, responsive Tailwind-styled admin dashboard for managing scraped leads and inspecting AI reasoning. |
| **HTML Scraping** | BeautifulSoup4 + Requests | Lightweight, fast, and resource-efficient for static HTML parsing without headless browser memory overhead. |
| **Feed Ingestion** | Feedparser | Battle-tested XML/RSS parser capable of handling non-standard feed dialects and encoding quirks. |
| **AI Inference** | Hugging Face Hub (`Llama-3.2-1B-Instruct`) | Cost-effective, high-accuracy serverless LLM inference without requiring dedicated GPU infrastructure. |
| **Push Notifications**| `python-telegram-bot` | Instant mobile/desktop push delivery with rich markdown support and zero messaging fees. |
| **Task Scheduling** | `django-cron` | Lightweight in-process or cron-driven task scheduling without mandatory Celery/Redis dependencies for minimal deployments. |
| **Testing** | `pytest` + `pytest-django` | Fast, deterministic test execution with fixture isolation and comprehensive coverage. |

---

**Related Documentation:**
- [Main Project README](../README.md) — Quick start, setup instructions, and CLI command reference.
- [Production Run Guide](PRODUCTION.md) — Production operations, scheduling, and logging.
- [Testing Guide](TESTING.md) — Scraper validation matrices and test suite workflows.
