from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Conversation, Message
from jobs.models import Application


def _get_user_conversations(user):
    """Return all conversations for a user (employer or seeker)."""
    as_employer = Conversation.objects.filter(application__job__employer=user)
    as_seeker   = Conversation.objects.filter(
        application__applicant=user,
        application__status='accepted'
    )
    return (as_employer | as_seeker).distinct().order_by('-created_at')


@login_required
def inbox(request, conv_pk=None):
    user = request.user
    conversations = _get_user_conversations(user)

    # Annotate each conversation with unread count
    conv_data = []
    total_unread = 0
    for conv in conversations:
        unread = conv.unread_count_for(user)
        total_unread += unread
        other = (conv.application.applicant
                 if user == conv.application.job.employer
                 else conv.application.job.employer)
        try:
            other_profile = other.profile
        except Exception:
            other_profile = None
        conv_data.append({
            'conv': conv,
            'unread': unread,
            'other_user': other,
            'other_profile': other_profile,
        })

    # Active conversation
    active_conv = None
    active_messages = []
    active_other = None
    active_other_profile = None
    is_employer = False
    show_contact = False

    if conv_pk:
        active_conv = get_object_or_404(Conversation, pk=conv_pk)
        app = active_conv.application
        is_employer = (user == app.job.employer)
        is_seeker   = (user == app.applicant)

        if not (is_employer or is_seeker):
            django_messages.error(request, 'No access.')
            return redirect('inbox')

        # Mark as read
        now = timezone.now()
        if is_employer:
            active_conv.employer_last_read = now
            active_conv.save(update_fields=['employer_last_read'])
        else:
            active_conv.seeker_last_read = now
            active_conv.save(update_fields=['seeker_last_read'])

        if request.method == 'POST':
            content = request.POST.get('content', '').strip()
            if content:
                Message.objects.create(
                    conversation=active_conv,
                    sender=user,
                    content=content
                )
            return redirect('inbox_conv', conv_pk=conv_pk)

        active_messages = active_conv.messages.all()
        active_other = app.applicant if is_employer else app.job.employer
        show_contact = app.contact_revealed
        try:
            active_other_profile = active_other.profile
        except Exception:
            active_other_profile = None
    elif request.method == 'POST':
        # POST with no conv_pk — ignore
        pass

    return render(request, 'chat/inbox.html', {
        'conv_data': conv_data,
        'total_unread': total_unread,
        'active_conv': active_conv,
        'active_messages': active_messages,
        'active_other': active_other,
        'active_other_profile': active_other_profile,
        'is_employer': is_employer,
        'show_contact': show_contact,
    })


@login_required
def unread_count_api(request):
    """JSON endpoint: returns total unread message count for the nav badge."""
    conversations = _get_user_conversations(request.user)
    total = sum(c.unread_count_for(request.user) for c in conversations)
    return JsonResponse({'unread': total})


@login_required
def online_status_api(request):
    """JSON endpoint: returns last_login timestamp for a given user id."""
    uid = request.GET.get('uid')
    if not uid:
        return JsonResponse({'online': False})
    from django.contrib.auth.models import User
    try:
        u = User.objects.get(pk=uid)
        # Consider "online" if last_login within 5 minutes
        online = False
        if u.last_login:
            delta = timezone.now() - u.last_login
            online = delta.total_seconds() < 300
        return JsonResponse({'online': online, 'last_seen': u.last_login.isoformat() if u.last_login else None})
    except User.DoesNotExist:
        return JsonResponse({'online': False})
