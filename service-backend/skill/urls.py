# service-backend/skill/urls.py
from django.urls import path
from . import views

app_name = 'skill'

urlpatterns = [
    path('categories/', views.SkillCategoryListView.as_view(), name='category_list'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/category/<int:category_id>/', views.CourseByCategoryView.as_view(), name='course_by_category'),
    # path('courses/<int:id>/', views.CourseDetailView.as_view(), name='course_detail'), # Optional
    # path('courses/recommended/', views.UserRecommendedCoursesView.as_view(), name='user_recommended_courses'), # Optional
]
