from django.contrib import admin
from .models import Profile, ProfileImage

class ProfileImageInline(admin.TabularInline):
    model = ProfileImage
    extra = 0

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'city', 'is_diaspora', 'is_active')
    list_filter = ('gender', 'is_diaspora', 'is_active')
    search_fields = ('user__email', 'city', 'bio')
    inlines = [ProfileImageInline]