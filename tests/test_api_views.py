# Unit tests for internal REST / AJAX API views
# Run: python manage.py test tests.test_api_views
import json
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import JobPost, Source


class InternalAPITests(TestCase):
    """Test suite for internal REST/AJAX endpoints in core.views."""

    def setUp(self):
        self.client = Client()
        self.source = Source.objects.create(
            type=Source.GITHUB_ISSUE,
            identifier='test_source',
            name='Test Source',
            is_active=True,
        )
        self.job = JobPost.objects.create(
            source=self.source,
            external_id='internal_test_001',
            title='Python Full-Stack Developer',
            body='Looking for Django & React expert',
            author='test_author',
            url='https://example.com/job/1',
            timestamp=timezone.now(),
            status=JobPost.NEW,
            user_status=JobPost.PENDING,
        )

    def test_update_job_status_success(self):
        """Test successfully updating job status via POST /api/jobs/<job_id>/status/."""
        url = reverse('update_job_status', kwargs={'job_id': self.job.id})
        payload = {'status': JobPost.ALERTED}
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobPost.ALERTED)

    def test_update_job_status_invalid_status(self):
        """Test update job status with an invalid status code returns 400."""
        url = reverse('update_job_status', kwargs={'job_id': self.job.id})
        payload = {'status': 'INVALID_STATUS'}
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Invalid status', data['message'])

    def test_update_job_status_not_found(self):
        """Test update job status on non-existent job returns 404."""
        url = reverse('update_job_status', kwargs={'job_id': 99999})
        payload = {'status': JobPost.SENT}
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Job not found')

    def test_update_job_status_invalid_json(self):
        """Test update job status with malformed JSON body returns 400."""
        url = reverse('update_job_status', kwargs={'job_id': self.job.id})
        response = self.client.post(
            url,
            data='invalid json content',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_update_user_status_success(self):
        """Test successfully updating user tracking status via POST /api/jobs/<job_id>/user-status/."""
        url = reverse('update_user_status', kwargs={'job_id': self.job.id})
        payload = {'user_status': JobPost.APPLIED}
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.job.refresh_from_db()
        self.assertEqual(self.job.user_status, JobPost.APPLIED)

    def test_update_user_status_invalid_status(self):
        """Test update user status with an invalid choice returns 400."""
        url = reverse('update_user_status', kwargs={'job_id': self.job.id})
        payload = {'user_status': 'UNKNOWN_STATUS'}
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Invalid user status', data['message'])

    def test_update_user_status_not_found(self):
        """Test update user status on non-existent job returns 404."""
        url = reverse('update_user_status', kwargs={'job_id': 99999})
        payload = {'user_status': JobPost.APPLIED}
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])

    def test_delete_job_success(self):
        """Test successfully deleting a job via DELETE /api/jobs/<job_id>/delete/."""
        url = reverse('delete_job', kwargs={'job_id': self.job.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(JobPost.objects.filter(id=self.job.id).exists())

    def test_delete_job_not_found(self):
        """Test delete on non-existent job returns 404."""
        url = reverse('delete_job', kwargs={'job_id': 99999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Job not found')
