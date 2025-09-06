# project_root/service-backend/assessment/views.py
from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
# Import your models and serializers
from .models import TestPackage, Assessment, UserAssessmentAttempt
from .serializers import (
    TestPackageSerializer, AssessmentSerializer,
    UserAssessmentAttemptSerializer, UserAssessmentAttemptCreateSerializer,
    UserAssessmentAttemptSubmitSerializer
)
# Import user model
from django.conf import settings
User = settings.AUTH_USER_MODEL

# --- Views for Test Packages ---

class TestPackageListView(generics.ListAPIView):
    """
    List all active test packages, filtered by the authenticated user's age.
    """
    serializer_class = TestPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'min_age', 'max_age', 'price']
    ordering = ['min_age', 'name']

    def get_queryset(self):
        user = self.request.user
        user_age = user.calculate_age() # Assuming this method exists on the User model

        if user_age is not None:
            # Filter packages based on user's age
            queryset = TestPackage.objects.filter(is_active=True, min_age__lte=user_age, max_age__gte=user_age)
        else:
            # If age is not available, maybe show all or none? Let's show none for security/safety.
            # Or, you could show packages with min_age=0 or a default range.
            # For now, let's be restrictive.
            queryset = TestPackage.objects.none() # Or TestPackage.objects.filter(is_active=True, min_age=0)

        return queryset

class TestPackageDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific test package (if user has access based on age).
    """
    serializer_class = TestPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id' # Use 'id' to look up the package

    def get_queryset(self):
        user = self.request.user
        user_age = user.calculate_age()

        if user_age is not None:
            # Allow access only if package is active and age-appropriate
            return TestPackage.objects.filter(is_active=True, min_age__lte=user_age, max_age__gte=user_age)
        else:
            return TestPackage.objects.none()

# --- Views for Assessments ---

class AssessmentListView(generics.ListAPIView):
    """
    List assessments within packages accessible to the user (based on age).
    """
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    # Allow filtering by packages (IDs) that contain the assessments the user can access
    filterset_fields = ['packages'] # Filter by package ID (M2M field on Assessment)

    def get_queryset(self):
        user = self.request.user
        user_age = user.calculate_age()

        if user_age is not None:
             # Get IDs of packages accessible to the user based on age
             accessible_package_ids = TestPackage.objects.filter(
                 is_active=True, min_age__lte=user_age, max_age__gte=user_age
             ).values_list('id', flat=True)

             # Get assessments that belong to any of these accessible packages
             # Use distinct() to avoid duplicates if an assessment is in multiple accessible packages
             return Assessment.objects.filter(
                 is_active=True, packages__in=accessible_package_ids
             ).distinct()
        else:
            return Assessment.objects.none()

class AssessmentDetailView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific assessment (if user has access to its package).
    """
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        user_age = user.calculate_age()

        if user_age is not None:
            # Get IDs of packages accessible to the user based on age
            accessible_package_ids = TestPackage.objects.filter(
                is_active=True, min_age__lte=user_age, max_age__gte=user_age
            ).values_list('id', flat=True)

            # Get assessments that belong to any of these accessible packages
            return Assessment.objects.filter(
                is_active=True, packages__in=accessible_package_ids # Updated filter using M2M
            ).distinct() # Use distinct to prevent duplicates
        else:
            return Assessment.objects.none()

# --- Views for User Assessment Attempts ---

class UserAssessmentAttemptListView(generics.ListAPIView):
    """
    List all assessment attempts for the authenticated user.
    """
    serializer_class = UserAssessmentAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['start_time', 'end_time', 'assessment__name']
    ordering = ['-start_time']
    # --- Updated filter reference to use 'assessment__packages' (the M2M field) ---
    filterset_fields = ['assessment__packages', 'assessment', 'is_completed'] # Filter by package, assessment, status

    def get_queryset(self):
        return UserAssessmentAttempt.objects.filter(user=self.request.user)

class StartAssessmentAttemptView(APIView):
    """
    Start a new attempt for an assessment.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = UserAssessmentAttemptCreateSerializer(data=request.data)
        if serializer.is_valid():
            assessment = serializer.validated_data['assessment']

            # Check if user has access to ANY package this assessment belongs to
            # based on age.
            user = request.user
            user_age = user.calculate_age()

            # Get packages this specific assessment belongs to
            # assessment_packages = assessment.packages.filter(is_active=True) # Old way
            # New way: Get the IDs of packages this assessment is in
            assessment_package_ids = assessment.packages.filter(is_active=True).values_list('id', flat=True)

            # Check if any of those package IDs are accessible to the user
            accessible_package = TestPackage.objects.filter(
                id__in=assessment_package_ids,
                is_active=True,
                min_age__lte=user_age,
                max_age__gte=user_age
            ).first() if user_age is not None and assessment_package_ids.exists() else None

            if not accessible_package:
                 return Response(
                     {"detail": "You do not have access to this assessment based on your age or package."},
                     status=status.HTTP_403_FORBIDDEN
                 )

            # Check if there's an existing incomplete attempt for this user and assessment
            # Uncomment the lines below if you want to enforce one active attempt per assessment
            # existing_attempt = UserAssessmentAttempt.objects.filter(
            #     user=user, assessment=assessment, is_completed=False
            # ).first()
            # if existing_attempt:
            #     return Response(
            #         {"detail": "You have an existing incomplete attempt for this assessment.",
            #          "attempt_id": existing_attempt.id},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )

            # Create the new attempt
            attempt = UserAssessmentAttempt.objects.create(
                user=user,
                assessment=assessment,
                start_time=timezone.now()
            )
            response_serializer = UserAssessmentAttemptSerializer(attempt)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubmitAssessmentAttemptView(generics.UpdateAPIView):
    """
    Submit results for an assessment attempt, marking it as completed.
    """
    serializer_class = UserAssessmentAttemptSubmitSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Only allow users to submit their own attempts
        return UserAssessmentAttempt.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.is_completed:
            return Response(
                {"detail": "This assessment attempt has already been submitted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Prepare response data
        response_serializer = UserAssessmentAttemptSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

# View to retrieve assessment JSON data (conceptual, might need auth checks)
# This would typically involve reading the file and returning its content
# class AssessmentJSONDataView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get(self, request, assessment_id):
#         assessment = get_object_or_404(Assessment, id=assessment_id)
#         # Add check if user has access to this assessment/package
#
#         json_file_path = assessment.get_json_file_path()
#         try:
#             with open(json_file_path, 'r', encoding='utf-8') as f:
#                 data = json.load(f)
#             return Response(data)
#         except FileNotFoundError:
#             return Response({"detail": "Assessment data not found."}, status=status.HTTP_404_NOT_FOUND)
#         except json.JSONDecodeError:
#             return Response({"detail": "Error reading assessment data."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
