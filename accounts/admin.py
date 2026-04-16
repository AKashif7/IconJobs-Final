from django.contrib import admin
from .models import UserProfile, Rating

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'location', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email', 'location']

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'reviewed', 'score', 'created_at']
