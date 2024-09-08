from rest_framework import serializers
from .models import AdminSupplierMessage, AdminOrganizationMessage
from authentication.serializers import SystemAdminSerializer

class AdminSupplierMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminSupplierMessage
        fields = ['id', 'admin', 'supplier', 'content', 'timestamp', 'is_read', 'user_role']
        read_only_fields = ['id', 'user_role']

class AdminOrganizationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminOrganizationMessage
        fields = ['id', 'admin', 'organization', 'content', 'timestamp', 'is_read', 'user_role']
        read_only_fields = ['id', 'user_role']
