from django.db import models
from account.models import Doctor, Patient
from booking.models import Transaction

# Create your models here.

class ChatMessage(models.Model):
    sender = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField(default="", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='chat_messages', null=True)
    sendername = models.TextField(max_length=100, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_send = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sender} to {self.receiver}: {self.message}'