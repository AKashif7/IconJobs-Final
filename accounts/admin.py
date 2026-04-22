from django.contrib import admin
from .models import UserProfile, UserDocument, VerificationQueue, Rating

# Registers the accounts app models with Django's built-in admin panel.
# Each class below customises how that model's list view looks and what
# actions are available, making it easier for the site admin to manage
# users and the verification queue without touching the database directly.


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    # Shows who rated whom, the score, and when — useful for spotting any
    # suspicious or repeated ratings.
    list_display = ['reviewer', 'reviewed', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['reviewer__username', 'reviewed__user__username']
    readonly_fields = ['created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # The verification columns (is_verified, blue_tick_awarded) are shown
    # here so admins can quickly scan who's been approved without opening
    # each record individually.
    list_display = ['user', 'role', 'is_verified', 'blue_tick_awarded', 'created_at']
    list_filter = ['role', 'is_verified', 'blue_tick_awarded', 'created_at']
    search_fields = ['user__username', 'user__email', 'legal_name']
    readonly_fields = ['created_at']


@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    # Lets admins see which documents have been uploaded and whether each
    # one has been manually verified yet.
    list_display = ['user', 'document_type', 'file_name', 'is_verified', 'uploaded_at']
    list_filter = ['document_type', 'is_verified', 'uploaded_at']
    search_fields = ['user__username', 'file_name']
    readonly_fields = ['uploaded_at', 'file_size_bytes']


@admin.register(VerificationQueue)
class VerificationQueueAdmin(admin.ModelAdmin):
    # The queue of users waiting for their documents to be reviewed.
    # The two bulk actions below let admins process multiple submissions
    # at once rather than clicking into each one individually.
    list_display = ['user', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['submitted_at']
    actions = ['approve_users', 'reject_users']

    def approve_users(self, request, queryset):
        # Loops through the selected queue entries, awards the blue tick
        # to each user's profile, and marks the entry as approved.
        for item in queryset:
            if item.status == 'pending':
                profile = item.user.profile
                profile.is_verified = True
                profile.blue_tick_awarded = True
                profile.save()
                item.status = 'approved'
                item.reviewed_by = request.user
                item.save()
        self.message_user(request, f'{queryset.count()} users approved!')
    approve_users.short_description = "Approve selected verifications"

    def reject_users(self, request, queryset):
        # Bulk rejection — sets status to rejected and records who did it.
        for item in queryset:
            if item.status == 'pending':
                item.status = 'rejected'
                item.reviewed_by = request.user
                item.save()
        self.message_user(request, f'{queryset.count()} users rejected!')
    reject_users.short_description = "Reject selected verifications"
