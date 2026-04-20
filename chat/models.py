from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):
    """Represents a conversation between two users"""
    participants = models.ManyToManyField(User, related_name='conversations')
    job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True,
                           related_name='conversations', help_text="Optional: link to specific job")
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        participant_names = ', '.join([u.username for u in self.participants.all()])
        return f"Chat: {participant_names}"

    def get_other_user(self, user):
        """Get the other participant in a 1-on-1 conversation"""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    """Individual messages in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True, help_text="When message was read by recipient")

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    @property
    def is_read(self):
        return self.read_at is not None


class TypingIndicator(models.Model):
    """Track who's typing in real-time (temporary, auto-cleaned)"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='typing_indicators')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user.username} is typing in {self.conversation}"
