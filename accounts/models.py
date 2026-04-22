from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Database models for the accounts app. This file defines the shape of every
# user-related table in the database: profiles, uploaded documents, the
# verification queue that admins review, and the rating system that lets
# employers score job seekers they've worked with.


class UserProfile(models.Model):
    # Every registered user is either a job seeker or an employer. This drives
    # which fields are shown, which pages they can access, and what actions
    # they're allowed to take throughout the platform.
    ROLE_CHOICES = [
        ('jobseeker', 'Job Seeker'),
        ('employer', 'Employer'),
    ]

    # One-to-one relationship with Django's built-in User model. When a User
    # is deleted, their profile is deleted too (CASCADE).
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Fields shared between both user types.
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

    # Contact details (phone/email) are hidden by default and only revealed
    # to an employer once they've formally accepted an applicant for a job.
    reveal_phone = models.BooleanField(default=False)
    reveal_email = models.BooleanField(default=False)

    # Verification system — admins review uploaded documents and can award a
    # blue tick badge to verified job seekers, building trust on the platform.
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
        # Calculates the mean score across all ratings this user has received.
        # Returns None if they haven't been rated yet, so templates can show
        # "No ratings yet" rather than 0/5.
        ratings = self.ratings_received.all()
        if not ratings:
            return None
        return round(sum(r.score for r in ratings) / len(ratings), 1)

    @property
    def jobs_completed(self):
        # Counts how many jobs this seeker has had marked as 'completed' by
        # an employer — used on the profile page as a trust signal.
        from jobs.models import Application
        return Application.objects.filter(
            applicant=self.user,
            status='completed'
        ).count()


class UserDocument(models.Model):
    # Stores the actual uploaded files that job seekers submit for identity
    # verification (DBS check, National Insurance, work permit, etc.).
    # Each user can have at most one document per type (unique_together).
    DOCUMENT_TYPES = [
        ('profile_photo', 'Profile Photo'),
        ('dbs_check', 'DBS Check Certificate'),
        ('national_insurance', 'National Insurance Document'),
        ('work_permit_visa', 'Work Permit / Visa'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)

    # Files are organised into dated folders (uploads/user_documents/YYYY/MM/DD/)
    # so they don't all pile into one flat directory.
    file = models.FileField(upload_to='user_documents/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size_bytes = models.IntegerField()

    # Admins tick this once they've manually reviewed and approved the document.
    is_verified = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'document_type')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"


class VerificationQueue(models.Model):
    # When a job seeker submits their documents, a queue entry is created here
    # so admins have a clear list of who needs reviewing. The status moves
    # from pending → approved or rejected.
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # One entry per user — if they resubmit documents, we update the existing
    # entry rather than creating duplicates.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_queue')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Tracks which admin made the decision, for accountability.
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='verifications_reviewed')
    rejection_reason = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        # Oldest submissions first — fair first-come, first-served for admins.
        ordering = ['submitted_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"


class Rating(models.Model):
    # Allows employers to leave a star rating (1–5) and optional comment
    # for a job seeker after working with them. Each employer can only rate
    # a given seeker once (unique_together).
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    reviewed = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='ratings_received')
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reviewer', 'reviewed')

    def __str__(self):
        return f"{self.reviewer.username} rated {self.reviewed.user.username}: {self.score}/5"
