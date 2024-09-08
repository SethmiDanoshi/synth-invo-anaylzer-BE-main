from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from .models import Organization, Supplier, SystemAdmin
from .utils import decode_token
from subscriptions.models import Subscription

class IsOrganization(permissions.BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        if not token:
            raise PermissionDenied("Token is missing")
        user_info = decode_token(token)
        if 'user_id' not in user_info or 'role' not in user_info:
            raise PermissionDenied("Invalid token")
        user_id = user_info['user_id']
        role = user_info['role']
        if role == 'organization':
            if Organization.objects.filter(user_id=user_id).exists():
                return True
        raise PermissionDenied("You do not have permission to access this resource as an organization")

class IsSupplier(permissions.BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        if not token:
            raise PermissionDenied("Token is missing")
        user_info = decode_token(token)
        if 'user_id' not in user_info or 'role' not in user_info:
            raise PermissionDenied("Invalid token")
        user_id = user_info['user_id']
        role = user_info['role']
        if role == 'supplier':
            if Supplier.objects.filter(user_id=user_id).exists():
                return True
        raise PermissionDenied("You do not have permission to access this resource as a supplier")

class IsSystemAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        if not token:
            raise PermissionDenied("Token is missing")
        user_info = decode_token(token)
        if 'user_id' not in user_info or 'role' not in user_info:
            raise PermissionDenied("Invalid token")
        user_id = user_info['user_id']
        role = user_info['role']
        if role == 'system_admin':
            if SystemAdmin.objects.filter(id=user_id).exists():
                return True
        raise PermissionDenied("You do not have permission to access this resource as a system admin")




class IsStandard(permissions.BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        if not token:
            raise PermissionDenied("Token is missing")
        
        user_info = decode_token(token)
        if 'user_id' not in user_info or 'role' not in user_info:
            raise PermissionDenied("Invalid token")
        
        user_id = user_info['user_id']
        role = user_info['role']
        
        if role == 'organization':
            try:
                subscription = Subscription.objects.get(organization__user_id=user_id)
                if subscription.subscription_model.model_name == 'Standard':
                    return True
                else:
                    raise PermissionDenied("You do not have permission to access this resource with Standard subscription")
            except Subscription.DoesNotExist:
                raise PermissionDenied("No subscription found for this organization")
        
        raise PermissionDenied("You do not have permission to access this resource as an organization with Standard subscription")

class IsPremium(permissions.BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('Authorization')
        if not token:
            raise PermissionDenied("Token is missing")
        
        user_info = decode_token(token)
        if 'user_id' not in user_info or 'role' not in user_info:
            raise PermissionDenied("Invalid token")
        
        user_id = user_info['user_id']
        role = user_info['role']
        
        if role == 'organization':
            try:
                subscription = Subscription.objects.get(organization__user_id=user_id)
                if subscription.subscription_model.model_name == 'Premium':
                    return True
                else:
                    raise PermissionDenied("You do not have permission to access this resource with Premium subscription")
            except Subscription.DoesNotExist:
                raise PermissionDenied("No subscription found for this organization")
        
        raise PermissionDenied("You do not have permission to access this resource as an organization with Premium subscription")