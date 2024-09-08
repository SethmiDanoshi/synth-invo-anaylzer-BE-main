# serializers.py
from rest_framework import serializers
from .models import Template
import uuid
from datetime import datetime

class TemplateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(default=uuid.uuid4)
    supplier = serializers.UUIDField(default=uuid.uuid4)
    template_name = serializers.CharField()
    template_content = serializers.CharField()
    uploaded_at = serializers.DateTimeField(default=datetime.now)
    mapping = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField(default=datetime.now)
    mapped_status = serializers.BooleanField(default=False)
    mapped_by = serializers.UUIDField(allow_null = True, required = False)
    mapped_at = serializers.DateTimeField(default=datetime.now)

    mapping_dict = serializers.SerializerMethodField()

    class Meta:
        model = Template
        fields = (
            'id', 'supplier', 'template_name', 'template_content', 'uploaded_at', 
            'mapping', 'created_at', 'mapped_status', 'mapped_by', 'mapped_at', 'mapping_dict'
        )
        read_only_fields = ('id', 'uploaded_at', 'created_at', 'mapping_dict')

    def get_mapping_dict(self, obj):
        return obj.mapping_dict
