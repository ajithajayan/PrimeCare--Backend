from django.urls import path
from .views import TransactionChatMessagesAPIView

urlpatterns = [
    path('chat-messages/transaction/<str:transaction_id>/', TransactionChatMessagesAPIView.as_view(), name='transaction-chat-messages'),
    
]