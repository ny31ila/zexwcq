# service-backend/account/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('national_code', 'phone_number', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'gender')
    fieldsets = (
        (None, {'fields': ('national_code', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'gender', 'birth_date_gregorian',
            'birth_date_shamsi', 'phone_number', 'email', 'profile_picture'
        )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('national_code', 'phone_number', 'password1', 'password2'),
        }),
    )
    search_fields = ('national_code', 'first_name', 'last_name', 'phone_number', 'email')
    ordering = ('national_code',)
    filter_horizontal = ('groups', 'user_permissions',)

# If you add a Role model later:
# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ('name',)