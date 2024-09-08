from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Organization, Supplier, SystemAdmin, AdminSupplierMessage, AdminOrganizationMessage
from .serializers import AdminSupplierMessageSerializer, AdminOrganizationMessageSerializer, SystemAdminSerializer
import uuid

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import AdminSupplierMessage, AdminOrganizationMessage
from .serializers import AdminSupplierMessageSerializer, AdminOrganizationMessageSerializer

@api_view(['GET'])
def chat_history(request, admin_id, user_id, user_type):
    try:
        admin_uuid = str(admin_id)
        user_uuid = str(user_id)
    except ValueError:
        return Response({"error": "Invalid UUID format"}, status=status.HTTP_400_BAD_REQUEST)

    if user_type == 'supplier':
        messages = AdminSupplierMessage.objects.filter(
            Q(admin_id=admin_uuid, supplier_id=user_uuid) |
            Q(admin_id=user_uuid, supplier_id=admin_uuid)
        ).order_by('timestamp')
        serializer = AdminSupplierMessageSerializer(messages, many=True, context={'user_id': user_uuid})
    elif user_type == 'organization':
        messages = AdminOrganizationMessage.objects.filter(
            Q(admin_id=admin_uuid, organization_id=user_uuid) |
            Q(admin_id=user_uuid, organization_id=admin_uuid)
        ).order_by('timestamp')
        serializer = AdminOrganizationMessageSerializer(messages, many=True, context={'user_id': admin_uuid})
    else:
        return Response({"error": "Unknown user type"}, status=status.HTTP_400_BAD_REQUEST)
    print(serializer.data)
    return Response(serializer.data)



@api_view(['GET'])
def user_list(request, admin_id):
    try:
        admin_uuid =str(admin_id)
    except ValueError:
        return Response({"error": "Invalid UUID format"}, status=status.HTTP_400_BAD_REQUEST)

    organizations = Organization.objects.all()
    suppliers = Supplier.objects.all()
    user_data = (
        [{"id": str(org.id), "username": org.user.username, "type": "organization"} for org in organizations] +
        [{"id": str(sup.id), "username": sup.user.username, "type": "supplier"} for sup in suppliers]
    )
    
    return Response(user_data)



@api_view(['GET'])
def current_user(request, user_id):
    try:
        user_uuid = str(user_id)
    except ValueError:
        return Response({"error": "Invalid UUID format"}, status=status.HTTP_400_BAD_REQUEST)

    user_type = get_user_type_from_id(user_uuid)

    if user_type == 'organization':
        user = get_organization_details(user_uuid)
    elif user_type == 'supplier':
        user = get_supplier_details(user_uuid)
    elif user_type == 'admin':
        user = get_admin_details(user_uuid)
    else:
        return Response({"error": "User type not recognized"}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        "id": str(user.id),
        "username": user.user.username,
        "email": user.user.email,
        "type": user_type
    })

def get_user_type_from_id(user_id):
    if Organization.objects.filter(id=user_id).exists():
        return 'organization'
    elif Supplier.objects.filter(id=user_id).exists():
        return 'supplier'
    elif SystemAdmin.objects.filter(id=user_id).exists():
        return 'admin'
    return 'unknown'

def get_organization_details(user_id):
    return get_object_or_404(Organization, id=user_id)

def get_supplier_details(user_id):
    return get_object_or_404(Supplier, id=user_id)

def get_admin_details(user_id):
    return get_object_or_404(SystemAdmin, id=user_id)



@api_view(['GET'])
def admin_list(request):
    try:
        admins = SystemAdmin.objects.all()
        serializer = SystemAdminSerializer(admins, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)