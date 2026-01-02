from django.db import models


class Source(models.Model):
    # Tracks data sources for job scraping
    JOB_BOARD = 'job_board'
    GITHUB_ISSUE = 'github_issue'
    RSS_FEED = 'rss_feed'
    TYPE_CHOICES = [
        (JOB_BOARD, 'Job Board'),
        (GITHUB_ISSUE, 'GitHub Issue'),
        (RSS_FEED, 'RSS Feed'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    identifier = models.CharField(max_length=255, help_text="Board name, GitHub repo, or RSS feed URL")
    name = models.CharField(max_length=255, blank=True, help_text="Friendly display name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Scraper configuration
    scraper_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="beautifulsoup, selenium, api, rss"
    )
    base_url = models.URLField(max_length=500, blank=True, help_text="Base URL for scraping")
    rate_limit_seconds = models.IntegerField(default=5, help_text="Seconds between requests")

    class Meta:
        unique_together = ['type', 'identifier']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()}: {self.name or self.identifier}"


class JobPost(models.Model):
    # Core job opportunity record
    NEW = 'new'
    ALERTED = 'alerted'
    SENT = 'sent'
    CLOSED = 'closed'
    STATUS_CHOICES = [
        (NEW, 'New'),
        (ALERTED, 'Alerted'),
        (SENT, 'Sent'),
        (CLOSED, 'Closed'),
    ]

    # User action status
    PENDING = 'pending'
    APPLIED = 'applied'
    IGNORED = 'ignored'
    USER_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPLIED, 'Applied'),
        (IGNORED, 'Ignored'),
    ]

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='job_posts')
    external_id = models.CharField(max_length=255, unique=True, help_text="Unique ID from platform")
    title = models.CharField(max_length=500)
    company_name = models.CharField(max_length=255, blank=True, help_text="Company name")
    job_type = models.CharField(max_length=100, blank=True, help_text="Full-time, Contract, etc.")
    location = models.CharField(max_length=255, blank=True, help_text="Location or Remote")
    skills_tags = models.TextField(blank=True, help_text="Comma-separated skills/tags")
    body = models.TextField(help_text="Job description")
    raw_html = models.TextField(blank=True, help_text="Original HTML content")
    author = models.CharField(max_length=255, blank=True, help_text="Poster username/email")
    url = models.URLField(max_length=500, help_text="Source URL")
    application_link = models.URLField(max_length=1000, blank=True, help_text="Direct application link")
    timestamp = models.DateTimeField(help_text="When posted on original platform")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NEW)
    user_status = models.CharField(max_length=20, choices=USER_STATUS_CHOICES, default=PENDING, help_text="User action status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title


class QualificationScore(models.Model):
    # AI evaluation results
    HIGH = 'high'
    MEDIUM = 'medium'
    IGNORE = 'ignore'
    CLASSIFICATION_CHOICES = [
        (HIGH, 'High'),
        (MEDIUM, 'Medium'),
        (IGNORE, 'Ignore'),
    ]

    job_post = models.OneToOneField(JobPost, on_delete=models.CASCADE, related_name='qualification')
    is_job_signal = models.BooleanField(default=False)
    confidence = models.FloatField(help_text="0.0 to 1.0")
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES)
    reasoning = models.TextField(help_text="AI explanation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_post.title} - {self.get_classification_display()} ({self.confidence:.0%})"


class DraftMessage(models.Model):
    # Auto-generated outreach
    GITHUB_COMMENT = 'github_comment'
    DIRECT_MESSAGE = 'direct_message'
    COVER_LETTER = 'cover_letter'
    PLATFORM_CHOICES = [
        (GITHUB_COMMENT, 'GitHub Comment'),
        (DIRECT_MESSAGE, 'Direct Message'),
        (COVER_LETTER, 'Cover Letter'),
    ]

    job_post = models.OneToOneField(JobPost, on_delete=models.CASCADE, related_name='draft')
    content = models.TextField()
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    cover_letter = models.TextField(blank=True, help_text="Full cover letter for job applications")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Draft for: {self.job_post.title}"


class AlertStatus(models.Model):
    # Telegram notification tracking
    job_post = models.OneToOneField(JobPost, on_delete=models.CASCADE, related_name='alert')
    sent_at = models.DateTimeField(auto_now_add=True)
    telegram_message_id = models.CharField(max_length=255)
    acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert for: {self.job_post.title}"
