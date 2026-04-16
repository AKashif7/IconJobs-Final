from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/saved/', views.saved_jobs, name='saved_jobs'),
    path('jobs/post/', views.post_job, name='post_job'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('jobs/<int:pk>/save/', views.save_job, name='save_job'),
    path('jobs/<int:pk>/edit/', views.edit_job, name='edit_job'),
    path('jobs/<int:pk>/close/', views.close_job, name='close_job'),
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('employer/jobs/<int:job_pk>/applicants/', views.view_applicants, name='view_applicants'),
    path('employer/applications/<int:app_pk>/update/', views.update_application, name='update_application'),
    path('jobseeker/dashboard/', views.jobseeker_dashboard, name='jobseeker_dashboard'),
]
