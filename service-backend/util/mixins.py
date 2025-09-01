# service-backend/util/mixins.py
"""
Reusable mixins for Django REST Framework views/serializers.
"""

# Example: A mixin to add owner filtering to ListAPIView
# Ensures users can only see objects they own (based on a foreign key to User).
from rest_framework import generics

class OwnerFilteredMixin:
    """
    Mixin to filter queryset by the requesting user (owner).
    Assumes the model has a ForeignKey to the User model named 'user'.
    Add this mixin to views like ListAPIView or DestroyAPIView.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter the queryset to only include objects owned by the current user
        return queryset.filter(user=self.request.user)

# Example: A mixin for views that need to prefetch related fields for performance
# class PrefetchRelatedMixin:
#     """
#     Mixin to add prefetch_related to the queryset for performance optimization.
#     Define `prefetch_related_fields` in the view.
#     """
#     prefetch_related_fields = []
#
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         if self.prefetch_related_fields:
#             queryset = queryset.prefetch_related(*self.prefetch_related_fields)
#         return queryset

# Example: A mixin for views that need to select related fields for performance
# class SelectRelatedMixin:
#     """
#     Mixin to add select_related to the queryset for performance optimization.
#     Define `select_related_fields` in the view.
#     """
#     select_related_fields = []
#
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         if self.select_related_fields:
#             queryset = queryset.select_related(*self.select_related_fields)
#         return queryset
