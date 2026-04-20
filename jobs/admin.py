from django.contrib import admin
from .models import JobCategory, Job, Application, SavedJob, JobTitleSynonym, ApplicationDocument


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'location', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'location']
    search_fields = ['title', 'employer__username']
    readonly_fields = ['views', 'applications_count', 'created_at', 'updated_at']
    actions = ['close_selected_jobs']

    def close_selected_jobs(self, request, queryset):
        queryset.update(status='closed')
    close_selected_jobs.short_description = 'Close selected jobs'

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'applicant', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['job__title', 'applicant__username']
    readonly_fields = ['applied_at', 'updated_at']

@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ['application', 'file_name', 'is_from_profile', 'uploaded_at']
    list_filter = ['is_from_profile', 'uploaded_at']
    search_fields = ['file_name']
    readonly_fields = ['uploaded_at', 'file_size_bytes']

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__username', 'job__title']

@admin.register(JobTitleSynonym)
class JobTitleSynonymAdmin(admin.ModelAdmin):
    list_display = ['primary_title', 'synonym', 'category']
    list_filter = ['category', 'created_at']
    search_fields = ['primary_title', 'synonym']