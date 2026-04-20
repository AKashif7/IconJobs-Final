from django.urls import path
from . import views

urlpatterns = [
    # Existing routes
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile_username'),
    path('rate/<str:username>/', views.rate_user, name='rate_user'),
    
    # NEW: Document upload and verification
    path('documents/upload/', views.upload_documents_view, name='upload_documents'),
    path('api/documents/<int:user_id>/', views.get_user_documents_api, name='get_user_documents_api'),
    path('api/verification/status/', views.verification_status_api, name='verification_status_api'),
    
    # NEW: Admin verification dashboard
    path('admin/verification/', views.admin_verification_dashboard, name='admin_verification_dashboard'),
    path('admin/verification/review/<int:user_id>/', views.admin_review_user, name='admin_review_user'),
    path('admin/verification/approve/<int:user_id>/', views.admin_approve_user, name='admin_approve_user'),
    path('admin/verification/reject/<int:user_id>/', views.admin_reject_user, name='admin_reject_user'),
]
