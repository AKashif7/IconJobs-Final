from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('jobseeker', 'Job Seeker'),
        ('employer', 'Employer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    cv = models.FileField(upload_to='cvs/', blank=True, null=True)

    # Job seeker specific
    skills = models.TextField(blank=True, help_text="Comma separated skills")
    availability = models.CharField(max_length=100, blank=True)

    # Employer specific
    company_name = models.CharField(max_length=150, blank=True)
    company_description = models.TextField(blank=True)
    website = models.URLField(blank=True)

    # Contact reveal (only after acceptance)
    reveal_phone = models.BooleanField(default=False)
    reveal_email = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def average_rating(self):
        ratings = self.ratings_received.all()
        if not ratings:
            return None
        return round(sum(r.score for r in ratings) / len(ratings), 1)

    @property
    def jobs_completed(self):
        from jobs.models import Application
        return Application.objects.filter(
            applicant=self.user,
            status='completed'
        ).count()


class Rating(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    reviewed = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='ratings_received')
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reviewer', 'reviewed')

    def __str__(self):
        return f"{self.reviewer.username} rated {self.reviewed.user.username}: {self.score}/5"
