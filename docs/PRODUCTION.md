# Production Run Guide - HireQuest 🚀

**Complete guide for running the full job hunting pipeline with real email leads**

---

## Quick Start (TL;DR)

```bash
# 1. Setup database and sources
uv run python manage.py migrate
uv run python manage.py setup_newsletter_sources

# 2. Run the full pipeline
uv run python manage.py poll_emails        # Fetch from inbox
uv run python manage.py poll_reddit        # Fetch from Reddit (if configured)

# 3. Monitor results
uv run python manage.py runserver
# Open: http://localhost:8000/admin
```

---

## Prerequisites

### 1. Environment Configuration

Ensure your `.env` file is configured with real credentials:

```bash
# Email Configuration (Required for email leads)
EMAIL_HOST=imap.gmail.com
EMAIL_PORT=993
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password

# Hugging Face API (Required for AI qualification)
HUGGINGFACE_API_KEY=hf_your_actual_api_key
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-1B-Instruct

# Telegram Bot (Required for alerts)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Reddit API (Optional - only if you want Reddit monitoring)
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
REDDIT_USER_AGENT=HireQuest Bot v1.0
REDDIT_USERNAME=your-reddit-username
REDDIT_PASSWORD=your-reddit-password
```

**Get Gmail App Password:**
1. Enable 2FA: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer"
4. Copy the 16-character password to `.env`

### 2. Database Setup

```bash
# Apply migrations
uv run python manage.py migrate

# Create admin user
uv run python manage.py createsuperuser
```

### 3. Configure Newsletter Sources

```bash
# This sets up keywords to match job newsletter emails
uv run python manage.py setup_newsletter_sources
```

**What this does:**
- Creates Source records for popular job platforms (LinkedIn, Indeed, Glassdoor, etc.)
- Matches emails containing these keywords in sender OR subject
- Example: `linkedin` matches `hello@linkedin.com`, `jobs@linkedin.com`, or subject "LinkedIn Job Alert"

---

## Running the Full Pipeline

### Method 1: Manual Polling (Recommended for Testing)

**Step 1: Poll Your Inbox**
```bash
uv run python manage.py poll_emails
```

**What happens:**
1. ✅ Connects to your email inbox via IMAP
2. ✅ Fetches recent unread emails
3. ✅ Matches emails against configured newsletter sources
4. ✅ Uses AI to detect if email contains job postings
5. ✅ Extracts and saves job posts to database
6. ✅ Qualifies jobs using AI (high/medium/low)
7. ✅ Sends Telegram alerts for high-quality jobs

**Example output:**
```
============================================================
Starting email polling...
============================================================
[OK] Matched 'linkedin' keyword in email from: linkedin@email.linkedin.com
[AI] Analyzing if email is a job posting: Senior Django Developer - Remote
[+] Confirmed job posting (confidence: 95%): Senior Django Developer - Remote
[+] Created new job post from email: Senior Django Developer - Remote
============================================================
Email polling complete:
  - New job posts: 3
  - Existing posts: 2
  - Non-job emails filtered: 5
  - Unmatched emails: 1
============================================================
```

**Step 2: Poll Reddit (Optional)**
```bash
uv run python manage.py poll_reddit
```

⚠️ **Note:** This requires Reddit API credentials. If not configured, skip this step.

### Method 2: Automated Continuous Polling

**Option A: Using Django Cron (Linux/Mac)**
```bash
# Start the cron loop (runs every 5 minutes)
uv run python manage.py runcrons --force
```

**Option B: Manual Scheduler (Windows)**

Create a batch file `run_polling.bat`:
```batch
@echo off
cd "c:\Users\User\Desktop\HireQuest"
.venv\Scripts\python.exe manage.py poll_emails
.venv\Scripts\python.exe manage.py poll_reddit
```

Schedule it in Windows Task Scheduler to run every 5 minutes.

---

## Monitoring & Management

### View Dashboard

```bash
# Start Django server
uv run python manage.py runserver
```

**Admin Panel:** http://localhost:8000/admin
- View all job posts
- Filter by status (NEW, QUALIFIED, ALERTED, etc.)
- See AI qualification scores
- Read generated outreach drafts

**Dashboard:** http://localhost:8000/
- Clean UI showing recent jobs
- Filter by classification (high/medium/low)
- Quick access to job URLs

### Check Logs

The system logs everything to console and Django's logging system:

```bash
# Run with verbose logging
uv run python manage.py poll_emails --verbosity 2
```

**Log levels in `.env`:**
```bash
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## Complete Pipeline Flow

```
┌─────────────────┐
│  Your Inbox     │
│  (Unread emails)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  1. Email Polling                        │
│  - Fetch unread emails                   │
│  - Match against newsletter keywords     │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  2. AI Signal Detection                  │
│  - Analyze: Is this a job posting?       │
│  - Confidence scoring                    │
│  - Filter out non-job emails             │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  3. Job Qualification                    │
│  - Extract job details                   │
│  - Score: high/medium/low                │
│  - Generate reasoning                    │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  4. Alert & Draft Generation             │
│  - Send Telegram alert (high quality)    │
│  - Generate personalized outreach        │
│  - Save to database                      │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Your Telegram  │
│  📱 Alert!      │
└─────────────────┘
```

---

## Advanced Usage

### Custom Email Polling

```bash
# Poll only last 5 emails
uv run python manage.py poll_emails --limit 5

# Force re-process all emails (ignores read status)
uv run python manage.py poll_emails --force
```

### Test Individual Components

```bash
# Validate all API connections
uv run python manage.py validate_all_apis

# Test email connection only
uv run python manage.py test_email_connection

# Test AI qualification
uv run python manage.py test_huggingface_connection

# Send test Telegram alert
uv run python manage.py test_telegram_alert
```

### Create Test Data

```bash
# Create a sample job post and run full AI pipeline
uv run python manage.py create_test_job
```

---

## Including Reddit (Even Without API)

The system is designed to work with **both email and Reddit sources** simultaneously.

### If Reddit API is NOT configured:

```bash
# Just poll emails
uv run python manage.py poll_emails
```

The Reddit poller will gracefully skip if credentials are missing.

### If Reddit API IS configured:

```bash
# First, create Reddit sources
uv run python manage.py shell
```

```python
from core.models import Source

# Create Reddit sources
Source.objects.get_or_create(
    type=Source.REDDIT,
    identifier='forhire',
    defaults={'is_active': True}
)

Source.objects.get_or_create(
    type=Source.REDDIT,
    identifier='slavelabour',
    defaults={'is_active': True}
)

exit()
```

```bash
# Then poll both
uv run python manage.py poll_emails
uv run python manage.py poll_reddit
```

---

## Troubleshooting

### Email Connection Issues

**Problem:** `Email authentication failed`

**Solution:**
1. Verify you're using Gmail App Password (not regular password)
2. Ensure 2FA is enabled on your Google account
3. Check EMAIL_HOST and EMAIL_PORT in `.env`

```bash
# Test connection
uv run python manage.py test_email_connection
```

### AI Processing Issues

**Problem:** `HuggingFace API error`

**Solution:**
1. Verify API key: https://huggingface.co/settings/tokens
2. Check model name: `meta-llama/Llama-3.2-1B-Instruct`
3. First request may take 30-60s (model loading)

```bash
# Test AI
uv run python manage.py test_huggingface_connection
```

### No Emails Being Processed

**Problem:** Polling runs but no jobs created

**Check:**
1. Do you have unread job emails in inbox?
2. Are newsletter sources configured?

```bash
# Verify sources
uv run python manage.py shell
```

```python
from core.models import Source
print(Source.objects.filter(type=Source.NEWSLETTER, is_active=True).count())
# Should be > 0
```

### Telegram Alerts Not Sending

**Problem:** No alerts received

**Solution:**
1. Message your bot first before getting chat_id
2. Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
3. Check bot permissions

```bash
# Test alert
uv run python manage.py test_telegram_alert
```

---

## Production Deployment Checklist

- [ ] `.env` configured with real credentials
- [ ] Database migrated: `python manage.py migrate`
- [ ] Admin user created: `python manage.py createsuperuser`
- [ ] Newsletter sources setup: `python manage.py setup_newsletter_sources`
- [ ] Email connection tested: `python manage.py test_email_connection`
- [ ] AI connection tested: `python manage.py test_huggingface_connection`
- [ ] Telegram tested: `python manage.py test_telegram_alert`
- [ ] First manual poll successful: `python manage.py poll_emails`
- [ ] Scheduler configured (cron/Task Scheduler)

---

## Example: Complete First Run

```bash
# 1. Navigate to project
cd "c:\Users\User\Desktop\HireQuest"

# 2. Ensure virtual environment is active (uv handles this)

# 3. Setup database
uv run python manage.py migrate
uv run python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: ****

# 4. Configure sources
uv run python manage.py setup_newsletter_sources

# 5. Validate everything works
uv run python manage.py validate_all_apis

# 6. Run first poll (with real inbox)
uv run python manage.py poll_emails

# 7. View results
uv run python manage.py runserver
# Open: http://localhost:8000/admin

# 8. Schedule for automation (optional)
# Setup Windows Task Scheduler or use:
uv run python manage.py runcrons --force
```

---

## Performance Tips

**Email Polling:**
- Default limit: 10 recent emails
- Increase for first run: `--limit 50`
- Emails are marked as read after processing
- Re-run won't duplicate jobs (uses external_id)

**AI Processing:**
- First HuggingFace call is slow (model load: ~30-60s)
- Subsequent calls are faster (~5-10s each)
- Consider batching emails for efficiency

**Database:**
- SQLite is fine for personal use (< 10,000 jobs)
- For production, consider PostgreSQL
- Jobs are deduplicated by external_id

---

## Next Steps

1. **Subscribe to job newsletters** using the email in your `.env`
   - LinkedIn Job Alerts
   - Indeed Job Alerts
   - Glassdoor Alerts
   - etc.

2. **Wait for emails to arrive** in your inbox

3. **Run polling:**
   ```bash
   uv run python manage.py poll_emails
   ```

4. **Check Telegram for alerts** 📱

5. **Review jobs in admin panel** and apply!

---

## Support

**For issues:**
- Check [API_VALIDATION_GUIDE.md](API_VALIDATION_GUIDE.md) for API setup
- Check [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing workflows
- Check [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for dashboard usage

**Common commands:**
```bash
# Full validation
uv run python manage.py validate_all_apis

# Quick test with sample data
uv run python manage.py create_test_job

# View all management commands
uv run python manage.py help
```

---

**Built with Django + AI | Monitor → Qualify → Alert → Apply 🚀**
