# service-backend/resume/urls.py
from django.urls import path
from . import views

app_name = 'resume'

urlpatterns = [
    path('', views.ResumeListView.as_view(), name='resume_list'),
    path('create/', views.ResumeCreateView.as_view(), name='resume_create'),
    path('<int:id>/', views.ResumeDetailView.as_view(), name='resume_detail'),
    path('<int:id>/update/', views.ResumeUpdateView.as_view(), name='resume_update'),
    path('<int:id>/delete/', views.ResumeDeleteView.as_view(), name='resume_delete'),
    path('<int:resume_id>/generate-pdf/', views.GeneratePDFView.as_view(), name='resume_generate_pdf'),
    path('share/<uuid:token>/', views.ShareableResumeView.as_view(), name='resume_share'), # Public link
]
