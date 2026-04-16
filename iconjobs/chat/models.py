from django.db import models
from django.contrib.auth.models import User
from jobs.models import Application


class Conversation(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    employer_last_read = models.DateTimeField(null=True, blank=True)
    seeker_last_read = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Chat: {self.application.applicant.username} <-> {self.application.job.employer.username} re: {self.application.job.title}"

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count_for(self, user):
        from django.utils import timezone
        if user == self.application.job.employer:
            last_read = self.employer_last_read
        else:
            last_read = self.seeker_last_read

        if last_read is None:
            return self.messages.exclude(sender=user).count()
        return self.messages.exclude(sender=user).filter(created_at__gt=last_read).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
