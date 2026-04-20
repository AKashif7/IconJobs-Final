from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
import json

from .models import Conversation, Message, TypingIndicator
from jobs.models import Job


@login_required
def inbox(request, conversation_id=None):
    all_convs = request.user.conversations.all().prefetch_related('participants', 'messages')

    conv_data = []
    total_unread = 0
    for conv in all_convs:
        other_user = conv.get_other_user(request.user)
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
        if not active_conv.participants.filter(id=request.user.id).exists():
            return redirect('inbox')

        if request.method == 'POST':
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

        active_conv.messages.filter(read_at__isnull=True).exclude(
            sender=request.user
        ).update(read_at=timezone.now())

        active_messages = active_conv.messages.all()

        try:
            is_employer = request.user.profile.role == 'employer'
        except Exception:
            is_employer = False

        app = active_conv.application
        show_contact = bool(
            app and app.status in ('accepted', 'completed') and app.contact_revealed
        )

        context.update({
            'active_conv': active_conv,
            'active_other': active_other,
            'active_other_profile': active_other_profile,
            'active_messages': active_messages,
            'is_employer': is_employer,
            'show_contact': show_contact,
            'app': app,
        })

    return render(request, 'chat/inbox.html', context)


@login_required
def conversation_detail(request, conversation_id):
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


@login_required
@require_http_methods(["POST"])
def send_message(request):
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
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        message = get_object_or_404(Message, id=message_id)
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
    try:
        data = json.loads(request.body)
        other_user_id = data.get('other_user_id')
        job_id = data.get('job_id')

        other_user = get_object_or_404(User, id=other_user_id)
        job = get_object_or_404(Job, id=job_id) if job_id else None

        # Find an existing conversation between exactly these two users
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


@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    count = Message.objects.filter(
        conversation__participants=request.user,
        read_at__isnull=True,
    ).exclude(sender=request.user).count()
    return JsonResponse({'unread': count})


@login_required
@require_http_methods(["GET"])
def get_online_status(request):
    return JsonResponse({'online': False, 'last_seen': None})


@login_required
@require_http_methods(["GET"])
def ping(request):
    return JsonResponse({'ok': True})


@login_required
@require_http_methods(["GET"])
def get_conversation_messages(request, conversation_id):
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
                'is_own': msg.sender_id == request.user.id,
            }
            for msg in conversation.messages.all()
        ]

        return JsonResponse({'success': True, 'messages': messages_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
