from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('api/jobs/<int:job_id>/status/', views.update_job_status, name='update_job_status'),
    path('api/jobs/<int:job_id>/user-status/', views.update_user_status, name='update_user_status'),
    path('api/jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
]
