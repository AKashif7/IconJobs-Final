from django.db import models
from django.contrib.auth.models import User

# Database models for the chat app. Three tables power the messaging system:
# Conversation groups the participants and links back to the job that prompted
# the chat; Message stores individual messages with read-receipt timestamps;
# and TypingIndicator is a lightweight, auto-cleaned table for the "is typing"
# feature shown in real time.


class Conversation(models.Model):
    # A conversation links two users (employer + job seeker) around a
    # specific job. It's created automatically when an employer accepts an
    # applicant, so the first message is the acceptance notification.
    participants = models.ManyToManyField(User, related_name='conversations')

    # Optional link back to the job — keeps the conversation in context
    # and allows contact details to be revealed based on application status.
    job = models.ForeignKey(
        'jobs.Job', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conversations', help_text="Optional: link to specific job"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # auto_now updates this every time a message is added, so the inbox
    # can sort conversations by most recently active.
    last_message_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        participant_names = ', '.join([u.username for u in self.participants.all()])
        return f"Chat: {participant_names}"

    def get_other_user(self, user):
        # Returns the other participant in the conversation (not the current user).
        # Used throughout the inbox to know whose name/avatar to display.
        return self.participants.exclude(id=user.id).first()

    @property
    def last_message(self):
        return self.messages.last()

    @property
    def application(self):
        # Looks up the Application record that corresponds to this conversation,
        # so the chat template can show the application status and decide
        # whether to reveal contact details.
        from jobs.models import Application
        if not self.job:
            return None
        for p in self.participants.all():
            try:
                return Application.objects.get(job=self.job, applicant=p)
            except Application.DoesNotExist:
                pass
        return None


class Message(models.Model):
    # Each row is one message in a conversation. sent_at is set on creation;
    # read_at is null until the recipient opens the conversation — that's
    # how the unread count badge and read receipts work.
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True, help_text="When message was read by recipient")

    class Meta:
        # Always return messages in chronological order so the chat view
        # renders them oldest-to-newest without extra sorting.
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    @property
    def is_read(self):
        return self.read_at is not None

    @property
    def created_at(self):
        # Alias so templates can use created_at consistently across models.
        return self.sent_at

    @property
    def is_system(self):
        # Placeholder for a future system-message type. Always False for now
        # but kept here so the template doesn't need changing later.
        return False


class TypingIndicator(models.Model):
    # Temporarily records that a user is typing in a conversation. The view
    # creates this on a "typing started" ping and deletes it when they stop
    # or send a message. unique_together means one record per (user, conversation).
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='typing_indicators')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user.username} is typing in {self.conversation}"
