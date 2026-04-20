from django.contrib import admin
from .models import Conversation, Message, TypingIndicator


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_participants', 'job', 'created_at', 'last_message_at']
    list_filter = ['created_at']
    search_fields = ['participants__username']
    
    def get_participants(self, obj):
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
    list_display = ['user', 'conversation', 'started_at']
    list_filter = ['started_at']
    search_fields = ['user__username']