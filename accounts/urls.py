from django.urls import path
from . import views

# URL patterns for the accounts app. All of these are mounted under /accounts/
# in the root urls.py, so register/ becomes /accounts/register/, etc.
# The admin verification routes are custom pages I built on top of Django's
# standard admin panel to give a more user-friendly review experience.

urlpatterns = [
    # Standard authentication routes.
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile routes — edit/ must come before the parameterised profile/<username>/
    # so Django doesn't try to treat "edit" as a username.
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile_username'),

    # Ratings — employers post to this after working with a seeker.
    path('rate/<str:username>/', views.rate_user, name='rate_user'),

    # Document upload page for job seeker verification submissions.
    path('documents/upload/', views.upload_documents_view, name='upload_documents'),

    # JSON APIs used by admin pages and the application form.
    path('api/documents/<int:user_id>/', views.get_user_documents_api, name='get_user_documents_api'),
    path('api/verification/status/', views.verification_status_api, name='verification_status_api'),

    # Admin-only verification dashboard and action endpoints.
    path('admin/verification/', views.admin_verification_dashboard, name='admin_verification_dashboard'),
    path('admin/verification/review/<int:user_id>/', views.admin_review_user, name='admin_review_user'),
    path('admin/verification/approve/<int:user_id>/', views.admin_approve_user, name='admin_approve_user'),
    path('admin/verification/reject/<int:user_id>/', views.admin_reject_user, name='admin_reject_user'),
]
