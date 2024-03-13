import json
from channels.generic.websocket import AsyncWebsocketConsumer

# consumers.py

class DoctorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Add the doctor to a group
        doctor_channel_name = f'doctor_{self.scope["user"].id}'
        await self.channel_layer.group_add(
            doctor_channel_name,
            self.channel_name
        )   

    async def disconnect(self, close_code):
        # Remove the doctor from the group
        doctor_channel_name = f'doctor_{self.scope["user"].id}'
        await self.channel_layer.group_discard(
            doctor_channel_name,
            self.channel_name
        )

    async def send_notification(self, event):
        message = event['message']

        # Send the notification to the WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
