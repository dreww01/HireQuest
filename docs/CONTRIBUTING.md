# Contributing to HireQuest

Thank you for contributing to HireQuest! This document outlines guidelines, conventions, development workflows, and an architectural quick reference for contributors.

---

## 📋 Table of Contents

1. [Branch Naming Convention](#branch-naming-convention)
2. [Commit Message Convention](#commit-message-convention)
3. [Testing & Verification Commands](#testing--verification-commands)
4. [Architecture Quick-Reference](#architecture-quick-reference)
5. [Development Workflow](#development-workflow)
6. [Related Documentation](#related-documentation)

---

## Branch Naming Convention

All feature, bugfix, and documentation branches should adhere to the following naming format:

```text
dsh/<issue-id>
```

### Examples
- `dsh/ORC-5`
- `dsh/ORC-12`
- `dsh/fix-rss-parser`

Keep branch names focused on a single issue or unit of work.

---

## Commit Message Convention

HireQuest follows the **Conventional Commits** specification. Commit messages must be structured as follows:

```text
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

### Allowed Types
- `feat`: A new feature or capability
- `fix`: A bug fix
- `docs`: Documentation changes only
- `test`: Adding or correcting tests
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Code change that improves performance
- `chore`: Maintenance tasks, dependency updates, build/tooling changes

### Examples
- `feat(integrations): add support for Remotive job board scraper`
- `fix(rss): handle malformed feed timestamps gracefully`
- `docs: add architecture and contributing quick-reference`
- `test(models): add unit tests for QualificationScore status transitions`

---

## Testing & Verification Commands

All changes must be verified using the automated test suite before opening a pull request.

### Running Tests

```bash
# Run full test suite with verbose output using uv (Recommended)
uv run pytest -v

# Run full test suite via Django test runner
python manage.py test

# Run a specific test file
uv run pytest tests/test_models.py -v
uv run pytest tests/test_integrations.py -v
uv run pytest tests/test_signal_detection.py -v

# Run a single test class or method
uv run pytest tests/test_signal_detection.py::TestSignalDetector -v
uv run pytest tests/test_signal_detection.py::TestSignalDetector::test_classify_job_high -v
```

### Verification Criteria
- 100% test pass rate (`uv run pytest -v` with zero failures and zero regressions).
- Hermetic test execution with proper mocking for external HTTP APIs and services.
- Clean code with no unresolved lint or runtime warnings.

---

## Architecture Quick-Reference

HireQuest is an automated job search, signal qualification, and notification system built on Django, HuggingFace AI, and Telegram.

### Project Layout

```text
hirequest/
├── config/                  # Django project configuration & settings
│   ├── settings.py          # Application configuration and environment settings
│   ├── urls.py              # Root URL routing configuration
│   ├── wsgi.py              # WSGI entry point
│   └── asgi.py              # ASGI entry point
├── core/                    # Core Django application
│   ├── models.py            # Data models (Source, JobPost, QualificationScore, etc.)
│   ├── views.py             # Dashboard UI views and endpoints
│   ├── admin.py             # Django admin interface configuration
│   └── management/commands/ # CLI management commands
│       ├── run_full_pipeline.py  # Full scraping & qualification pipeline
│       ├── scrape_github.py      # GitHub Issues scraping command
│       ├── scrape_rss.py         # RSS feeds scraping command
│       └── scrape_boards.py      # Job board scraping command
├── integrations/            # External scrapers & API clients
│   ├── base_scraper.py      # Base scraper class with rate-limiting & session handling
│   ├── github_scraper.py    # GitHub Issues search API client
│   ├── rss_scraper.py       # RSS feed parser for job feeds
│   ├── remoteok_scraper.py  # RemoteOK BeautifulSoup scraper
│   ├── weworkremotely_scraper.py # WeWorkRemotely BeautifulSoup scraper
│   ├── huggingface_client.py     # HuggingFace AI inference API client
│   └── telegram_client.py   # Telegram Bot alert integration
├── jobs/                    # Background polling and task orchestrators
│   └── scraper_poller.py    # Multi-source scraper polling runner
├── utils/                   # Shared utility modules & helpers
│   ├── ai_service.py        # AI job qualification & draft outreach generation
│   ├── signal_detection.py  # Job signal classification heuristics (HIGH/MEDIUM/IGNORE)
│   ├── validators.py        # Credential & environment validation helpers
│   └── exceptions.py        # Custom exception definitions
└── tests/                   # Test suite (Django test cases and pytest tests)
    ├── test_models.py           # Unit tests for core models
    ├── test_integrations.py     # Tests for external clients & scrapers (mocked)
    └── test_signal_detection.py # Tests for signal detection & AI service
```

### Core Data Models

- **`Source`**: Represents an external data feed or platform (GitHub Issues, RSS feed, job board) with rate limit settings and status.
- **`JobPost`**: Ingested job opportunity with title, description, URL, source reference, and processing status.
- **`QualificationScore`**: AI-evaluated scoring and classification (`HIGH`, `MEDIUM`, `IGNORE`) with reasoning.
- **`DraftMessage`**: Generated personalized application/outreach message for high-quality leads.
- **`AlertStatus`**: Tracking record for Telegram alert delivery.

### Pipeline Dataflow

```text
[ Sources / APIs ] (GitHub Issues, RSS feeds, Job Boards)
        │
        ▼
[ Ingestion & Normalization ] (integrations/*)
        │
        ▼
[ Database Persistence ] (core.models.JobPost)
        │
        ▼
[ Signal Detection & AI Qualification ] (utils.signal_detection, utils.ai_service)
        │
        ├── Score: HIGH ────► [ Draft Generation ] ────► [ Telegram Notification ]
        └── Score: MEDIUM / IGNORE ──► [ Archived in Database ]
```

---

## Development Workflow

1. **Clone the repository and set up environment:**
   ```bash
   git checkout master
   git pull origin master
   git checkout -b dsh/<issue-id>
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   # or
   pip install -r requirements.txt
   ```

3. **Configure local environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your development credentials
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Make your changes:**
   - Keep changes focused and minimal.
   - Maintain hermetic automated tests for any new behavior or bugfixes.
   - Follow existing style, naming conventions, and architecture.

6. **Run tests to verify:**
   ```bash
   uv run pytest -v
   ```

---

## Related Documentation

- [Project README](../README.md) - Project overview, features, and setup instructions.
- [Testing Guide](TESTING.md) - Detailed guide for manual and automated testing.
- [Production Guide](PRODUCTION.md) - Production deployment and execution runbook.
