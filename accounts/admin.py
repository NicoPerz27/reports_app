
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom user admin to manage the custom User model.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'congregation', 'is_staff')
    list_filter = ('role', 'congregation', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    fieldsets = UserAdmin.fieldsets + (
        ('S-21-S Custom Fields', {'fields': ('role', 'congregation')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('S-21-S Custom Fields', {'fields': ('role', 'congregation')}),
    )
