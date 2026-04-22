from django.contrib import admin
from .models import Conversation, Message, TypingIndicator

# Registers the chat app's models with Django's admin panel so conversations
# and messages can be inspected and deleted if needed (e.g. for moderation).
# TypingIndicator is registered mainly for debugging — in normal use these
# rows are created and deleted in seconds.


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_participants', 'job', 'created_at', 'last_message_at']
    list_filter = ['created_at']
    search_fields = ['participants__username']

    def get_participants(self, obj):
        # Custom column that lists all participant usernames in one cell,
        # since participants is a ManyToMany field and can't be shown directly.
        return ', '.join([u.username for u in obj.participants.all()])
    get_participants.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'sent_at', 'is_read']
    list_filter = ['sent_at', 'read_at']
    search_fields = ['sender__username', 'content']
    readonly_fields = ['sent_at']


@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    # Rarely needs manual management, but useful during development to check
    # whether indicators are being created and cleaned up correctly.
    list_display = ['user', 'conversation', 'started_at']
    list_filter = ['started_at']
    search_fields = ['user__username']
