from rest_framework import serializers
from account.models import Doctor
from notification.models import Notification



class DoctorNotifySerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ('custom_id', 'full_name')



class NotificationSerializer(serializers.ModelSerializer):
    from_user = DoctorNotifySerializer(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('notification_type',)

    def validate_notification_type(self, value):
        choices = dict(Notification.NOTIFICATION_TYPES)
        if value not in choices:
            raise serializers.ValidationError("Invalid notification type.")
        return value