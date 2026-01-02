from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SignalDetector:
    # Simple keyword-based job signal detector

    def __init__(self):
        self.keywords = [kw.strip().lower() for kw in settings.JOB_KEYWORDS.split(',')]

    def is_job_signal(self, text):
        # Detect if text contains job signals
        if not text:
            return False, 0.0

        text_lower = text.lower()
        matches = 0
        for keyword in self.keywords:
            if keyword in text_lower:
                matches += 1

        if matches == 0:
            return False, 0.0
        elif matches == 1:
            return True, 0.6
        elif matches == 2:
            return True, 0.8
        else:
            return True, 0.9

    def classify_job(self, job_post):
        # Classify job quality
        text = f"{job_post.title} {job_post.body}".lower()

        high_indicators = ['django', 'full-time', 'long-term', '$', 'budget', 'hourly', 'monthly']
        medium_indicators = ['python', 'api', 'backend', 'automation']

        high_count = sum(1 for ind in high_indicators if ind in text)
        medium_count = sum(1 for ind in medium_indicators if ind in text)

        if high_count >= 2:
            return 'high'
        elif high_count >= 1 or medium_count >= 2:
            return 'medium'
        else:
            return 'ignore'
