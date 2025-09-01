# service-backend/career/urls.py
from django.urls import path
from . import views

app_name = 'career'

urlpatterns = [
    path('jobs/', views.JobOpeningListView.as_view(), name='job_list'),
    path('jobs/<int:id>/', views.JobOpeningDetailView.as_view(), name='job_detail'),
    path('resources/', views.BusinessResourceListView.as_view(), name='resource_list'),
    path('resources/<int:id>/', views.BusinessResourceDetailView.as_view(), name='resource_detail'),
    # path('ask-consultant/', views.AskBusinessConsultantView.as_view(), name='ask_consultant'), # Optional future feature
]
