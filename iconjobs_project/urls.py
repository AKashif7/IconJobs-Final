from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Root URL configuration for the entire IconJobs platform. Every incoming
# request passes through here first, and Django routes it to the right app
# based on the URL prefix. Think of this as the main switchboard.

urlpatterns = [
    # Django's built-in admin panel — accessible to staff users only.
    path('admin/', admin.site.urls),

    # All user account routes (register, login, logout, profile, etc.)
    # are handled inside the accounts app.
    path('accounts/', include('accounts.urls')),

    # Messaging routes (inbox, conversations, API endpoints for real-time
    # features) are namespaced under /chat/.
    path('chat/', include('chat.urls')),

    # The jobs app owns the root URL, so the homepage, job listings,
    # dashboards, and application routes all live under /.
    path('', include('jobs.urls')),

# During development, Django itself serves uploaded media files (profile
# photos, CVs, documents). In production this would be handled by a web
# server like Nginx instead.
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
