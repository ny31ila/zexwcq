# service-backend/skill/admin.py
from django.contrib import admin
from .models import SkillCategory, Course

@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    ordering = ['name']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'recommended_by_ai', 'created_at')
    list_filter = ('category', 'recommended_by_ai', 'created_at')
    search_fields = ('title', 'description', 'url')
    ordering = ['-created_at']
    # raw_id_fields = ('category',) # Useful if you have many categories
