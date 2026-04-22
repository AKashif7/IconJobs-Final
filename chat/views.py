from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
import json

from .models import Conversation, Message, TypingIndicator
from jobs.models import Job

# All view functions for the chat app. The messaging system is built around
# a combined inbox/conversation view, a set of AJAX endpoints for sending
# messages and managing read receipts, and a lightweight online-presence
# system that uses Django's cache framework rather than WebSockets.

# How long (in seconds) a user is considered "online" after their last ping.
ONLINE_TIMEOUT = 120


# ── Inbox ─────────────────────────────────────────────────────────────────

@login_required
def inbox(request, conversation_id=None):
    # The main chat page. It doubles as both the conversation list (sidebar)
    # and the active conversation panel. When conversation_id is provided,
    # the conversation is opened in the main area; without it, only the
    # sidebar list is shown.

    # Gather all conversations for the current user with participant and
    # message data pre-fetched to avoid N+1 queries in the loop below.
    all_convs = request.user.conversations.all().prefetch_related('participants', 'messages')

    conv_data = []
    total_unread = 0
    for conv in all_convs:
        other_user = conv.get_other_user(request.user)
        # Count only messages not yet read that were sent by the other person.
        unread = conv.messages.filter(read_at__isnull=True).exclude(sender=request.user).count()
        total_unread += unread
        try:
            other_profile = other_user.profile if other_user else None
        except Exception:
            other_profile = None
        conv_data.append({
            'conv': conv,
            'other_user': other_user,
            'other_profile': other_profile,
            'unread': unread,
        })

    context = {
        'conv_data': conv_data,
        'total_unread': total_unread,
        'active_conv': None,
    }

    if conversation_id:
        active_conv = get_object_or_404(Conversation, id=conversation_id)

        # Security check — users can only open conversations they're part of.
        if not active_conv.participants.filter(id=request.user.id).exists():
            return redirect('inbox')

        if request.method == 'POST':
            # Handle message submission from the inline form. After saving,
            # redirect back (PRG pattern) to prevent double-submission on refresh.
            content = request.POST.get('content', '').strip()
            if content:
                Message.objects.create(
                    conversation=active_conv,
                    sender=request.user,
                    content=content,
                )
                active_conv.save(update_fields=['last_message_at'])
            return redirect('inbox_conversation', conversation_id=conversation_id)

        active_other = active_conv.get_other_user(request.user)
        try:
            active_other_profile = active_other.profile if active_other else None
        except Exception:
            active_other_profile = None

        # Mark all unread messages from the other person as read now that
        # the user has opened the conversation.
        active_conv.messages.filter(read_at__isnull=True).exclude(
            sender=request.user
        ).update(read_at=timezone.now())

        active_messages = active_conv.messages.all()

        try:
            is_employer = request.user.profile.role == 'employer'
        except Exception:
            is_employer = False

        app = active_conv.application

        # Contact details are only shown in the chat banner if the application
        # has been formally accepted and the contact flag has been set.
        show_contact = bool(
            app and app.status in ('accepted', 'completed') and app.contact_revealed
        )

        # Find the ID of the last message I sent that the other person has
        # already read — used to show the "Seen" tick in the chat.
        last_read_sent = active_messages.filter(
            sender=request.user,
            read_at__isnull=False,
        ).last()
        last_read_sent_id = last_read_sent.id if last_read_sent else None

        context.update({
            'active_conv': active_conv,
            'active_other': active_other,
            'active_other_profile': active_other_profile,
            'active_messages': active_messages,
            'is_employer': is_employer,
            'show_contact': show_contact,
            'app': app,
            'last_read_sent_id': last_read_sent_id,
        })

    return render(request, 'chat/inbox.html', context)


@login_required
def conversation_detail(request, conversation_id):
    # Alternative standalone conversation view. Handles POST for message
    # sending and marks messages as read when the page loads.
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if not conversation.participants.filter(id=request.user.id).exists():
        return redirect('inbox')

    other_user = conversation.get_other_user(request.user)
    try:
        other_profile = other_user.profile if other_user else None
    except Exception:
        other_profile = None

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
            )
            conversation.save(update_fields=['last_message_at'])
        return redirect('conversation_detail', conversation_id=conversation_id)

    # Bulk-mark all incoming unread messages as read now that the user
    # has opened this conversation.
    conversation.messages.filter(read_at__isnull=True).exclude(
        sender=request.user
    ).update(read_at=timezone.now())

    msgs = conversation.messages.all()

    try:
        is_employer = request.user.profile.role == 'employer'
    except Exception:
        is_employer = False

    app = conversation.application
    show_contact = bool(
        app and app.status in ('accepted', 'completed') and app.contact_revealed
    )

    context = {
        'conversation': conversation,
        'other_user': other_user,
        'other_profile': other_profile,
        'messages': msgs,
        'application': app,
        'job': conversation.job,
        'show_contact': show_contact,
        'is_employer': is_employer,
    }
    return render(request, 'chat/conversation.html', context)


# ── AJAX messaging endpoints ──────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def send_message(request):
    # Receives the message body as JSON from the frontend, creates the
    # Message record, updates the conversation timestamp, and clears any
    # typing indicator the sender had active.
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()

        if not content:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'}, status=400)

        conversation = get_object_or_404(Conversation, id=conversation_id)
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not a participant'}, status=403)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
        )
        conversation.save(update_fields=['last_message_at'])

        # Clear the typing indicator for this user once the message is sent.
        TypingIndicator.objects.filter(conversation=conversation, user=request.user).delete()

        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content,
            'sent_at': message.sent_at.isoformat(),
            'sender_username': message.sender.username,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def mark_message_read(request):
    # Called by the frontend when the recipient opens a conversation and
    # sees a message. Stamps read_at with the current time so the sender's
    # "Seen" tick can be shown.
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        message = get_object_or_404(Message, id=message_id)

        # You can't mark your own messages as read.
        if message.sender == request.user:
            return JsonResponse({'success': False, 'error': 'Cannot mark own message as read'}, status=400)
        message.read_at = timezone.now()
        message.save(update_fields=['read_at'])
        return JsonResponse({'success': True, 'message_id': message.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def set_typing_indicator(request, conversation_id):
    # Creates or removes a TypingIndicator row for the current user in this
    # conversation. The frontend sends {is_typing: true} when the user starts
    # typing and {is_typing: false} when they stop or send the message.
    try:
        data = json.loads(request.body)
        is_typing = data.get('is_typing', True)
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not a participant'}, status=403)
        if is_typing:
            TypingIndicator.objects.update_or_create(
                conversation=conversation, user=request.user,
                defaults={'started_at': timezone.now()},
            )
        else:
            TypingIndicator.objects.filter(conversation=conversation, user=request.user).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_typing_indicators(request, conversation_id):
    # Returns a list of usernames currently typing in this conversation
    # (excluding the requester). Polled by the frontend every few seconds.
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not a participant'}, status=403)
        typing_users = list(
            TypingIndicator.objects.filter(conversation=conversation)
            .exclude(user=request.user)
            .values_list('user__username', flat=True)
        )
        return JsonResponse({'success': True, 'typing_users': typing_users})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def start_conversation(request):
    # Creates a new conversation between the current user and another user,
    # optionally linked to a specific job. If one already exists for this
    # pair (and job), the existing one is returned to avoid duplicates.
    try:
        data = json.loads(request.body)
        other_user_id = data.get('other_user_id')
        job_id = data.get('job_id')

        other_user = get_object_or_404(User, id=other_user_id)
        job = get_object_or_404(Job, id=job_id) if job_id else None

        qs = Conversation.objects.filter(participants=request.user).filter(participants=other_user)
        if job:
            qs = qs.filter(job=job)

        if qs.exists():
            conversation = qs.first()
            created = False
        else:
            conversation = Conversation.objects.create(job=job)
            conversation.participants.add(request.user, other_user)
            created = True

        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'created': created,
            'url': f'/chat/inbox/{conversation.id}/',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ── Online presence & unread count ───────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    # Returns the total number of unread messages across all conversations
    # for the current user. Polled every 15 seconds by the navbar badge.
    count = Message.objects.filter(
        conversation__participants=request.user,
        read_at__isnull=True,
    ).exclude(sender=request.user).count()
    return JsonResponse({'unread': count})


@login_required
@require_http_methods(["GET"])
def get_online_status(request):
    # Looks up whether a specific user (by uid) is online by checking their
    # last ping timestamp in the cache. Returns True if they pinged within
    # ONLINE_TIMEOUT seconds.
    uid = request.GET.get('uid')
    if uid:
        last_seen_iso = cache.get(f'online_{uid}')
        if last_seen_iso:
            return JsonResponse({'online': True, 'last_seen': last_seen_iso})
        return JsonResponse({'online': False, 'last_seen': None})
    return JsonResponse({'online': False, 'last_seen': None})


@login_required
@require_http_methods(["GET"])
def ping(request):
    # Records the current user's presence by writing their user ID and
    # timestamp to the cache with a 2-minute TTL. The frontend calls this
    # every 60 seconds to keep the "Online" dot lit while the user is active.
    now_iso = timezone.now().isoformat()
    cache.set(f'online_{request.user.id}', now_iso, ONLINE_TIMEOUT)
    return JsonResponse({'ok': True})


@login_required
@require_http_methods(["GET"])
def get_conversation_messages(request, conversation_id):
    # Returns all messages in a conversation as JSON. Used by the frontend
    # to poll for new messages and render them without a full page reload.
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not a participant'}, status=403)

        messages_data = [
            {
                'id': msg.id,
                'sender_id': msg.sender.id,
                'sender_username': msg.sender.username,
                'sender_name': msg.sender.first_name or msg.sender.username,
                'content': msg.content,
                'sent_at': msg.sent_at.isoformat(),
                'is_read': msg.is_read,
                'read_at': msg.read_at.isoformat() if msg.read_at else None,
                # is_own lets the frontend decide which side of the chat to
                # render the bubble on without needing the user's ID client-side.
                'is_own': msg.sender_id == request.user.id,
            }
            for msg in conversation.messages.all()
        ]

        return JsonResponse({'success': True, 'messages': messages_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
