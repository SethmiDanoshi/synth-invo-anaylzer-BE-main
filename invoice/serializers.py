from rest_framework import serializers
from .models import Invoice
from authentication.models import Supplier, Organization
from datetime import datetime
import uuid

class InvoiceSerializer(serializers.Serializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    issuer = serializers.UUIDField(default=uuid.uuid4)
    recipient = serializers.UUIDField(default=uuid.uuid4)
    source_format = serializers.CharField()  
    internal_format = serializers.CharField()  
    created_at = serializers.DateTimeField(default=datetime.now)
    archived = serializers.BooleanField(default=False)
    archived_at = serializers.DateTimeField(required=False, allow_null=True)
    archived_by = serializers.CharField(required=False, allow_null=True)

    issuer_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    supplier_logo_url = serializers.SerializerMethodField()

    def create(self, validated_data):
        return Invoice.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.source_format = validated_data.get('source_format', instance.source_format)
        instance.internal_format = validated_data.get('internal_format', instance.internal_format)
        instance.archived = validated_data.get('archived', instance.archived)
        instance.archived_at = validated_data.get('archived_at', instance.archived_at)
        instance.archived_by = validated_data.get('archived_by', instance.archived_by)
        instance.save()
        return instance

    def get_issuer_name(self, obj):
        try:
            supplier = Supplier.objects.get(id=obj.issuer)
            return supplier.user.username
        except Supplier.DoesNotExist:
            return None

    def get_supplier_logo_url(self, obj):
        try:
            supplier = Supplier.objects.get(id=obj.issuer)
            return supplier.logo_url
        except Supplier.DoesNotExist:
            return None

    def get_recipient_name(self, obj):
        try:
            organization = Organization.objects.get(id=obj.recipient)
            return organization.name
        except Organization.DoesNotExist:
            return None
