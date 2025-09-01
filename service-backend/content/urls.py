# service-backend/content/urls.py
from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('news/', views.NewsArticleListView.as_view(), name='news_list'),
    path('news/<int:id>/', views.NewsArticleDetailView.as_view(), name='news_detail'),
    # path('pages/<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'), # For dynamic pages
    # path('contact-us/', views.ContactUsView.as_view(), name='contact_us'), # For contact form
]
