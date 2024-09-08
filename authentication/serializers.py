from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Organization, Supplier, SystemAdmin, SupplierOrganization, SupplierRequest

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
    

class OrganizationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Organization
        fields = ['id', 'name', 'address', 'logo_url','business_registration_number', 'user']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            organization = Organization.objects.create(user=user, **validated_data)
            return organization
        else:
            raise serializers.ValidationError(user_serializer.errors)




class SupplierSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Supplier
        fields = ['id', 'user', 'address']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            supplier = Supplier.objects.create(user=user, **validated_data)
            return supplier
        else:
            raise serializers.ValidationError(user_serializer.errors)


class SystemAdminSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = SystemAdmin
        fields = ['id', 'user']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            system_admin = SystemAdmin.objects.create(user=user, **validated_data)
            return system_admin
        else:
            raise serializers.ValidationError(user_serializer.errors)


class SupplierRequestSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = SupplierRequest
        fields = ['id', 'email', 'name', 'address', 'status', 'created_at', 'updated_at', 'organization_id','organization_name']
        
        
class SupplierOrganizationSerializer(serializers.ModelSerializer):
    supplier_id = serializers.ReadOnlyField(source='supplier.id')
    supplier_name = serializers.ReadOnlyField(source='supplier.name')
    organization_id = serializers.ReadOnlyField(source='organization.id')
    organization_name = serializers.ReadOnlyField(source='organization.name')

    class Meta:
        model = SupplierOrganization
        fields = ['id', 'supplier_id', 'supplier_name', 'organization_id', 'organization_name']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation