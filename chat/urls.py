from django.urls import path
from django.shortcuts import redirect
from . import views

# URL patterns for the chat app. All routes are mounted under /chat/ in the
# project urls.py. The inbox view is reused for both the conversation list
# (no ID) and individual conversations (with ID), keeping the layout in one
# template. The /api/ routes are JSON endpoints called by JavaScript on the
# frontend — they don't render HTML.

urlpatterns = [
    # Main inbox view — shows the conversation list with no active conversation.
    path('inbox/', views.inbox, name='inbox'),

    # Same inbox view, but with a specific conversation opened in the panel.
    path('inbox/<int:conversation_id>/', views.inbox, name='inbox_conversation'),

    # Redirect /chat/ to the inbox so the chat icon in the navbar works.
    path('', lambda req: redirect('inbox'), name='conversations_list'),

    # Standalone conversation detail page (alternative to the split inbox view).
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),

    # AJAX: Start a new conversation or return an existing one.
    path('api/start/', views.start_conversation, name='start_conversation'),

    # AJAX: Fetch all messages for a conversation (used for polling).
    path('api/<int:conversation_id>/messages/', views.get_conversation_messages, name='get_conversation_messages'),

    # AJAX: Send a new message.
    path('api/message/send/', views.send_message, name='send_message'),

    # AJAX: Mark a specific message as read.
    path('api/message/read/', views.mark_message_read, name='mark_message_read'),

    # AJAX: Set or clear the "is typing" indicator for a conversation.
    path('api/<int:conversation_id>/typing/', views.set_typing_indicator, name='set_typing_indicator'),
    path('api/<int:conversation_id>/typing/get/', views.get_typing_indicators, name='get_typing_indicators'),

    # AJAX: Get the total unread message count across all conversations
    # (used by the navbar badge).
    path('api/unread/', views.get_unread_count, name='get_unread_count'),

    # AJAX: Check whether a specific user is currently online.
    path('api/online/', views.get_online_status, name='get_online_status'),

    # AJAX: Record the current user's heartbeat to keep their online status alive.
    path('api/ping/', views.ping, name='ping'),
]
