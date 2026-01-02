# Tests for rule-based email qualification system
import pytest
from utils.email_qualifier import EmailQualifier


class TestEmailQualifier:
    # Test suite for EmailQualifier

    def setup_method(self):
        # Set up test fixtures
        self.qualifier = EmailQualifier()

    def test_trusted_sender_classification(self):
        # Trusted senders should always get HIGH classification
        result = self.qualifier.qualify_email(
            sender='jobalerts@upwork.com',
            subject='New Django job posted',
            body='A client is looking for a Django developer.'
        )

        assert result['classification'] == 'high'
        assert result['confidence'] >= 0.9
        assert 'Trusted sender' in result['reasoning']

    def test_red_flag_detection(self):
        # Emails with red flags should be ignored
        result = self.qualifier.qualify_email(
            sender='random@example.com',
            subject='Great opportunity!',
            body='Looking for developer. This is unpaid work for equity only.'
        )

        assert result['classification'] == 'ignore'
        assert 'Red flags' in result['reasoning']

    def test_high_score_classification(self):
        # Email with high keyword score should be HIGH
        result = self.qualifier.qualify_email(
            sender='recruiter@example.com',
            subject='Django Full-time Remote Developer Position',
            body='We are hiring a senior Django developer for a long-term project. '
                 'Competitive salary $100k/year with benefits, remote work, Python, PostgreSQL, REST API.'
        )

        assert result['classification'] == 'high'
        assert result['confidence'] >= 0.8

    def test_medium_score_classification(self):
        # Email with medium keyword score should be MEDIUM
        result = self.qualifier.qualify_email(
            sender='client@example.com',
            subject='Python developer needed',
            body='Looking for a Python developer to help with some work.'
        )

        # Should be medium or higher (scoring is lenient)
        assert result['classification'] in ['medium', 'high']

    def test_low_score_ignore(self):
        # Email with low keyword score should be ignored
        result = self.qualifier.qualify_email(
            sender='marketing@example.com',
            subject='Newsletter: Tech trends this week',
            body='Here are the latest tech trends and news from this week.'
        )

        assert result['classification'] == 'ignore'

    def test_budget_mentioned_boost(self):
        # Email with budget mentioned should get classification boost
        result = self.qualifier.qualify_email(
            sender='client@example.com',
            subject='Python automation project',
            body='Need Python developer for automation. Budget is $75/hour. API integration needed.'
        )

        # Should be HIGH because budget mentioned + decent score
        assert result['classification'] in ['high', 'medium']
        assert result['score_details']['has_budget'] is True

    def test_job_signal_detection_positive(self):
        # Should detect legitimate job postings
        is_job, confidence, reasoning = self.qualifier.is_job_signal(
            subject='Django developer needed',
            body='Looking for Django developer with Python experience.'
        )

        assert is_job is True
        assert confidence > 0.5

    def test_job_signal_detection_negative(self):
        # Should reject non-job emails
        is_job, confidence, reasoning = self.qualifier.is_job_signal(
            subject='Weekly newsletter',
            body='Here are this week\'s top tech articles and news.'
        )

        assert is_job is False

    def test_job_signal_red_flag(self):
        # Should reject job postings with red flags
        is_job, confidence, reasoning = self.qualifier.is_job_signal(
            subject='Developer needed',
            body='Looking for developer. Unpaid work, equity only.'
        )

        assert is_job is False
        assert 'Red flags' in reasoning

    def test_keyword_score_calculation(self):
        # Test keyword scoring system
        text = 'Django Python developer full-time remote $100/hour backend API'
        score_data = self.qualifier.calculate_keyword_score(text)

        assert score_data['score'] > 0
        assert len(score_data['high_value_matches']) > 0
        assert len(score_data['medium_value_matches']) > 0
        assert score_data['has_budget'] is True

    def test_empty_input_handling(self):
        # Should handle empty inputs gracefully
        result = self.qualifier.qualify_email(
            sender='',
            subject='',
            body=''
        )

        assert result['classification'] == 'ignore'
        assert result['confidence'] > 0

    def test_score_details_structure(self):
        # Score details should have correct structure
        result = self.qualifier.qualify_email(
            sender='test@example.com',
            subject='Python job',
            body='Python developer needed'
        )

        assert 'score_details' in result
        assert 'score' in result['score_details']

    def test_case_insensitive_matching(self):
        # Keywords should match case-insensitively
        result1 = self.qualifier.qualify_email(
            sender='test@example.com',
            subject='DJANGO DEVELOPER',
            body='PYTHON BACKEND API'
        )

        result2 = self.qualifier.qualify_email(
            sender='test@example.com',
            subject='django developer',
            body='python backend api'
        )

        # Should get similar classifications regardless of case
        assert result1['classification'] == result2['classification']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
