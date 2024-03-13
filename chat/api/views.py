from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chat.models import Transaction
from .serializers import ChatMessageSerializer

class TransactionChatMessagesAPIView(APIView):
    def get(self, request, transaction_id, *args, **kwargs):
        try:
            transaction = Transaction.objects.get(pk=transaction_id)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        chat_messages = transaction.chat_messages.all()
        serializer = ChatMessageSerializer(chat_messages, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
