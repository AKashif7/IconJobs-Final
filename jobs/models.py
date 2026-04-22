from django.db import models
from django.contrib.auth.models import User

# Database models for the jobs app. This is the heart of the platform —
# it defines job listings, applications, saved jobs, the synonym table that
# powers smart search, and the documents attached to each application.


class JobCategory(models.Model):
    # A simple label used to group jobs (e.g. "Hospitality", "Retail",
    # "Events"). The icon field holds a Bootstrap Icons name so each
    # category can have a visual icon on the frontend.
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=50, default='briefcase')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Job Categories'


class JobTitleSynonym(models.Model):
    # Powers the intelligent search feature. For example, if someone searches
    # "cashier" this table maps it to "till worker", "checkout assistant", etc.
    # so relevant jobs appear even if the employer used a different title.
    primary_title = models.CharField(max_length=100)
    synonym = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('primary_title', 'synonym')
        verbose_name_plural = 'Job Title Synonyms'
        ordering = ['primary_title']

    def __str__(self):
        return f"{self.primary_title} ↔ {self.synonym}"


class Job(models.Model):
    # The main job listing model. Employers create jobs; job seekers browse
    # and apply. Duration and pay_type use predefined choices to keep the
    # data consistent across the site.

    DURATION_CHOICES = [
        ('2h', '2 Hours'),
        ('4h', '4 Hours'),
        ('8h', '1 Day (8 Hours)'),
        ('2d', '2 Days'),
        ('5d', '5 Days (1 Week)'),
        ('2w', '2 Weeks'),
        ('1m', '1 Month'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('filled', 'Filled'),
    ]

    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=200)
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES)
    pay_rate = models.DecimalField(max_digits=8, decimal_places=2)
    pay_type = models.CharField(
        max_length=20,
        choices=[('hourly', 'Per Hour'), ('daily', 'Per Day'), ('fixed', 'Fixed Rate')],
        default='hourly'
    )
    spots_available = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    start_date = models.DateField()

    # Views and applications_count are incremented in the view layer each
    # time someone views or applies, so the trending algorithm has something
    # to work with.
    views = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        # Newest jobs first everywhere by default.
        ordering = ['-created_at']

    @property
    def is_trending(self):
        # A job is considered trending if it has had at least 3 applications
        # or 20 views. The homepage uses this to surface popular listings.
        return self.applications_count >= 3 or self.views >= 20

    @property
    def applicant_count(self):
        return self.applications.count()


class Application(models.Model):
    # Tracks a job seeker's application to a specific job. The status field
    # moves through the hiring pipeline: pending → shortlisted → accepted →
    # completed (or rejected/withdrawn/cancelled at any point).

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('withdrawn', 'Withdrawn'),
        ('cancelled', 'Cancelled by Employer'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # When an employer accepts someone, contact_revealed is set to True and
    # the seeker's phone/email becomes visible on their profile to that employer.
    contact_revealed = models.BooleanField(default=False)

    # If an employer cancels an accepted application, we store why —
    # this is shown to the job seeker so they're not left in the dark.
    cancellation_reason = models.CharField(max_length=100, blank=True)
    cancellation_detail = models.TextField(blank=True)

    class Meta:
        # One application per (job, applicant) pair — can't apply twice.
        unique_together = ('job', 'applicant')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} → {self.job.title} [{self.status}]"

    @property
    def conversation(self):
        # Convenience property that looks up the chat conversation linked
        # to this application, so templates can link straight to the chat.
        from chat.models import Conversation
        return Conversation.objects.filter(
            job=self.job,
            participants=self.applicant,
        ).first()


class ApplicationDocument(models.Model):
    # Files attached directly to a job application (CV, cover letter, etc.).
    # Separate from UserDocument so the seeker can upload fresh copies for
    # each application if they want, rather than always using their profile CV.
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='applications/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size_bytes = models.IntegerField()

    # Flag to distinguish between a document uploaded fresh for this
    # application vs one pulled directly from the seeker's profile.
    is_from_profile = models.BooleanField(default=False, help_text="True if using existing CV from profile")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    document_order = models.IntegerField(default=0, help_text="Order of documents in application")

    class Meta:
        ordering = ['document_order', 'uploaded_at']

    def __str__(self):
        return f"Document for {self.application.applicant.username}'s application"


class SavedJob(models.Model):
    # Simple bookmarking — a job seeker can save a listing to review later.
    # unique_together means they can only save each job once.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"
