from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from json import loads, dumps
import logging

from .models import JobPost, QualificationScore

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'core/home.html')


class JobListView(ListView):
    # Dashboard view for job listings with filtering and search
    model = JobPost
    template_name = 'core/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 20

    def get_queryset(self):
        queryset = JobPost.objects.select_related(
            'source',
            'qualification'
        ).order_by('-timestamp')

        status = self.request.GET.get('status')
        if status and status in [choice[0] for choice in JobPost.STATUS_CHOICES]:
            queryset = queryset.filter(status=status)

        classification = self.request.GET.get('classification')
        if classification:
            queryset = queryset.filter(
                qualification__classification=classification
            )

        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(author__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = JobPost.STATUS_CHOICES
        context['classification_choices'] = QualificationScore.CLASSIFICATION_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_classification'] = self.request.GET.get('classification', '')
        context['current_search'] = self.request.GET.get('q', '')
        jobs_data = []
        for job in context['jobs']:
            job_dict = {
                'id': job.id,
                'title': job.title,
                'body': job.body,
                'author': job.author,
                'url': job.url,
                'status': job.status,
                'user_status': job.user_status,
                'timestamp': job.timestamp.isoformat(),
                'source_name': job.source.name or job.source.identifier,
                'qualification': None
            }

            try:
                if job.qualification:
                    job_dict['qualification'] = {
                        'classification': job.qualification.classification,
                        'confidence': job.qualification.confidence,
                        'is_job_signal': job.qualification.is_job_signal,
                    }
            except QualificationScore.DoesNotExist:
                pass

            jobs_data.append(job_dict)

        context['jobs_json'] = dumps(jobs_data)

        return context


class JobDetailView(DetailView):
    # Detailed view for a single job posting
    model = JobPost
    template_name = 'core/job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return JobPost.objects.select_related(
            'source',
            'qualification',
            'draft',
            'alert'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = JobPost.STATUS_CHOICES
        return context


@require_http_methods(["POST"])
@csrf_exempt
def update_job_status(request, job_id):
    # AJAX endpoint to update job status
    try:
        job = JobPost.objects.get(id=job_id)
        data = loads(request.body)
        new_status = data.get('status')
        valid_statuses = [choice[0] for choice in JobPost.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }, status=400)

        job.status = new_status
        job.save(update_fields=['status', 'updated_at'])

        logger.info(f"Job {job_id} status updated to {new_status}")

        return JsonResponse({
            'success': True,
            'message': f'Job status updated to {new_status}',
            'status': job.get_status_display()
        })

    except JobPost.DoesNotExist:
        logger.warning(f"Attempted to update non-existent job {job_id}")
        return JsonResponse({
            'success': False,
            'message': 'Job not found'
        }, status=404)

    except ValueError as e:
        logger.error(f"Invalid JSON in update_job_status: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON in request body'
        }, status=400)

    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating job status: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def update_user_status(request, job_id):
    # AJAX endpoint to update job user status
    try:
        job = JobPost.objects.get(id=job_id)
        data = loads(request.body)
        new_user_status = data.get('user_status')
        valid_statuses = [choice[0] for choice in JobPost.USER_STATUS_CHOICES]
        if new_user_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'message': f'Invalid user status. Must be one of: {", ".join(valid_statuses)}'
            }, status=400)

        job.user_status = new_user_status
        job.save(update_fields=['user_status', 'updated_at'])

        logger.info(f"Job {job_id} user_status updated to {new_user_status}")

        return JsonResponse({
            'success': True,
            'message': f'Job marked as {new_user_status}',
            'user_status': job.get_user_status_display()
        })

    except JobPost.DoesNotExist:
        logger.warning(f"Attempted to update non-existent job {job_id}")
        return JsonResponse({
            'success': False,
            'message': 'Job not found'
        }, status=404)

    except ValueError as e:
        logger.error(f"Invalid JSON in update_user_status: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON in request body'
        }, status=400)

    except Exception as e:
        logger.error(f"Error updating job {job_id} user status: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating user status: {str(e)}'
        }, status=500)


@require_http_methods(["DELETE"])
@csrf_exempt
def delete_job(request, job_id):
    # AJAX endpoint to delete a job
    try:
        job = JobPost.objects.get(id=job_id)
        job_title = job.title
        job.delete()

        logger.info(f"Job {job_id} ({job_title}) deleted")

        return JsonResponse({
            'success': True,
            'message': f'Job "{job_title}" deleted successfully'
        })

    except JobPost.DoesNotExist:
        logger.warning(f"Attempted to delete non-existent job {job_id}")
        return JsonResponse({
            'success': False,
            'message': 'Job not found'
        }, status=404)

    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error deleting job: {str(e)}'
        }, status=500)
