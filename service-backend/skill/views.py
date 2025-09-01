# service-backend/skill/views.py
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
# Import your models and serializers
from .models import SkillCategory, Course
from .serializers import SkillCategorySerializer, CourseSerializer

class SkillCategoryListView(generics.ListAPIView):
    """
    List all skill categories.
    """
    queryset = SkillCategory.objects.all()
    serializer_class = SkillCategorySerializer
    permission_classes = [permissions.IsAuthenticated] # Or AllowAny if public
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']

class CourseListView(generics.ListAPIView):
    """
    List all courses, filterable by category and searchable.
    Can be extended to filter by AI recommendation status.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated] # Or AllowAny if public
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['category', 'recommended_by_ai'] # Allow filtering by category ID and AI recommendation
    ordering_fields = ['title', 'created_at']
    ordering = ['-created_at']

class CourseByCategoryView(generics.ListAPIView):
    """
    List courses belonging to a specific category.
    """
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated] # Or AllowAny if public
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return Course.objects.filter(category_id=category_id)

# If you want a detail view for a specific course
# class CourseDetailView(generics.RetrieveAPIView):
#     queryset = Course.objects.all()
#     serializer_class = CourseSerializer
#     permission_classes = [permissions.IsAuthenticated] # Or AllowAny if public
#     lookup_field = 'id'

# If you want to list AI-recommended courses for the user
# This would require linking courses to user recommendations (e.g., through ai_integration app)
# class UserRecommendedCoursesView(generics.ListAPIView):
#     serializer_class = CourseSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get_queryset(self):
#         user = self.request.user
#         # Get course IDs recommended for this user by the AI
#         # This requires a link, perhaps through ai_integration.models.AIRecommendation
#         # Example logic (needs adaptation based on actual model relationships):
#         # recommended_course_ids = AIRecommendation.objects.filter(
#         #     user=user,
#         #     recommendation_type__in=['academic', 'career', 'artistic'] # Or specific types
#         # ).values_list('deepseek_output_json__recommended_courses__id', flat=True) # This is complex JSON lookup
#         # Or, if Course has a direct link to AIRecommendation:
#         # return Course.objects.filter(ai_recommendations__user=user, ai_recommendations__is_active=True).distinct()
#
#         # Placeholder - return all AI recommended courses for now
#         return Course.objects.filter(recommended_by_ai=True)
