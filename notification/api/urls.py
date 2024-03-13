from django.urls import path
from .views import DoctorNotificationMessagesAPIView,UpdateNotificationSeenStatusView

urlpatterns = [
    path('doctor-side/doctor-notification/<str:custom_id>/', DoctorNotificationMessagesAPIView.as_view(), name='doc-notification-messages'),
    path('update-notification/<int:pk>/', UpdateNotificationSeenStatusView.as_view(), name='update-notification'),
    
]