from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import TimeLog, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sign_in_time', 'sign_out_time', 'is_active', 'duration')
    list_filter = ('is_active', 'sign_in_time', 'user')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    ordering = ('-sign_in_time',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'employee_id', 'department', 'position')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'employee_id', 'department', 'position')
    ordering = ('user__username',)# Project Structure: