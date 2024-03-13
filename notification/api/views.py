
from rest_framework.response import Response
from notification.api.serializers import NotificationSerializer
from account.models import Doctor

from notification.models import Notification
from rest_framework import generics, permissions
from rest_framework import status


class DoctorNotificationMessagesAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self, custom_id):
        user = Doctor.objects.get(custom_id=custom_id)
        return Notification.objects.filter(Doctor=user, receiver_type='doctor').exclude(is_seen=True).order_by('-created')

    def get(self, request, custom_id, *args, **kwargs):
        try:
            queryset = self.get_queryset(custom_id)
            notification_count = queryset.count()
            serializer = self.get_serializer(queryset, many=True)
            response_data = {
                'notifications': serializer.data,
                'notification_count': notification_count,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class UpdateNotificationSeenStatusView(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_seen = True
        instance.save()
        return Response({'status': 'success', 'message': 'Notification seen status updated'}, status=status.HTTP_200_OK)



