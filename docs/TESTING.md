# Testing Guide - HireQuest 🧪

> **Comprehensive guide for running tests, validating scraper modules, and testing the AI qualification pipeline.**

---

## 📑 Table of Contents

- [Quick Start Testing](#-quick-start-testing)
  - [Method 1: Full Pipeline Integration Test (Recommended)](#method-1-full-pipeline-integration-test-recommended)
  - [Method 2: Individual Scraper Tests](#method-2-individual-scraper-tests)
  - [Method 3: Skip Flags for Fast Testing](#method-3-skip-flags-for-fast-testing)
- [Unit & Integration Test Suite](#-unit--integration-test-suite)
- [Scraper Verification Matrix](#-scraper-verification-matrix)
  - [GitHub Issues Scraper](#github-issues-scraper)
  - [RSS Feed Scraper](#rss-feed-scraper)
  - [HTML Job Board Scraper](#html-job-board-scraper)
- [Testing AI Qualification & Signal Detection](#-testing-ai-qualification--signal-detection)
- [Testing System Features](#-testing-system-features)
  - [Rate Limiting Verification](#rate-limiting-verification)
  - [robots.txt Compliance](#robotstxt-compliance)
  - [Deduplication Engine](#deduplication-engine)
  - [Keyword Filtering](#keyword-filtering)
- [Test Coverage Matrix](#-test-coverage-matrix)
- [Performance Benchmarks](#-performance-benchmarks)
- [Troubleshooting Test Failures](#-troubleshooting-test-failures)
- [Pre-Deployment Test Checklist](#-pre-deployment-test-checklist)

---

## 🎯 Quick Start Testing

### Method 1: Full Pipeline Integration Test (Recommended)

Run an end-to-end integration test across all active scrapers with a capped limit:

```bash
# Run complete pipeline with small limit
python manage.py run_full_pipeline --limit 5
```

**What this executes:**
1. Ingests 5 listings from GitHub Issues API.
2. Ingests 5 listings from RSS feeds (RemoteOK, WeWorkRemotely).
3. Ingests 5 listings from HTML job boards with polite delays.
4. Executes AI signal detection & qualification for all listings.
5. Sends Telegram notifications for `HIGH` classification items.

---

### Method 2: Individual Scraper Tests

Isolate and debug specific ingestion components:

```bash
# Test GitHub Issues scraper only
python manage.py scrape_github --limit 5

# Test RSS feeds only
python manage.py scrape_rss --limit 5

# Test HTML job boards only (BeautifulSoup)
python manage.py scrape_boards --limit 5
```

---

### Method 3: Skip Flags for Fast Testing

Bypass rate-limited or long-running sources during development:

```bash
# Skip GitHub (preserves API quota)
python manage.py run_full_pipeline --skip-github

# Skip RSS feeds
python manage.py run_full_pipeline --skip-rss

# Skip HTML job boards
python manage.py run_full_pipeline --skip-boards

# Test only GitHub Issues
python manage.py run_full_pipeline --skip-rss --skip-boards
```

---

## 🧪 Unit & Integration Test Suite

Execute Django unit tests to verify models, integrations, and services:

```bash
# Run all project tests
python manage.py test

# Run specific test modules
python manage.py test tests.test_models
python manage.py test tests.test_integrations
```

---

## 🔍 Scraper Verification Matrix

### GitHub Issues Scraper
- **Scope:** Verifies GitHub API authentication, query parameters, language extraction, and paid/unpaid filtering.
- **Verification Command:**
  ```bash
  python manage.py scrape_github --limit 5
  ```
- **Database Verification:**
  ```python
  # Run in: python manage.py shell
  from core.models import JobPost, Source
  github_source = Source.objects.get(type='github_issue')
  print("GitHub Jobs:", JobPost.objects.filter(source=github_source).count())
  ```

---

### RSS Feed Scraper
- **Scope:** Validates RSS feed parsing, keyword filtering, and structured attribute extraction.
- **Verification Command:**
  ```bash
  python manage.py scrape_rss --limit 5
  ```
- **Database Verification:**
  ```python
  # Run in: python manage.py shell
  from core.models import JobPost, Source
  rss_sources = Source.objects.filter(type='rss_feed')
  print("RSS Jobs:", JobPost.objects.filter(source__in=rss_sources).count())
  ```

---

### HTML Job Board Scraper
- **Scope:** Tests `robots.txt` compliance, inter-request rate limiting, HTML selector extraction, and detail page crawling.
- **Verification Command:**
  ```bash
  python manage.py scrape_boards --limit 5 --verbosity 2
  ```
- **Database Verification:**
  ```python
  # Run in: python manage.py shell
  from core.models import JobPost, Source
  board_sources = Source.objects.filter(type='job_board')
  print("Board Jobs:", JobPost.objects.filter(source__in=board_sources).count())
  ```

---

## 🤖 Testing AI Qualification & Signal Detection

Verify that the AI qualification engine evaluates opportunities accurately:

```bash
# 1. Create a sample job post and run AI evaluation
python manage.py create_test_job

# 2. Inspect qualification results in Django shell
python manage.py shell
```

```python
from core.models import JobPost, QualificationScore

total_jobs = JobPost.objects.count()
qualified_jobs = QualificationScore.objects.count()
print(f"Qualification Rate: {qualified_jobs}/{total_jobs}")

high_jobs = QualificationScore.objects.filter(classification='high')
print(f"HIGH matches: {high_jobs.count()}")

if high_jobs.exists():
    sample = high_jobs.first()
    print(f"Title: {sample.job_post.title}")
    print(f"Confidence: {sample.confidence:.0%}")
    print(f"Reasoning: {sample.reasoning}")
```

---

## 🔧 Testing System Features

### Rate Limiting Verification
Run scraper with verbose logging to observe delay enforcement:
```bash
python manage.py scrape_boards --limit 5 --verbosity 2
# Expected output includes: [INFO] Rate limiting: sleeping 3.00s
```

### robots.txt Compliance
Verify programmatic permission check:
```python
# python manage.py shell
from integrations.weworkremotely_scraper import WeWorkRemotelyScraper
scraper = WeWorkRemotelyScraper()
print("Can fetch programming category:", scraper.can_fetch('https://weworkremotely.com/categories/remote-programming-jobs'))
```

### Deduplication Engine
Run a scraper twice and verify that no duplicate records are created:
```bash
python manage.py scrape_rss --limit 5
python manage.py scrape_rss --limit 5
```
```python
# python manage.py shell
from django.db.models import Count
from core.models import JobPost
duplicates = JobPost.objects.values('external_id').annotate(c=Count('id')).filter(c__gt=1)
assert duplicates.count() == 0, "Duplicate records found!"
```

### Keyword Filtering
```bash
# Test with specific keywords
python manage.py scrape_rss --limit 5
```

---

## 📊 Test Coverage Matrix

| Feature / Component | Full Pipeline | Scraper Command | Unit Tests | Verification Method |
| :--- | :---: | :---: | :---: | :--- |
| **GitHub Issues API** | ✅ | `scrape_github` | ✅ | `test_integrations` |
| **RSS Feed Ingestion** | ✅ | `scrape_rss` | ✅ | `test_integrations` |
| **HTML BeautifulSoup** | ✅ | `scrape_boards` | ✅ | `test_integrations` |
| **Rate Limiter & Backoff** | ✅ | `scrape_boards` | ✅ | CLI logs (`--verbosity 2`) |
| **`robots.txt` Checker** | ✅ | `scrape_boards` | ✅ | Direct scraper unit checks |
| **Record Deduplication** | ✅ | All scrapers | ✅ | Database uniqueness check |
| **AI Signal Detection** | ✅ | `create_test_job` | ✅ | `QualificationScore` validation |
| **Telegram Notifications** | ✅ | `test_telegram_alert` | ✅ | `test_integrations` |

---

## ⏱️ Performance Benchmarks

Expected run times for standard scraping cycles (`--limit 20`):

| Pipeline Stage | Expected Time | Yield (Jobs) | Notes |
| :--- | :--- | :--- | :--- |
| **GitHub Issues** | 10–15s | 15–20 | 1–3 REST API calls |
| **RSS Feeds** | 5–10s | 30–40 | 2 XML feed requests |
| **HTML Job Boards** | 60–90s | 20–30 | Enforces polite delay between pages |
| **AI Qualification** | 30–60s | All | ~2–3 API calls per item (serverless cold start + inference) |
| **Total Cycle** | **2–3 min** | **65–90** | Complete end-to-end run |

---

## 🛠️ Troubleshooting Test Failures

### 1. `ModuleNotFoundError` or Missing Dependencies
- Verify virtual environment activation.
- Run `pip install -r requirements.txt`.

### 2. `GitHub API rate limit exceeded`
- Add `GITHUB_TOKEN` to your `.env` file to increase rate limit from 60 to 5,000 requests/hr.
- Alternatively, use `--skip-github`.

### 3. `HuggingFace API timeout / 503`
- The Hugging Face inference container may be cold-starting. Retry the command after 30 seconds.

### 4. `Telegram send failed`
- Validate `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` using `python manage.py test_telegram_alert`.

---

## 📋 Pre-Deployment Test Checklist

- [ ] All unit and integration tests pass: `python manage.py test`.
- [ ] Ingestion verified for GitHub Issues: `python manage.py scrape_github --limit 3`.
- [ ] Ingestion verified for RSS Feeds: `python manage.py scrape_rss --limit 3`.
- [ ] Ingestion verified for HTML Boards: `python manage.py scrape_boards --limit 3`.
- [ ] AI qualification and draft generation verified: `python manage.py create_test_job`.
- [ ] Telegram alert delivery confirmed: `python manage.py test_telegram_alert`.
- [ ] No duplicate records created during repeated runs.

---

**Related Documentation:**
- [Main README](../README.md) — System architecture, setup, and overview.
- [Production Guide](PRODUCTION.md) — Production operations and automated scheduling.
