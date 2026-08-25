# Production Run Guide - HireQuest 🚀

> **Complete guide for configuring, running, and monitoring the full job hunting pipeline in production environments.**

---

## 📑 Table of Contents

- [Quick Start (TL;DR)](#-quick-start-tldr)
- [Prerequisites & Environment Configuration](#-prerequisites--environment-configuration)
  - [1. Environment Variables](#1-environment-variables)
  - [2. Obtaining Credentials](#2-obtaining-credentials)
  - [3. Database Initialization](#3-database-initialization)
  - [4. Source Configuration](#4-source-configuration)
- [Running the Ingestion Pipeline](#-running-the-ingestion-pipeline)
  - [Method 1: Manual CLI Execution](#method-1-manual-cli-execution)
  - [Method 2: Automated Scheduled Polling](#method-2-automated-scheduled-polling)
- [Pipeline Architecture & Lifecycle](#-pipeline-architecture--lifecycle)
- [Monitoring & Dashboard Operations](#-monitoring--dashboard-operations)
  - [Web Dashboard & Admin Panel](#web-dashboard--admin-panel)
  - [Log Management & Verbosity](#log-management--verbosity)
- [Component Health Checks & Diagnostics](#-component-health-checks--diagnostics)
- [Troubleshooting Common Production Issues](#-troubleshooting-common-production-issues)
- [Production Deployment Checklist](#-production-deployment-checklist)

---

## ⚡ Quick Start (TL;DR)

```bash
# 1. Setup database migrations and administrative account
python manage.py migrate
python manage.py createsuperuser

# 2. Run the ingestion pipeline
python manage.py run_full_pipeline

# 3. Start the dashboard and admin panel
python manage.py runserver
# Open: http://localhost:8000/admin
```

---

## 📋 Prerequisites & Environment Configuration

### 1. Environment Variables

Ensure your `.env` file contains valid credentials for all active ingestion and alerting integrations:

```ini
# --- Django Settings ---
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# --- Email Integration (IMAP) ---
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password

# --- Hugging Face AI Qualification ---
HUGGINGFACE_API_KEY=hf_your_actual_api_key
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-1B-Instruct

# --- Telegram Bot Alerts ---
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# --- Scraping Configuration ---
SCRAPE_INTERVAL_MINUTES=60
MAX_JOBS_PER_SOURCE=20
JOB_MAX_AGE_DAYS=7
LOG_LEVEL=INFO
```

---

### 2. Obtaining Credentials

#### Gmail App Password Setup
1. Enable 2-Factor Authentication on your Google Account: [Google Security Settings](https://myaccount.google.com/security).
2. Generate an App Password: [Google App Passwords](https://myaccount.google.com/apppasswords).
3. Set the app type to **Mail** and device to your workstation.
4. Copy the generated 16-character token to `EMAIL_PASSWORD` in `.env`.

#### Telegram Bot Setup
1. Message [@BotFather](https://t.me/botfather) on Telegram.
2. Run `/newbot` and follow the instructions to create your bot and obtain the `TELEGRAM_BOT_TOKEN`.
3. Open your new bot's chat and click **Start**.
4. Retrieve your `TELEGRAM_CHAT_ID` via `https://api.telegram.org/bot<TOKEN>/getUpdates`.

#### Hugging Face API Token
1. Log in to [Hugging Face](https://huggingface.co/settings/tokens).
2. Create an access token with `read` permissions.
3. Set `HUGGINGFACE_API_KEY` in `.env`.

---

### 3. Database Initialization

```bash
# Apply all database schema migrations
python manage.py migrate

# Create initial administrator credentials
python manage.py createsuperuser
```

---

### 4. Source Configuration

Configure active sources and keyword filters:

```bash
# Run all initial pipeline scrapers to populate sources
python manage.py run_full_pipeline --limit 5
```

---

## 🚀 Running the Ingestion Pipeline

### Method 1: Manual CLI Execution

Run the complete pipeline or individual scraper modules:

```bash
# Run full scraping, AI qualification, and alerting pipeline
python manage.py run_full_pipeline

# Run individual scraper components
python manage.py scrape_github --limit 20
python manage.py scrape_rss --limit 20
python manage.py scrape_boards --limit 20
```

---

### Method 2: Automated Scheduled Polling

#### Option A: Cron Schedule (Linux / macOS)

Add a crontab entry to execute the ingestion pipeline periodically:

```bash
# Edit crontab
crontab -e

# Run pipeline every hour at the top of the hour
0 * * * * cd /path/to/hirequest && /path/to/hirequest/venv/bin/python manage.py run_full_pipeline >> /var/log/hirequest.log 2>&1
```

#### Option B: Background Poller Command

HireQuest includes a polling daemon for continuous operation:

```bash
# Run the continuous poller and alert daemon
python manage.py poll_and_alert
```

---

## 🔄 Pipeline Architecture & Lifecycle

```
┌────────────────────────────────────────────────────────┐
│ 1. Ingestion Stage                                     │
│    • Queries GitHub Issues, RSS feeds, and HTML boards │
│    • Enforces rate limiting and robots.txt rules       │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 2. Deduplication & Persistence                         │
│    • Checks external_id against existing JobPost items │
│    • Saves new listings with status=NEW                │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 3. AI Qualification & Signal Filtering                 │
│    • Validates job signal (filters non-opportunities)  │
│    • Classifies match quality: HIGH / MEDIUM / IGNORE  │
│    • Stores confidence scores and qualification notes  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ 4. Alerting & Outreach Generation                      │
│    • Auto-generates personalized cover letters/drafts  │
│    • Dispatches instant Telegram alert for HIGH leads  │
│    • Updates JobPost status to ALERTED                 │
└────────────────────────────────────────────────────────┘
```

---

## 📊 Monitoring & Dashboard Operations

### Web Dashboard & Admin Panel

Launch the local web server to access the dashboard and admin panel:

```bash
python manage.py runserver 0.0.0.0:8000
```

- **Admin Panel:** `http://localhost:8000/admin`
  - Manage `Source`, `JobPost`, `QualificationScore`, and `AlertStatus` records.
  - Review AI reasoning and generated cover letter drafts.
  - Update job application statuses (e.g., APPLIED, INTERVIEWING, REJECTED).
- **Public Dashboard:** `http://localhost:8000/`
  - View incoming opportunities, filter by classification score, and follow direct application links.

---

### Log Management & Verbosity

Control log verbosity via `.env` or CLI arguments:

```bash
# Run with detailed debug output
python manage.py run_full_pipeline --verbosity 2
```

---

## 🩺 Component Health Checks & Diagnostics

Run diagnostic commands to verify integration health before scheduling production jobs:

```bash
# 1. Validate all API credentials and external connections
python manage.py validate_all_apis

# 2. Test Telegram notification delivery
python manage.py test_telegram_alert

# 3. Create a synthetic job post to verify the end-to-end AI qualification pipeline
python manage.py create_test_job
```

---

## 🛠️ Troubleshooting Common Production Issues

### Email / IMAP Authentication Failure
- Verify you are using a 16-character **Google App Password**, not your primary password.
- Verify `EMAIL_HOST=imap.gmail.com` and `EMAIL_PORT=993`.

### Hugging Face API Errors or Timeouts
- The first API request will encounter cold-start latency (30–60s) as model weights load.
- Ensure your `HUGGINGFACE_API_KEY` token has active read permissions.

### Telegram Notifications Not Arriving
- Ensure you have opened a chat with your bot and clicked **Start**.
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` with `python manage.py test_telegram_alert`.

---

## ✅ Production Deployment Checklist

- [ ] `.env` created and configured with production secrets and API keys.
- [ ] Database migrations applied: `python manage.py migrate`.
- [ ] Administrative user initialized: `python manage.py createsuperuser`.
- [ ] External API connections verified: `python manage.py validate_all_apis`.
- [ ] Test Telegram alert confirmed: `python manage.py test_telegram_alert`.
- [ ] Initial pipeline scrape verified: `python manage.py run_full_pipeline --limit 5`.
- [ ] Scheduled automation configured (Cron or systemd service).
- [ ] Log rotation configured for pipeline logs.

---

**Related Documentation:**
- [Main README](../README.md) — Architectural overview, feature matrix, and setup.
- [Testing Guide](TESTING.md) — Unit and integration test workflows.
