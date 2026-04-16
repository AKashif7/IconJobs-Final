from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:conv_pk>/', views.inbox, name='inbox_conv'),
    path('api/unread/', views.unread_count_api, name='unread_count_api'),
    path('api/online/', views.online_status_api, name='online_status_api'),
]

from django.views.decorators.http import require_POST as _rp
from django.contrib.auth.decorators import login_required as _lr
from django.utils import timezone as _tz
from django.http import JsonResponse as _jr
from django.contrib.auth.models import User as _U

@_lr
def ping_activity(request):
    """Called by JS to keep last_login fresh while user is active on the page."""
    _U.objects.filter(pk=request.user.pk).update(last_login=_tz.now())
    return _jr({'ok': True})

urlpatterns += [path('api/ping/', ping_activity, name='ping_activity')]
