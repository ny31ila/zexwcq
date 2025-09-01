# service-backend/counseling/urls.py
from django.urls import path
from . import views

app_name = 'counseling'

urlpatterns = [
    path('consultants/', views.ConsultantListView.as_view(), name='consultant_list'),
    path('consultants/<int:id>/', views.ConsultantDetailView.as_view(), name='consultant_detail'),
    path('consultants/<int:consultant_id>/schedules/', views.ConsultantScheduleListView.as_view(), name='consultant_schedule_list'),
    path('appointments/my/', views.UserAppointmentListView.as_view(), name='user_appointment_list'),
    path('appointments/consultant/', views.ConsultantAppointmentListView.as_view(), name='consultant_appointment_list'), # For consultants
    path('appointments/book/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('appointments/<int:appointment_id>/cancel/', views.CancelAppointmentView.as_view(), name='cancel_appointment'),
    # path('appointments/<int:appointment_id>/confirm/', views.ConfirmAppointmentView.as_view(), name='confirm_appointment'), # Optional
]
