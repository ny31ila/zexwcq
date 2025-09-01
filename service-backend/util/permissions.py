# service-backend/util/permissions.py
"""
Custom permission classes for the project.
"""
from rest_framework import permissions

class IsConsultant(permissions.BasePermission):
    """
    Custom permission to only allow consultants to access the view.
    The user must have a related Consultant profile.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False
        # Check if the user has a consultant profile
        return hasattr(request.user, 'consultant_profile')

    def has_object_permission(self, request, view, obj):
        # For object-level permissions, delegate to has_permission
        # Or add specific logic if needed (e.g., checking if the object belongs to the consultant)
        return self.has_permission(request, view)

# If needed, a permission to check for specific roles (requires Role model)
# This would depend on how RBAC is implemented (e.g., groups, custom model)
# class HasRole(permissions.BasePermission):
#     """
#     Custom permission to check if a user has a specific role.
#     Requires a Role model or group-based system.
#     Usage: permission_classes = [HasRole('ContentManager')]
#     """
#     def __init__(self, role_name):
#         self.role_name = role_name
#
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
#         # Example using a custom Role model (assuming User has a roles ManyToManyField)
#         # return request.user.roles.filter(name=self.role_name).exists()
#         # Example using Django Groups
#         return request.user.groups.filter(name=self.role_name).exists()
