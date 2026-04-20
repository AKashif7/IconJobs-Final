from django.contrib import admin
from .models import UserProfile, UserDocument, VerificationQueue, Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'reviewed', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['reviewer__username', 'reviewed__user__username']
    readonly_fields = ['created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_verified', 'blue_tick_awarded', 'created_at']
    list_filter = ['role', 'is_verified', 'blue_tick_awarded', 'created_at']
    search_fields = ['user__username', 'user__email', 'legal_name']
    readonly_fields = ['created_at']

@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'file_name', 'is_verified', 'uploaded_at']
    list_filter = ['document_type', 'is_verified', 'uploaded_at']
    search_fields = ['user__username', 'file_name']
    readonly_fields = ['uploaded_at', 'file_size_bytes']

@admin.register(VerificationQueue)
class VerificationQueueAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['submitted_at']
    actions = ['approve_users', 'reject_users']
    
    def approve_users(self, request, queryset):
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
        for item in queryset:
            if item.status == 'pending':
                item.status = 'rejected'
                item.reviewed_by = request.user
                item.save()
        self.message_user(request, f'{queryset.count()} users rejected!')
    reject_users.short_description = "Reject selected verifications"
