# service-backend/skill/serializers.py
from rest_framework import serializers
from .models import SkillCategory, Course

class SkillCategorySerializer(serializers.ModelSerializer):
    """Serializer for SkillCategory model."""
    # Optionally include a count of courses in this category
    # course_count = serializers.SerializerMethodField()

    class Meta:
        model = SkillCategory
        fields = '__all__'
        
    # def get_course_count(self, obj):
    #     return obj.courses.count() # Or use annotations in the view for better performance

class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'category_name')

# If you need a simpler serializer for listing (e.g., in category detail)
# class CourseListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Course
#         fields = ('id', 'title', 'url', 'recommended_by_ai')
