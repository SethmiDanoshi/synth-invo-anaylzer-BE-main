from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model
from .permissions import  IsOrganization, IsSupplier, IsSystemAdmin
from .utils import generate_token, generate_refresh_token, decode_token, send_email, send_otp, verify_otp , resend_otp, generate_temporary_password
from .models import  Organization, Supplier, SystemAdmin, SupplierOrganization, OTP, SupplierRequest
from .serializers import  SupplierSerializer, SystemAdminSerializer, OrganizationSerializer, SupplierRequestSerializer, SupplierOrganizationSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
import json

User = get_user_model()

@api_view(['POST'])
def organization_signup(request):
    try:
        serializer_data = {
        "user": {
            "username": request.data.get('username'),
            "email": request.data.get('email'),
            "password": request.data.get('password')
        },
        "name": request.data.get('orgName'),
        "address": request.data.get('address'),
        "business_registration_number": request.data.get('businessRegNum'),
        "logo_url" : request.data.get('logoUrl')
    }
        serializer = OrganizationSerializer(data=serializer_data)
        if serializer.is_valid():
            
            if send_otp(request.data.get('email')):
                organization = serializer.save()
                token = generate_token(str(organization.id), 'organization', '')
                return Response({'user': serializer.data, 'token': token, 'organization_id': str(organization.id), 'organization_name':organization.name}, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(serializer.errors)
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        print(e)
        return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@api_view(['POST'])
def organization_signin(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email=email, password=password)

    if user:
        organization = Organization.objects.filter(user=user).first()
        if organization:
            access_token = generate_token(str(user.id), 'organization', str(organization.id))
            refresh_token = generate_refresh_token(access_token)

            if user.is_verified_email:
                return Response({
                    'access': access_token,
                    'refresh': refresh_token,
                    'organization_id': str(organization.id),
                }, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Not a verified e-mail', 'email': user.email}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        else:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)




@api_view(['POST'])
def add_supplier(request):
    email = request.data.get('email')
    name = request.data.get('name')
    address = request.data.get('address')
    organization_id = request.data.get('organization_id')

    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        return Response({'error': 'Organization not found'}, status=404)

    supplier = Supplier.objects.filter(user__email=email).first()

    if supplier:
        request_exists = SupplierRequest.objects.filter(email=email, organization=organization_id).exists()
        if request_exists:
            return Response({'message': 'You already requested this.'}, status=status.HTTP_409_CONFLICT)

        supplier_request = SupplierRequest.objects.create(
            organization=organization,
            name=name,
            email=email,
            address=address,
            status='pending',
        )
        return Response({'message': 'Supplier request created successfully'}, status=status.HTTP_201_CREATED)

    # If supplier does not exist, create the supplier
    temp_password = generate_temporary_password()
    subject = 'Your Temporary Credentials For SynthInvoAnalyzer'
    context = {
        'temporary_password': temp_password
    }

    serializer_data = {
        "user": {
            "username": name,
            "email": email,
            "password": temp_password,
            "is_verified_email": True
        },
        "address": address
    }

    serializer = SupplierSerializer(data=serializer_data)
    if serializer.is_valid():
        supplier = serializer.save()
        send_email(email, subject, 'employee_add_email.html', context)
        SupplierOrganization.objects.create(
            supplier=supplier,
            organization=organization
        )
        return Response({'message': 'Supplier created and email sent successfully'}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def supplier_signin(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email=email, password=password)
    

    if user:
        try:
            supplier = user.supplier
            
            access_token = generate_token(str(supplier.user_id), 'supplier', '')
            refresh_token = generate_refresh_token(access_token)
            if supplier.temporary_password:
                return Response({'message' : 'You must change your Password', 'supplier' : supplier.user_id, 'token': access_token, 'email': user.email}, status = status.HTTP_307_TEMPORARY_REDIRECT )
            return Response({
                'access': access_token, 
                'refresh': refresh_token, 
                'supplier_id': str(supplier.id)
            }, status=status.HTTP_200_OK)
        except Supplier.DoesNotExist:
            return Response({'error': 'User is not a supplier'}, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def admin_signup(request):
    
    serializer_data = {
        "user": {
            "username": request.data.get('username'),
            "email": request.data.get('email'),
            "password": request.data.get('password'),
        }
        }
    
    serializer = SystemAdminSerializer(data = serializer_data)
    if serializer.is_valid():
        admin = serializer.save()
        user = admin.user
        token = generate_token(str(admin.id), 'system_admin', '')
        return Response({'admin': serializer.data, 'token': token, "admin_id": str(admin.id)}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def admin_signin(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email=email, password=password)

    if user:
        try:
            admin = user.systemadmin
            access_token = generate_token(str(admin.id), 'system_admin', '')
            refresh_token = generate_refresh_token(access_token)
            return Response({
                'access': access_token, 
                'refresh': refresh_token, 
                'admin_id': str(admin.id)
            }, status=status.HTTP_200_OK)
        except SystemAdmin.DoesNotExist:
            return Response({'error': 'User is not a system admin'}, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



@api_view(['GET'])
def check_supplier_exists(request):
    email = request.GET.get('email')
    try:
        supplier = Supplier.objects.get(user__email=email)
        response_data = {
            'exists': True,
            'name': supplier.user.username,
            'address': supplier.address,
        }
    except Supplier.DoesNotExist:
        response_data = {
            'exists': False,
        }
    return Response(response_data, status=status.HTTP_200_OK)



@api_view(["POST"])
def verify_otp_view(request):
    user_email = request.data.get("email")
    user_otp = request.data.get("otp")
    
    if not user_email or not user_otp:
        return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=user_email)
        if user.is_verified_email:
            return Response({"error": "User's email is already verified"}, status=status.HTTP_400_BAD_REQUEST)
        
        is_verified, message = verify_otp(user_email, user_otp)
        if is_verified:
            user.is_verified_email = True
            user.save()
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)



@api_view(["POST"])
def resend_otp_view(request):
    user_email = request.data.get("email")
    
    if not user_email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=user_email)
        if user.is_verified_email:
            return Response({"error": "User's email is already verified"}, status=status.HTTP_400_BAD_REQUEST)
        
        if resend_otp(user_email):
            return Response({"message": "OTP resent successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to resend OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except User.DoesNotExist:
        return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_org_by_supplier(request):
    supplier_id = request.query_params.get('supplier_id')

    if not supplier_id:
        return Response({'error': 'Supplier ID parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        supplier_orgs = SupplierOrganization.objects.filter(supplier_id=supplier_id)
        organizations = [
            {
                'organization_id': supplier_org.organization.id,
                'organization_name': supplier_org.organization.name
            }
            for supplier_org in supplier_orgs
        ]
        return Response({'organizations': organizations}, status=status.HTTP_200_OK)

    except SupplierOrganization.DoesNotExist:
        return Response({'error': 'Supplier organizations not found'}, status=status.HTTP_404_NOT_FOUND)

    except ValueError as e:
        return Response({'error': f'Invalid supplier_id: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    

@api_view(['GET'])
def pending_requests_supplier_view(request):
    supplier_email = request.query_params.get('supplier_email')
    
    if not supplier_email:
        return Response({"error": "Supplier email is required"}, status=status.HTTP_400_BAD_REQUEST)

    supplier_requests = SupplierRequest.objects.filter(email=supplier_email)

    if supplier_requests.exists():
        serializer = SupplierRequestSerializer(supplier_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response({"message": "No requests found for this supplier"}, status=status.HTTP_404_NOT_FOUND)
 
 
    
@api_view(['GET'])
def pending_requests_organization_view(request):
    organization_id = request.query_params.get('orgId')
    
    if not organization_id:
        return Response({"error": "organization_id required"}, status=status.HTTP_400_BAD_REQUEST)
    
    supplier_requests = SupplierRequest.objects.filter(organization_id=organization_id)

    if supplier_requests.exists():
        serializer = SupplierRequestSerializer(supplier_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response({"message": "No requests found for this organization"}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
def add_supplier_to_organization(request):
    supplier_id = request.data.get('supplier_id')
    organization_id = request.data.get('organization_id')
    supplier_email = request.data.get('email')
    
    add_request = SupplierRequest.objects.filter(organization_id=organization_id, email = supplier_email)
    organization = Organization.objects.get(id = organization_id)
    supplier = Supplier.objects.get(id = supplier_id)
    if add_request.exists():
        supplierorganization = SupplierOrganization.objects.create(
            supplier = supplier,
            organization = organization
        )
        
        add_request.delete()
        return Response({"message": "supplier added succesfully"}, status=status.HTTP_201_CREATED)
    else: 
        return Response({'message':'Request not found'}, status=status.HTTP_404_NOT_FOUND)


    

@api_view(['POST'])
def forgot_password(requet):
    user_email = requet.data.get('email')
    try:
        user = User.objects.get(email=user_email)
        user.is_verified_email = False
        user.save()
        if send_otp(user_email):
            return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Failed to send OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except User.DoesNotExist:
        return Response({"message": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
def reset_password(request):
    email = request.data.get('email')
  
    new_password = request.data.get('new_password')
 
    try:
        user = User.objects.get(email=email)
        user.password = make_password(new_password)
        user.save()
        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"message": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['POST'])      
def change_password(request):
    user_id = request.data.get('user_id')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    user  = User.objects.get(id = user_id)
    supplier = Supplier.objects.get(user_id = user_id)
    if new_password and confirm_password:
        if new_password == confirm_password:
            try:
                user.password = make_password(new_password)
                supplier.temporary_password = False
                user.save()
                supplier.save()
                return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "New password and confirmation are required."}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def organization_profile(request, organization_id):
    try:
        organization = Organization.objects.get(id=organization_id)
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data)
    except Organization.DoesNotExist:
        return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)
    
    
@api_view(['GET'])
@permission_classes([IsOrganization])
def organization_protected_view(request):
    return Response({'message': 'Authenticated as organization'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsSystemAdmin])
def admin_protected_view(request):
    return Response({'message': 'Authenticated as system admin'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsSupplier])
def supplier_protected_view(request):
    return Response({'message': 'Authenticated as supplier'}, status=status.HTTP_200_OK)





