# service-backend/account/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""
    # --- Updated list_display to include profile fields ---
    list_display = (
        'national_code', 'phone_number', 'email', 'first_name', 'last_name',
        'gender', 'is_staff', 'is_active', 'is_superuser'
    )
    # --- Updated list_filter to include relevant filters ---
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'gender', 'date_joined'
    )
    # --- Updated fieldsets to organize fields properly ---
    fieldsets = (
        (None, {'fields': ('national_code', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'gender', 'birth_date', # Use renamed field
                'phone_number', 'email', 'profile_picture'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    # --- add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'national_code', 'phone_number', 'email', 'password1', 'password2', 'is_superuser', 'is_staff'
            ),
        }),
    )
    # --- Updated search_fields to include new profile fields ---
    search_fields = (
        'national_code', 'first_name', 'last_name',
        'phone_number', 'email'
    )
    ordering = ('national_code',)
    filter_horizontal = ('groups', 'user_permissions',)
