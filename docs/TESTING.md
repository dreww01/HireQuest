# Testing Guide - HireQuest

This guide explains how to test the job scraping system and complete AI pipeline.

## 🎯 Quick Start Testing

### Method 1: Test Full Pipeline (Recommended)

**Best for:** Testing all scrapers at once

```bash
# Run complete pipeline with small limit
python manage.py run_full_pipeline --limit 5
```

This will:
- ✅ Scrape GitHub Issues (5 jobs)
- ✅ Scrape RSS feeds (5 jobs each)
- ✅ Scrape job boards (5 jobs each)
- ✅ Run AI qualification on all
- ✅ Send Telegram alerts for HIGH matches

**Expected output:**
```
🐙 STEP 1: GitHub Issues Scraping
✅ GitHub scraping complete

📡 STEP 2: RSS Feed Scraping
✅ RSS scraping complete

🌐 STEP 3: Job Board Scraping
✅ Job board scraping complete

📊 PIPELINE SUMMARY
Total jobs in database: 15
Total qualified: 12
Total alerts sent: 3
```

---

### Method 2: Test Individual Scrapers

**Best for:** Debugging specific scrapers

```bash
# Test GitHub Issues scraper only
python manage.py scrape_github --limit 5

# Test RSS feeds only
python manage.py scrape_rss --limit 5

# Test job boards only (BeautifulSoup)
python manage.py scrape_boards --limit 5
```

**Pros:**
- Faster feedback
- Isolate issues to specific scrapers
- Less API usage

**Cons:**
- Doesn't test full integration

---

### Method 3: Skip Specific Scrapers

**Best for:** Testing while avoiding rate limits or slow scrapers

```bash
# Skip GitHub (avoid rate limits)
python manage.py run_full_pipeline --skip-github

# Skip RSS feeds
python manage.py run_full_pipeline --skip-rss

# Skip job boards (BeautifulSoup)
python manage.py run_full_pipeline --skip-boards

# Only test GitHub
python manage.py run_full_pipeline --skip-rss --skip-boards
```

---

## 🔍 What Each Scraper Tests

### GitHub Issues Scraper

**Tests:**
- GitHub API authentication (optional token)
- Issue search with keywords
- Tech stack extraction
- Paid vs unpaid filtering
- AI qualification

**Expected results:**
- 5-10 GitHub issues containing "paid", "contract", "hire"
- Filtered to remove volunteer/unpaid posts
- Tech stack extracted from repo languages

**Verify:**
```bash
python manage.py shell
>>> from core.models import JobPost, Source
>>> github_source = Source.objects.get(type='github_issue')
>>> JobPost.objects.filter(source=github_source).count()
10
```

---

### RSS Feed Scraper

**Tests:**
- RSS feed parsing
- Keyword filtering
- Company/location extraction
- Job type classification

**Expected results:**
- Jobs from RemoteOK RSS feed
- Jobs from WeWorkRemotely RSS feed
- Filtered by keywords (Python, Django, etc.)

**Verify:**
```bash
>>> rss_sources = Source.objects.filter(type='rss_feed')
>>> JobPost.objects.filter(source__in=rss_sources).count()
20
```

---

### Job Board Scraper (BeautifulSoup)

**Tests:**
- robots.txt compliance
- Rate limiting (5s between requests)
- HTML parsing
- Detail page scraping
- Skill extraction

**Expected results:**
- Jobs from We Work Remotely HTML
- Jobs from RemoteOK HTML
- Full descriptions from detail pages
- Skills extracted (python, django, etc.)

**Verify:**
```bash
>>> board_sources = Source.objects.filter(type='job_board')
>>> jobs = JobPost.objects.filter(source__in=board_sources)
>>> jobs.count()
15
>>> jobs.first().skills_tags
'python,django,react'
```

---

## 🧪 Testing AI Qualification

After scraping, verify AI is working:

```bash
python manage.py shell
>>> from core.models import JobPost, QualificationScore
>>>
>>> # Check qualification rate
>>> total_jobs = JobPost.objects.count()
>>> qualified_jobs = QualificationScore.objects.count()
>>> print(f"Qualified: {qualified_jobs}/{total_jobs}")
>>>
>>> # Check HIGH classification jobs
>>> high_jobs = QualificationScore.objects.filter(classification='high')
>>> print(f"HIGH jobs: {high_jobs.count()}")
>>>
>>> # View a HIGH job
>>> high_job = high_jobs.first()
>>> print(f"Title: {high_job.job_post.title}")
>>> print(f"Confidence: {high_job.confidence:.0%}")
>>> print(f"Reasoning: {high_job.reasoning}")
```

---

## 📊 Test Coverage Matrix

| Component | Full Pipeline | Individual | Skip Mode |
|-----------|--------------|------------|-----------|
| GitHub API | ✅ | ✅ scrape_github | --skip-github |
| RSS parsing | ✅ | ✅ scrape_rss | --skip-rss |
| BeautifulSoup | ✅ | ✅ scrape_boards | --skip-boards |
| robots.txt check | ✅ | ✅ | ✅ |
| Rate limiting | ✅ | ✅ | ✅ |
| Job deduplication | ✅ | ✅ | ✅ |
| AI signal detection | ✅ | ✅ | ✅ |
| AI qualification | ✅ | ✅ | ✅ |
| Draft generation | ✅ | ✅ | ✅ |
| Telegram alerts | ✅ | ✅ | ✅ |

---

## 🔧 Testing Specific Features

### Test Rate Limiting

```bash
# Monitor rate limiting in logs
python manage.py scrape_boards --limit 10 --verbosity=2

# Should see logs like:
# [INFO] Rate limiting: sleeping 5.00s
# [INFO] Rate limiting: sleeping 3.00s
```

### Test robots.txt Compliance

```bash
python manage.py shell
>>> from integrations.weworkremotely_scraper import WeWorkRemotelyScraper
>>> scraper = WeWorkRemotelyScraper()
>>> scraper.can_fetch('https://weworkremotely.com/categories/remote-programming-jobs')
True
```

### Test Deduplication

```bash
# Run scraper twice
python manage.py scrape_rss --limit 5
python manage.py scrape_rss --limit 5

# Check no duplicates
>>> JobPost.objects.values('external_id').annotate(count=Count('id')).filter(count__gt=1)
<QuerySet []>  # Should be empty
```

### Test Keyword Filtering

```bash
# Update keywords in .env
JOB_KEYWORDS=python,django

# Run scraper
python manage.py scrape_rss --limit 10

# Verify jobs match keywords
>>> jobs = JobPost.objects.all()
>>> for job in jobs[:5]:
...     print(f"{job.title} - {job.skills_tags}")
```

---

## 🔍 Troubleshooting

### GitHub Rate Limit Exceeded

**Problem:** `GitHub API rate limit exceeded`

**Solutions:**
1. Add GITHUB_TOKEN to .env (increases from 60/hr to 5,000/hr)
2. Reduce scraping frequency
3. Use `--skip-github` flag
4. Check rate limit status:
```bash
python manage.py shell
>>> from integrations.github_scraper import GitHubScraper
>>> scraper = GitHubScraper(github_token='your_token')
>>> # Make request and check headers
```

---

### RSS Feed Not Returning Jobs

**Problem:** `No entries found in RSS feed`

**Solutions:**
1. Check internet connection
2. Verify feed URL is correct:
```bash
>>> from integrations.rss_scraper import RSSJobScraper
>>> scraper = RSSJobScraper(board_name='remoteok')
>>> scraper.feed_url
'https://remoteok.com/remote-jobs.rss'
```
3. Test feed manually in browser
4. Check if feed requires authentication

---

### BeautifulSoup Scraper Returns Empty

**Problem:** `Scraped 0 jobs from We Work Remotely`

**Solutions:**
1. Job board may have changed HTML structure
2. Check console logs for specific errors
3. Test scraper directly:
```bash
>>> from integrations.weworkremotely_scraper import WeWorkRemotelyScraper
>>> scraper = WeWorkRemotelyScraper()
>>> jobs = scraper.scrape_listings(limit=5)
>>> len(jobs)
5
```
4. Verify robots.txt didn't block access
5. Check rate limiting isn't too aggressive

---

### AI Not Qualifying Jobs

**Problem:** `QualificationScore.objects.count() == 0`

**Solutions:**
1. Check HUGGINGFACE_API_KEY in .env
2. First API call takes 30-60 seconds (model loading)
3. Check HuggingFace account has credits
4. View error logs:
```bash
tail -f hirequest.log | grep ERROR
```
5. Test AI directly:
```bash
>>> from utils.ai_service import detect_job_signal
>>> job = JobPost.objects.first()
>>> is_signal, confidence, reasoning = detect_job_signal(job)
>>> print(f"Signal: {is_signal}, Confidence: {confidence}")
```

---

### No Telegram Alerts Sent

**Problem:** Telegram not receiving messages

**Solutions:**
1. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
2. Verify jobs are classified as HIGH:
```bash
>>> QualificationScore.objects.filter(classification='high').count()
```
3. Check AlertStatus records:
```bash
>>> from core.models import AlertStatus
>>> AlertStatus.objects.count()
```
4. Test Telegram directly:
```bash
>>> from integrations.telegram_client import TelegramClient
>>> client = TelegramClient()
>>> client.send_message("Test message")
```

---

## 📝 Test Checklist

Before production deployment:

- [ ] GitHub scraper works (with and without token)
- [ ] RSS feeds parse correctly
- [ ] Job boards scrape without errors
- [ ] robots.txt compliance verified
- [ ] Rate limiting works (check logs)
- [ ] Deduplication prevents duplicates
- [ ] AI signal detection filters non-jobs
- [ ] AI qualification classifies correctly
- [ ] HIGH jobs generate drafts
- [ ] Telegram alerts send for HIGH jobs
- [ ] Admin panel displays all data
- [ ] No errors in logs after full pipeline

---

## 🚀 Quick Test Workflow (2 minutes)

For rapid testing during development:

```bash
# 1. Test with small limits
python manage.py run_full_pipeline --limit 3

# 2. Check results
python manage.py shell
>>> from core.models import JobPost, QualificationScore, AlertStatus
>>> print(f"Jobs: {JobPost.objects.count()}")
>>> print(f"Qualified: {QualificationScore.objects.count()}")
>>> print(f"Alerts: {AlertStatus.objects.count()}")

# 3. View dashboard
python manage.py runserver
# Visit: http://localhost:8000/admin/core/jobpost/
```

---

## 💡 Pro Tips

1. **Start small** - Use `--limit 3` for initial testing

2. **Test one scraper at a time** - Isolate issues faster

3. **Check logs** - Run with verbose output:
   ```bash
   python manage.py run_full_pipeline --verbosity=2
   ```

4. **Monitor API usage** - Each job makes 2-3 HuggingFace calls

5. **Clean test data** - Delete test jobs periodically:
   ```bash
   python manage.py shell
   >>> JobPost.objects.filter(created_at__lt='2025-01-01').delete()
   ```

6. **Test different keywords** - Update JOB_KEYWORDS in .env

7. **Verify external_id uniqueness** - Check for duplicate detection:
   ```bash
   >>> JobPost.objects.values('external_id').annotate(count=Count('id')).filter(count__gt=1).count()
   0
   ```

---

## 🎯 Performance Benchmarks

Expected performance for `--limit 20`:

| Scraper | Time | Jobs | API Calls |
|---------|------|------|-----------|
| GitHub | 10-15s | 15-20 | 1-3 (search) |
| RSS Feeds | 5-10s | 30-40 | 2 (feeds) |
| Job Boards | 60-90s | 20-30 | 20-30 (with rate limit) |
| AI Qualification | 30-60s | - | 2-3 per job |
| **Total** | **2-3 min** | **65-90** | **150-250** |

*Note: First HuggingFace call adds 30-60s for model loading*

---

## 🔄 Continuous Testing

For ongoing monitoring:

```bash
# Run daily
0 9 * * * cd /path/to/project && python manage.py run_full_pipeline --limit 10

# Check for errors
0 10 * * * grep ERROR /path/to/project/job_hunt_bot.log | mail -s "Job Bot Errors" you@email.com
```

---

## 📚 Next Steps After Testing

Once all tests pass:

1. **Increase limits** - Use `--limit 50` for production
2. **Schedule automated runs** - Set up cron jobs
3. **Monitor scrapers** - Check for HTML structure changes
4. **Tune AI prompts** - Adjust if too many false positives
5. **Add more scrapers** - Expand to other job boards
6. **Set up monitoring** - Track scraping success rates

---

Need help? Check the main [README.md](../README.md) or review scraper implementations in `integrations/`
