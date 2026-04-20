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

    # NEW: Verification system
    is_verified = models.BooleanField(default=False, help_text="Admin has verified this user")
    blue_tick_awarded = models.BooleanField(default=False, help_text="User has blue tick badge")
    verification_submitted_at = models.DateTimeField(null=True, blank=True, help_text="When user submitted documents")
    legal_name = models.CharField(max_length=200, blank=True, help_text="User's legal full name")
    phone_for_otp = models.CharField(max_length=20, blank=True, help_text="Phone number for OTP verification")

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


class UserDocument(models.Model):
    """Store uploaded documents for job seekers (DBS, NIN, work permits, etc.)"""
    DOCUMENT_TYPES = [
        ('profile_photo', 'Profile Photo'),
        ('dbs_check', 'DBS Check Certificate'),
        ('national_insurance', 'National Insurance Document'),
        ('work_permit_visa', 'Work Permit / Visa'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='user_documents/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size_bytes = models.IntegerField()
    is_verified = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'document_type')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"


class VerificationQueue(models.Model):
    """Admin queue for reviewing user documents"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_queue')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='verifications_reviewed')
    rejection_reason = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"


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
