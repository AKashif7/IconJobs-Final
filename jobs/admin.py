from django.contrib import admin
from .models import Job, Application, SavedJob, JobCategory

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'location', 'duration', 'status', 'created_at']
    list_filter = ['status', 'duration']
    search_fields = ['title', 'employer__username', 'location']
    actions = ['close_selected_jobs']

    def close_selected_jobs(self, request, queryset):
        queryset.update(status='closed')
    close_selected_jobs.short_description = 'Close selected jobs'

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job', 'status', 'applied_at']
    list_filter = ['status']
    search_fields = ['applicant__username', 'job__title']

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'saved_at']
