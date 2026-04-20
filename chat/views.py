from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
import json

from .models import Conversation, Message, TypingIndicator
from jobs.models import Job


@login_required
@require_http_methods(["GET"])
def conversations_list(request):
    """
    Show all conversations for the current user
    """
    conversations = request.user.conversations.all().prefetch_related('participants', 'messages')
    
    # Enrich with last message and unread count
    conv_data = []
    for conv in conversations:
        other_user = conv.get_other_user(request.user)
        unread = conv.messages.filter(read_at__isnull=True).exclude(sender=request.user).count()
        last_msg = conv.messages.last()
        
        conv_data.append({
            'conversation': conv,
            'other_user': other_user,
            'unread_count': unread,
            'last_message': last_msg,
        })

    context = {'conversations': conv_data}
    return render(request, 'chat/conversations_list.html', context)


@login_required
@require_http_methods(["GET"])
def conversation_detail(request, conversation_id):
    """
    Detailed conversation view - messages between two users
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check user is participant
    if not conversation.participants.filter(id=request.user.id).exists():
        return redirect('conversations_list')

    # Get other user
    other_user = conversation.get_other_user(request.user)
    
    # Get all messages
    messages = conversation.messages.all()
    
    # Mark messages as read
    unread_messages = messages.filter(read_at__isnull=True).exclude(sender=request.user)
    unread_messages.update(read_at=timezone.now())

    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages,
        'job': conversation.job
    }
    return render(request, 'chat/conversation_detail.html', context)


@login_required
@require_http_methods(["POST"])
def send_message(request):
    """
    AJAX endpoint: Send a message in a conversation
    """
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()

        if not content:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'}, status=400)

        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Check user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not a participant'}, status=403)

        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        # Update conversation timestamp
        conversation.save(update_fields=['last_message_at'])

        # Clear typing indicator
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
    """
    AJAX endpoint: Mark a message as read
    """
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')

        message = get_object_or_404(Message, id=message_id)
        
        # Only the recipient can mark as read
        if message.sender == request.user:
            return JsonResponse({
                'success': False,
                'error': 'Cannot mark your own message as read'
            }, status=400)

        message.read_at = timezone.now()
        message.save(update_fields=['read_at'])

        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'read_at': message.read_at.isoformat()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def set_typing_indicator(request):
    """
    AJAX endpoint: User is typing
    (In production, you'd use WebSocket for real-time. This uses polling)
    """
    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        is_typing = data.get('is_typing', True)

        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not a participant'}, status=403)

        if is_typing:
            # Create or update typing indicator
            TypingIndicator.objects.update_or_create(
                conversation=conversation,
                user=request.user
            )
        else:
            # Remove typing indicator
            TypingIndicator.objects.filter(conversation=conversation, user=request.user).delete()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_typing_indicators(request, conversation_id):
    """
    AJAX endpoint: Get who's currently typing in a conversation
    """
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not a participant'}, status=403)

        # Get users typing (exclude current user)
        typing_users = TypingIndicator.objects.filter(
            conversation=conversation
        ).exclude(user=request.user).values_list('user__username', flat=True)

        return JsonResponse({
            'success': True,
            'typing_users': list(typing_users)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def start_conversation(request):
    """
    Create or get existing conversation between two users
    """
    try:
        data = json.loads(request.body)
        other_user_id = data.get('other_user_id')
        job_id = data.get('job_id')  # Optional: link to a job

        other_user = get_object_or_404(User, id=other_user_id)
        job = None
        if job_id:
            job = get_object_or_404(Job, id=job_id)

        # Create or get conversation
        conversation, created = Conversation.objects.get_or_create(
            job=job
        )

        # Add participants if not already there
        conversation.participants.add(request.user, other_user)

        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'created': created,
            'url': f'/chat/{conversation.id}/'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_conversation_messages(request, conversation_id):
    """
    AJAX endpoint: Get all messages in a conversation (for pagination/refresh)
    """
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if not conversation.participants.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Not a participant'}, status=403)

        messages = conversation.messages.all()
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'sender_id': msg.sender.id,
                'sender_username': msg.sender.username,
                'sender_name': msg.sender.first_name or msg.sender.username,
                'content': msg.content,
                'sent_at': msg.sent_at.isoformat(),
                'is_read': msg.is_read,
                'read_at': msg.read_at.isoformat() if msg.read_at else None,
                'is_own_message': msg.sender == request.user
            })

        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'total': len(messages_data)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
