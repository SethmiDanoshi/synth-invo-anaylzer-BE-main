import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Organization, SystemAdmin, AdminOrganizationMessage
from .serializers import AdminOrganizationMessageSerializer
from .models import Supplier, SystemAdmin, AdminSupplierMessage
from .serializers import AdminSupplierMessageSerializer

class AdminOrganizationChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.admin_id = self.scope['url_route']['kwargs']['admin_id']
        self.organization_id = self.scope['url_route']['kwargs']['organization_id']
        self.room_group_name = f"chat_admin_{self.admin_id}_organization_{self.organization_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        if 'content' in text_data_json and 'sender_id' in text_data_json:
            content = text_data_json["content"]
            sender_id = text_data_json["sender_id"]
            sender_role = 'admin' if sender_id == self.admin_id else 'organization'

            message = await self.save_message(content, sender_id, sender_role)

            serializer = AdminOrganizationMessageSerializer(message)
            await self.channel_layer.group_send(
                self.room_group_name, {
                    "type": "chat.message",
                    "message": {
                        **serializer.data,
                        "admin": str(serializer.data["admin"]),
                        "organization": str(serializer.data["organization"]),
                    }
                }
            )
        else:
            print(f"Invalid data received: {text_data_json}")  

    async def chat_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def save_message(self, content, sender_id, sender_role):
        admin = SystemAdmin.objects.get(id=self.admin_id)
        organization = Organization.objects.get(id=self.organization_id)

        return AdminOrganizationMessage.objects.create(
            admin=admin,
            organization=organization,
            content=content,
            user_role=sender_role  
        )



class AdminSupplierChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.admin_id = self.scope['url_route']['kwargs']['admin_id']
        self.supplier_id = self.scope['url_route']['kwargs']['supplier_id']
        self.room_group_name = f"chat_admin_{self.admin_id}_supplier_{self.supplier_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(f"Received data: {text_data_json}")  # Debugging line

        if 'content' in text_data_json and 'sender_id' in text_data_json:
            content = text_data_json["content"]
            sender_id = text_data_json["sender_id"]
            sender_role = 'admin' if sender_id == self.admin_id else 'supplier'

            message = await self.save_message(content, sender_id, sender_role)

            serializer = AdminSupplierMessageSerializer(message)
            await self.channel_layer.group_send(
                self.room_group_name, {
                    "type": "chat.message",
                    "message": serializer.data
                }
            )
        else:
            print(f"Invalid data received: {text_data_json}")  # Debugging line

    async def chat_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def save_message(self, content, sender_id, sender_role):
        admin = SystemAdmin.objects.get(id=self.admin_id)
        supplier = Supplier.objects.get(id=self.supplier_id)

        return AdminSupplierMessage.objects.create(
            admin=admin,
            supplier=supplier,
            content=content,
            user_role=sender_role  # Save the sender's role
        )
