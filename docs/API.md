# API & Testing Documentation - HireQuest 🔌

> **Comprehensive reference documentation for all external integrations, AI inference clients, data ingestion APIs, internal REST/AJAX endpoints, and their automated test suites.**

---

## 📑 Table of Contents

- [1. Overview & Architecture](#1-overview--architecture)
- [2. API Inventory Matrix](#2-api-inventory-matrix)
- [3. External Third-Party APIs & Scraper Clients](#3-external-third-party-apis--scraper-clients)
  - [3.1 GitHub Issues Search API](#31-github-issues-search-api)
  - [3.2 Hugging Face Serverless Inference API](#32-hugging-face-serverless-inference-api)
  - [3.3 Telegram Bot API](#33-telegram-bot-api)
  - [3.4 RemoteOK REST / JSON API](#34-remoteok-rest--json-api)
  - [3.5 RSS / XML Feed Aggregation APIs](#35-rss--xml-feed-aggregation-apis)
  - [3.6 We Work Remotely Web Ingestion API](#36-we-work-remotely-web-ingestion-api)
- [4. Internal Application REST / AJAX APIs](#4-internal-application-rest--ajax-apis)
  - [4.1 Update Job Pipeline Status (`POST /api/jobs/<id>/status/`)](#41-update-job-pipeline-status)
  - [4.2 Update Job User Tracking Status (`POST /api/jobs/<id>/user-status/`)](#42-update-job-user-tracking-status)
  - [4.3 Delete Job (`DELETE /api/jobs/<id>/delete/`)](#43-delete-job)
- [5. Credential Validation & Exception Architecture](#5-credential-validation--exception-architecture)
  - [5.1 Validation Utilities (`utils/validators.py`)](#51-validation-utilities)
  - [5.2 Custom Exception Hierarchy (`utils/exceptions.py`)](#52-custom-exception-hierarchy)
- [6. Automated API Test Suite & Verification Matrix](#6-automated-api-test-suite--verification-matrix)
  - [6.1 Testing Methodology & Hermetic Isolation](#61-testing-methodology--hermetic-isolation)
  - [6.2 Test Matrix: Mapping APIs to Test Cases](#62-test-matrix-mapping-apis-to-test-cases)
  - [6.3 Running Unit & Integration Tests](#63-running-unit--integration-tests)
  - [6.4 Live API Connectivity & Health Validation CLI](#64-live-api-connectivity--health-validation-cli)

---

## 1. Overview & Architecture

**HireQuest** interacts with a variety of external APIs and provides internal RESTful JSON endpoints to power its automated job qualification pipeline and web dashboard. 

The API layer is partitioned into four major domains:
1. **Data Ingestion APIs:** External REST APIs (GitHub, RemoteOK), structured RSS/XML feeds (RemoteOK, WeWorkRemotely, Remotive, StackOverflow), and HTML scrapers.
2. **AI Inference APIs:** Serverless Large Language Model inference via Hugging Face Inference API (`meta-llama/Llama-3.2-1B-Instruct`) for job signal detection, classification, and personalized outreach generation.
3. **Notification APIs:** Telegram Bot API for real-time push alerts of high-priority leads.
4. **Internal Dashboard REST/AJAX APIs:** Django JSON endpoints enabling client-side status mutations, application tracking updates, and record management without full page reloads.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL INTEGRATIONS                            │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ GitHub Search API │ Hugging Face LLM  │ Telegram Bot API  │ RemoteOK / RSS  │
│  (REST / v3 JSON) │ (ChatCompletions) │ (Async Push Alert)│ (JSON / XML)    │
└─────────┬─────────┴─────────┬─────────┴─────────┬─────────┴────────┬────────┘
          │                   │                   │                  │
          ▼                   ▼                   ▼                  ▼
┌───────────────────┬───────────────────┬───────────────────┬─────────────────┐
│ GitHubScraper     │ HuggingFaceClient │ TelegramClient    │ RemoteOKScraper │
│                   │ & ai_service.py   │ & core/signals.py │ RSSJobScraper   │
└─────────┬─────────┴─────────┬─────────┴─────────┬─────────┴────────┬────────┘
          │                   │                   │                  │
          └───────────────────┼───────────────────┘                  │
                              ▼                                      │
                   ┌───────────────────────┐                         │
                   │  Django ORM (JobPost) │ ◄───────────────────────┘
                   └──────────┬────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     INTERNAL REST / AJAX DASHBOARD APIS                     │
├────────────────────────────┬────────────────────────────┬───────────────────┤
│ POST /api/jobs/:id/status/ │ POST /api/jobs/:id/user-st/│ DELETE /api/jobs/ │
└────────────────────────────┴────────────────────────────┴───────────────────┘
```

---

## 2. API Inventory Matrix

| API / Service | Category | Protocol / Format | Authentication | Source Module | Test Module |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GitHub Issues API** | Ingestion | HTTPS REST (JSON) | `GITHUB_TOKEN` (Optional, recommended) | `integrations/github_scraper.py` | `tests/test_integrations.py` |
| **Hugging Face Inference API** | AI / Inference | HTTPS REST (Chat Completions) | `HUGGINGFACE_API_KEY` (Required for AI) | `integrations/huggingface_client.py`, `utils/ai_service.py` | `tests/test_integrations.py`, `tests/test_ai_service.py` |
| **Telegram Bot API** | Notification | HTTPS REST / Async | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | `integrations/telegram_client.py` | `tests/test_integrations.py` |
| **RemoteOK API** | Ingestion | HTTPS REST (JSON) | Public (User-Agent header) | `integrations/remoteok_scraper.py` | `tests/test_integrations.py` |
| **RSS Feed Aggregation** | Ingestion | RSS 2.0 / Atom (XML) | Public (User-Agent header) | `integrations/rss_scraper.py` | `tests/test_integrations.py` |
| **We Work Remotely Scraper** | Ingestion | HTTPS (HTML) | Public (User-Agent header) | `integrations/weworkremotely_scraper.py` | `tests/test_integrations.py` |
| **Job Status API** | Internal REST | HTTP POST (JSON) | Session / CSRF-Exempt AJAX | `core/views.py` (`update_job_status`) | `tests/test_api_views.py` |
| **User Status API** | Internal REST | HTTP POST (JSON) | Session / CSRF-Exempt AJAX | `core/views.py` (`update_user_status`) | `tests/test_api_views.py` |
| **Job Delete API** | Internal REST | HTTP DELETE (JSON) | Session / CSRF-Exempt AJAX | `core/views.py` (`delete_job`) | `tests/test_api_views.py` |

---

## 3. External Third-Party APIs & Scraper Clients

### 3.1 GitHub Issues Search API

The GitHub Issues scraper identifies contract, freelance, and paid developer opportunities posted across public GitHub repository issues.

- **Endpoints Used:**
  - `GET https://api.github.com/search/issues`: Queries issues matching target keywords.
  - `GET https://api.github.com/repos/{owner}/{repo}/languages`: Identifies programming languages in parent repositories.
- **Client Class:** `integrations.github_scraper.GitHubScraper`
- **Authentication:** Bearer token via `Authorization: token <GITHUB_TOKEN>` header.
- **Rate Limits:**
  - Authenticated: 5,000 requests/hour.
  - Unauthenticated: 60 requests/hour.
  - Returns `403 Forbidden` on quota exhaustion (handled gracefully by breaking query loops).
- **Search Parameters:**
  - `q`: Search query with date filter, e.g. `"paid" in:title,body created:>2025-01-01`.
  - `sort`: `created`
  - `order`: `desc`
  - `per_page`: Max 30 per page (API maximum is 100).

#### Keyword Classification Rules
- **Paid Keywords:** `paid`, `contract`, `freelancer`, `freelance`, `hire`, `hiring`, `bounty`, `looking for developer`, `looking for a developer`, `need a developer`, `compensation`, `budget`, `rate`, `payment`.
- **Unpaid Filter Keywords (Filtered Out):** `volunteer`, `unpaid`, `no budget`, `free`, `open source contributor`, `looking for contributors`.

#### Standardized Output Schema
```json
{
  "id": "github_12345678",
  "title": "Need Python Django Developer for SaaS Integration",
  "company_name": "example-repo",
  "job_type": "Contract",
  "location": "Remote",
  "skills_tags": "django,docker,postgresql,python",
  "body": "Looking for an experienced Django contractor...",
  "url": "https://github.com/example/repo/issues/123",
  "application_link": "https://github.com/example/repo/issues/123",
  "timestamp": "2025-01-01T12:00:00Z",
  "author": "client_username"
}
```

---

### 3.2 Hugging Face Serverless Inference API

HireQuest uses the Hugging Face Inference API to execute zero-shot evaluation, classification, and generation tasks using open-weights models (default: `meta-llama/Llama-3.2-1B-Instruct`).

- **Endpoint / SDK:** Hugging Face Serverless Inference via `huggingface_hub.InferenceClient.chat_completion`
- **Client Class:** `integrations.huggingface_client.HuggingFaceClient`
- **Authentication:** `HUGGINGFACE_API_KEY` (configured in `.env` / `settings.HUGGINGFACE_API_KEY`).
- **Configured Model:** `settings.HUGGINGFACE_MODEL` (`meta-llama/Llama-3.2-1B-Instruct`).

#### Core Methods
1. `query(prompt, max_tokens=500, temperature=0.7) -> str`
   - Dispatches a single chat completion message to the configured LLM.
   - Raises `InvalidAPIKeyError` on 401/Unauthorized, `APIConnectionError` on 404/NotFound or network failures.
2. `test_connection() -> bool`
   - Smoke-test verifying API token validity and model availability.
3. `analyze_job_relevance(job_post) -> dict`
   - Returns `{'is_relevant': bool, 'confidence': float, 'reasoning': str}`.
4. `generate_draft_message(job_post, user_profile) -> str`
   - Generates contextual outreach messages matching candidate parameters.

#### Higher-Level AI Services (`utils/ai_service.py`)
- `detect_job_signal(job_post)`:
  - Invokes `HuggingFaceClient` to classify if a posting represents a legitimate hiring signal.
  - **Graceful Fallback:** If Hugging Face is unreachable or unconfigured, falls back to a deterministic keyword matching algorithm (`hiring`, `looking for`, `developer`, `freelance`, `remote`, `django`, etc.).
- `qualify_job(job_post)`:
  - Evaluates job text against spam indicators (`mlm`, `pyramid scheme`, `get rich quick` $\rightarrow$ `IGNORE`), senior experience filters (`senior` $\rightarrow$ `IGNORE`), and high-match tech indicators (`django`, `fastapi`, `postgresql`, `full-time`, `$` $\rightarrow$ `HIGH`).
- `generate_draft_message(job_post, qualification)`:
  - Creates a `DraftMessage` model instance containing platform-specific copy:
    - **GitHub Issues:** Comment-formatted pitch (`GITHUB_COMMENT`).
    - **RSS / Job Boards:** Email pitch and formal 300–400 word cover letter (`COVER_LETTER`).
  - **Graceful Fallback:** If the LLM call fails, falls back to templated professional outreach drafts.

---

### 3.3 Telegram Bot API

Delivers real-time push notifications for `HIGH`-priority qualified job postings directly to a Telegram chat or channel.

- **Protocol / SDK:** `python-telegram-bot` (`telegram.Bot.send_message`)
- **Client Class:** `integrations.telegram_client.TelegramClient`
- **Authentication:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **Notification Trigger:** Triggered synchronously via Django post-save signal on `QualificationScore` (`core/signals.py`) when `instance.classification == QualificationScore.HIGH`.

#### Methods
- `send_alert(job_post, qualification=None, draft=None, dashboard_url=None) -> int`
  - Formats Markdown message with title, source, description snippet, and dashboard link.
  - Escapes special Markdown V1 reserved characters (`_`, `*`, `[`, `]`, `(`, `)`, `~`, `\``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`).
  - Sends message with `disable_web_page_preview=True`.
  - Returns Telegram `message_id`.
- `send_simple_alert(job_post) -> int`
  - Shorthand alert helper without qualification metadata.

#### Sample Telegram Notification Payload
```markdown
🚨 *NEW JOB ALERT*

*Senior Django / React Engineer Needed*

📍 *Source:* GitHub Issue

*📋 Job Description*
Looking for an experienced Django contractor to build REST APIs and integrate frontend components...

[View Full Details on Dashboard →](http://localhost:8000/jobs/42/)
```

---

### 3.4 RemoteOK REST / JSON API

RemoteOK exposes a public JSON endpoint containing recent remote job listings.

- **Endpoint:** `GET https://remoteok.com/api`
- **Client Class:** `integrations.remoteok_scraper.RemoteOKScraper` (inherits from `BaseScraper`)
- **Protocol:** HTTP GET returning JSON array.
- **Quirks & Format:** The first element (`data[0]`) is legal metadata; job listings begin at `data[1:]`.
- **Sanitization:** HTML tags are decomposed, line breaks preserved, entities unescaped, and text truncated to 5,000 characters.
- **Polite Crawling:** Configured with a 5-second rate limiting delay (`_rate_limit()`) and robots.txt checking via `RobotFileParser`.

---

### 3.5 RSS / XML Feed Aggregation APIs

Ingests structured XML feeds from popular job boards.

- **Client Class:** `integrations.rss_scraper.RSSJobScraper`
- **Protocol:** RSS 2.0 / Atom XML parsed via `requests` and `feedparser`.
- **Built-in Feeds:**
  - `remoteok`: `https://remoteok.com/remote-jobs.rss`
  - `weworkremotely`: `https://weworkremotely.com/categories/remote-programming-jobs.rss`
  - `remotive`: `https://remotive.com/api/remote-jobs/feed`
  - `stackoverflow`: `https://stackoverflow.com/jobs/feed`
  - Custom user-specified feed URLs
- **Parsing Capabilities:**
  - Date extraction from `published_parsed` or `updated_parsed`.
  - Metadata parsing (company, location, job type, skills) from structured tags and description summaries.
  - Keyword filtering against title, body, and skill tags.

---

### 3.6 We Work Remotely Web Ingestion API

Scrapes HTML listings and detail pages from We Work Remotely when RSS is not utilized.

- **Endpoints:**
  - Search: `GET https://weworkremotely.com/remote-jobs/search?term=programming`
  - Detail: `GET https://weworkremotely.com/remote-jobs/<job-slug-id>`
- **Client Class:** `integrations.weworkremotely_scraper.WeWorkRemotelyScraper`
- **Engine:** BeautifulSoup4 with rate-limited HTTP sessions (`BaseScraper`).
- **Resilience:** 3-second request pacing, 3 retries with exponential backoff on network errors.

---

## 4. Internal Application REST / AJAX APIs

HireQuest exposes lightweight RESTful AJAX endpoints in `core/views.py` (routed in `core/urls.py`) to support asynchronous UI updates from the dashboard.

### 4.1 Update Job Pipeline Status

Updates the internal pipeline status of a job post (e.g. tracking whether it was alerted, sent, or ignored).

- **Route:** `POST /api/jobs/<int:job_id>/status/`
- **View:** `core.views.update_job_status`
- **Headers:** `Content-Type: application/json`
- **Valid Status Values:** `NEW`, `ALERTED`, `SENT`, `IGNORED`

#### Request Body
```json
{
  "status": "SENT"
}
```

#### Response Codes
- `200 OK`: Status successfully updated.
  ```json
  {
    "success": true,
    "message": "Job status updated to SENT",
    "status": "Proposal Sent"
  }
  ```
- `400 Bad Request`: Invalid status value or malformed JSON.
  ```json
  {
    "success": false,
    "message": "Invalid status. Must be one of: NEW, ALERTED, SENT, IGNORED"
  }
  ```
- `404 Not Found`: Target `job_id` does not exist.
  ```json
  {
    "success": false,
    "message": "Job not found"
  }
  ```
- `500 Internal Server Error`: Unexpected database or server error.

---

### 4.2 Update Job User Tracking Status

Updates the candidate's personal application tracking status for an opportunity.

- **Route:** `POST /api/jobs/<int:job_id>/user-status/`
- **View:** `core.views.update_user_status`
- **Headers:** `Content-Type: application/json`
- **Valid User Status Values:** `PENDING`, `APPLIED`, `INTERVIEWING`, `REJECTED`, `OFFER`, `IGNORED`

#### Request Body
```json
{
  "user_status": "APPLIED"
}
```

#### Response Codes
- `200 OK`: User status successfully updated.
  ```json
  {
    "success": true,
    "message": "Job marked as APPLIED",
    "user_status": "Applied"
  }
  ```
- `400 Bad Request`: Invalid user status choice or malformed JSON.
- `404 Not Found`: Target `job_id` does not exist.
- `500 Internal Server Error`: Unexpected error.

---

### 4.3 Delete Job

Deletes a job post and cascades associated qualification scores, alerts, and draft messages.

- **Route:** `DELETE /api/jobs/<int:job_id>/delete/`
- **View:** `core.views.delete_job`
- **Method:** `DELETE`

#### Response Codes
- `200 OK`: Job successfully deleted.
  ```json
  {
    "success": true,
    "message": "Job \"Python Backend Developer\" deleted successfully"
  }
  ```
- `404 Not Found`: Target `job_id` does not exist.
  ```json
  {
    "success": false,
    "message": "Job not found"
  }
  ```
- `500 Internal Server Error`: Unexpected database error.

---

## 5. Credential Validation & Exception Architecture

### 5.1 Validation Utilities (`utils/validators.py`)

Validation helpers run during service initialization and pipeline execution to catch misconfigurations early:

- `validate_required_settings(settings_dict, service_name, instructions=None)`: Verifies that required configuration keys exist, are non-empty, and do not contain placeholder values (`your-`, `placeholder`, `change-this`, `example`, `xxx`, `yyy`).
- `validate_github_credentials(github_token)`: Validates `GITHUB_TOKEN`.
- `validate_telegram_credentials(bot_token, chat_id)`: Validates `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
- `validate_huggingface_credentials(api_key)`: Validates `HUGGINGFACE_API_KEY`.
- `check_optional_service(service_name, required_settings)`: Non-raising validation returning `bool` to allow optional services to be skipped gracefully.

### 5.2 Custom Exception Hierarchy (`utils/exceptions.py`)

```
Exception
├── ConfigurationError
│   ├── MissingAPIKeyError     # Missing or placeholder credentials
│   └── InvalidAPIKeyError     # 401 Unauthorized / expired token
└── APIConnectionError         # 404 / network timeout / remote failure
```

---

## 6. Automated API Test Suite & Verification Matrix

### 6.1 Testing Methodology & Hermetic Isolation

All automated API tests in HireQuest adhere to strict enterprise isolation standards:
1. **Hermetic & Offline:** Unit and integration tests NEVER make live network calls. All external endpoints (`requests.Session.get`, `feedparser.parse`, `InferenceClient`, `telegram.Bot`) are mocked using `unittest.mock.patch` and `unittest.mock.MagicMock`.
2. **Zero Regressions:** 100% of tests must pass with zero warnings or deprecation errors.
3. **Contract Verification:** Tests assert on response status codes, payload structures, schema parsing, exception wrapping, and database state mutations.

---

### 6.2 Test Matrix: Mapping APIs to Test Cases

| Target API / Component | Test Module | Test Class & Method | Test Description & Invariants Verified |
| :--- | :--- | :--- | :--- |
| **GitHub Issues Search API** | `tests/test_integrations.py` | `GitHubScraperTest.test_search_issues` | Mocks GitHub search response; verifies issue parsing, ID format (`github_<id>`), and skill extraction. |
| **RSS Feed API** | `tests/test_integrations.py` | `RSSJobScraperTest.test_scrape_listings` | Mocks XML content and feedparser entries; tests metadata parsing, location extraction, and keyword filtering. |
| **RemoteOK JSON API** | `tests/test_integrations.py` | `RemoteOKScraperTest.test_scrape_listings` | Mocks JSON payload; verifies skipping of index 0 legal metadata, field normalization, and keyword matching. |
| **We Work Remotely Scraper** | `tests/test_integrations.py` | `WeWorkRemotelyScraperTest.test_scrape_listings` | Mocks BeautifulSoup HTML document; verifies CSS selector parsing, detail page fetching, and tech stack tags. |
| **Hugging Face Query API** | `tests/test_integrations.py` | `HuggingFaceClientTest.test_query` | Mocks `InferenceClient.chat_completion`; verifies prompt delivery and response extraction. |
| **Hugging Face Health Check** | `tests/test_integrations.py` | `HuggingFaceClientTest.test_test_connection` | Tests `test_connection()` returning `True` on successful test prompt response. |
| **Hugging Face Relevance** | `tests/test_integrations.py` | `HuggingFaceClientTest.test_analyze_job_relevance` | Tests structured classification parsing (`is_relevant`, `confidence`, `reasoning`). |
| **Hugging Face Draft Pitch** | `tests/test_integrations.py` | `HuggingFaceClientTest.test_generate_draft_message` | Tests applicant profile injection and contextual message generation. |
| **Telegram Bot Alert API** | `tests/test_integrations.py` | `TelegramClientTest.test_send_alert` | Mocks async `Bot.send_message`; tests Markdown message building, character escaping, and message ID return. |
| **AI Signal Detection (LLM)** | `tests/test_ai_service.py` | `TestAIService.test_detect_job_signal_ai_success` | Tests LLM response parsing for `IS_JOB_SIGNAL: YES` and confidence computation. |
| **AI Signal Fallback** | `tests/test_ai_service.py` | `TestAIService.test_detect_job_signal_fallback` | Verifies heuristic keyword detector activates when Hugging Face credentials are missing. |
| **AI Job Qualification (High)** | `tests/test_ai_service.py` | `TestAIService.test_qualify_job_high` | Verifies jobs with budget and target tech stack receive `HIGH` classification. |
| **AI Job Qualification (Senior)** | `tests/test_ai_service.py` | `TestAIService.test_qualify_job_senior_ignore` | Verifies senior/principal level positions are classified as `IGNORE`. |
| **AI Job Qualification (Spam)** | `tests/test_ai_service.py` | `TestAIService.test_qualify_job_spam_ignore` | Verifies multi-level marketing/get rich quick keywords trigger `IGNORE`. |
| **AI Draft Fallback** | `tests/test_ai_service.py` | `TestAIService.test_generate_draft_message_fallback` | Verifies deterministic fallback draft generation when AI client fails. |
| **Update Job Status (Success)** | `tests/test_api_views.py` | `InternalAPITests.test_update_job_status_success` | Tests `POST /api/jobs/<id>/status/` with valid status (returns 200 and updates DB). |
| **Update Job Status (Invalid)** | `tests/test_api_views.py` | `InternalAPITests.test_update_job_status_invalid_status` | Tests `POST /api/jobs/<id>/status/` with invalid status returns 400 Bad Request. |
| **Update Job Status (404)** | `tests/test_api_views.py` | `InternalAPITests.test_update_job_status_not_found` | Tests `POST /api/jobs/99999/status/` returns 404 Not Found. |
| **Update Job Status (Bad JSON)**| `tests/test_api_views.py` | `InternalAPITests.test_update_job_status_invalid_json` | Tests `POST /api/jobs/<id>/status/` with malformed JSON body returns 400. |
| **Update User Status (Success)**| `tests/test_api_views.py` | `InternalAPITests.test_update_user_status_success` | Tests `POST /api/jobs/<id>/user-status/` with valid user status (returns 200). |
| **Update User Status (Invalid)**| `tests/test_api_views.py` | `InternalAPITests.test_update_user_status_invalid_status` | Tests `POST /api/jobs/<id>/user-status/` with invalid user status returns 400. |
| **Update User Status (404)** | `tests/test_api_views.py` | `InternalAPITests.test_update_user_status_not_found` | Tests `POST /api/jobs/99999/user-status/` returns 404 Not Found. |
| **Delete Job (Success)** | `tests/test_api_views.py` | `InternalAPITests.test_delete_job_success` | Tests `DELETE /api/jobs/<id>/delete/` returns 200 and removes record from DB. |
| **Delete Job (404)** | `tests/test_api_views.py` | `InternalAPITests.test_delete_job_not_found` | Tests `DELETE /api/jobs/99999/delete/` returns 404 Not Found. |

---

### 6.3 Running Unit & Integration Tests

Execute the automated test suite locally:

```bash
# Run entire test suite via pytest
pytest

# Run entire test suite via Django test runner
python manage.py test

# Run API integration tests only
python manage.py test tests.test_integrations

# Run internal REST/AJAX API tests only
python manage.py test tests.test_api_views

# Run AI service & signal tests only
python manage.py test tests.test_ai_service
```

---

### 6.4 Live API Connectivity & Health Validation CLI

To validate live network connectivity and API keys against upstream providers:

```bash
# Validate GitHub, Telegram, and Hugging Face connections
python manage.py validate_all_apis --verbose

# Send an interactive test push alert to Telegram
python manage.py test_telegram_alert
```

#### Example Output: `validate_all_apis`
```text
======================================================================
HIREQUEST - API VALIDATION
======================================================================

[1/3] Testing GitHub API...
  -> Found issue: Python Developer needed for automation bot...
  -> Author: client_lead
  [OK] GitHub: CONNECTED

[2/3] Testing Telegram Bot...
  -> Message sent with ID: 1042
  -> Chat ID: 987654321
  [OK] Telegram: CONNECTED
     Check your Telegram app for test message!

[3/3] Testing Hugging Face AI...
  -> Model: meta-llama/Llama-3.2-1B-Instruct
  [OK] Hugging Face: CONNECTED

======================================================================
VALIDATION SUMMARY
======================================================================
Total APIs Tested: 3
Passed: 3

[OK] GITHUB: PASS
[OK] TELEGRAM: PASS
[OK] HUGGINGFACE: PASS
```
