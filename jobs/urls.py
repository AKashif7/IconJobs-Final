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
    path('career-guide/', views.career_guide, name='career_guide'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('api/search/suggestions/', views.get_job_title_suggestions, name='job_title_suggestions'),
    path('api/search/', views.search_jobs, name='search_jobs'),
    
    # NEW: Job applications with CV uploads
    path('<int:job_id>/apply/', views.apply_for_job, name='apply_for_job'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/', views.application_detail, name='application_detail'),
    path('employer/applications/', views.job_applications_for_employer, name='employer_applications'),
    path('api/application/<int:application_id>/status/', views.update_application_status, name='update_application_status'),
    path('api/application/<int:application_id>/documents/', views.get_application_documents, name='get_application_documents'),
]
