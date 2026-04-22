from django.contrib import admin
from .models import JobCategory, Job, Application, SavedJob, JobTitleSynonym, ApplicationDocument

# Registers all jobs app models with Django's admin panel. The customisations
# below control which columns appear in each list view, what you can filter
# and search by, and what bulk actions are available — keeping admin work
# as straightforward as possible.


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    # Simple list — categories are short records, just a name and icon.
    list_display = ['name', 'icon']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'location', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'location']
    search_fields = ['title', 'employer__username']

    # Views and counts are calculated fields — marking them readonly
    # prevents admins from accidentally editing them directly.
    readonly_fields = ['views', 'applications_count', 'created_at', 'updated_at']
    actions = ['close_selected_jobs']

    def close_selected_jobs(self, request, queryset):
        # Bulk action to close multiple job listings at once, useful for
        # clearing out old posts in one go.
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
    # Lets admins inspect documents that were submitted with specific
    # applications — useful if there's a dispute or review needed.
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
    # The synonym table powers intelligent job title matching in search.
    # Admins can add new synonyms here without touching the codebase.
    list_display = ['primary_title', 'synonym', 'category']
    list_filter = ['category', 'created_at']
    search_fields = ['primary_title', 'synonym']
