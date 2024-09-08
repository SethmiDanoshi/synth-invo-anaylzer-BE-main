import jwt
import datetime
import os
import random, string
from dotenv import load_dotenv
from rest_framework.exceptions import PermissionDenied
import json
from .models import OTP
import pyotp
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from subscriptions.models import Subscription
from .models import Organization



load_dotenv()


def generate_token(user, role, organization_id=None):
    SECRET_KEY = "synthInvoAnalyzer"
    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  
    created_time = datetime.datetime.utcnow()
    random_value = random.randint(1, 1000000)  

    if not isinstance(user, str):
        user = json.dumps(user)

    model_name = 'none'
    subscription_status = 'inactive'
    if role == 'organization' and organization_id:
        organization = Organization.objects.filter(id=organization_id).first()
        if organization:
            subscription = Subscription.objects.filter(organization=organization).first()
            if subscription:
                model_name = subscription.subscription_model.model_name
                subscription_status = 'active' if subscription.is_current_period_paid() else 'inactive'

    payload = {
        'rand': random_value,
        'user_id': user,
        'role': role,
        'organization_id': organization_id,
        'model_name': model_name,
        'subscription_status': subscription_status,
        'exp': expiry_time,
        'iat': created_time
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return f"Bearer {token}"



def decode_token(token):
    SECRET_KEY = os.getenv('SECRET_KEY')

    try:
        token = token.replace("Bearer ", "")  
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return decoded_payload
    except jwt.ExpiredSignatureError:
        raise PermissionDenied("Token has expired")
    except jwt.InvalidTokenError:
        raise PermissionDenied("Invalid token")


def generate_refresh_token(access_token):
    SECRET_KEY = os.getenv('SECRET_KEY')
    try:
        access_payload = jwt.decode(access_token.replace("Bearer ", ""), SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise PermissionDenied("Access token has expired")
    except jwt.InvalidTokenError:
        raise PermissionDenied("Invalid access token")
    
    
    user = access_payload.get('user_id')
    role = access_payload.get('role')
    organization_id = access_payload.get('organization_id')
    

    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(hours=6)  
    created_time = datetime.datetime.utcnow()
    random_value = random.randint(1, 1000000)  
    payload = {'rand': random_value, 'user_id': user, 'role': role, 'organization_id': organization_id, 'exp': expiry_time, 'iat': created_time}
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return f"Bearer {token.encode('utf-8')}"




def send_email(clientMail, subject, template_name, context):
    try:
        with get_connection(
                host=settings.EMAIL_HOST, 
                port=settings.EMAIL_PORT,  
                username=settings.EMAIL_HOST_USER, 
                password=settings.EMAIL_HOST_PASSWORD, 
                use_tls=settings.EMAIL_USE_TLS
        ) as connection:
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [clientMail]
            html_message = render_to_string(template_name, context)
            
            email = EmailMessage(subject, html_message, email_from, recipient_list, connection=connection)
            email.content_subtype = 'html'  
            email.send()
            return True
    except Exception as e:
        print(e)
        return False

def send_otp(user_email):
    otp = pyotp.TOTP(pyotp.random_base32(), interval=60).now()  
    try:
        OTP.objects.create(user=user_email, otp=otp)
        subject = "Your Verification Code for SynthInvoAnalyzer"
        context = {
            'otp': otp,
        }
        
        send_status = send_email(user_email, subject, 'otp_email.html', context)
        if send_status:
            return True
    except Exception as e:
        print(f"Failed to send OTP to {user_email}: {e}")
        return False


def resend_otp(user_email):
    try:
        temp_user = OTP.objects.get(user=user_email)
        temp_user.delete()
    except OTP.DoesNotExist:
        pass
    return send_otp(user_email)



def verify_otp(user_email, user_otp):
    try:
        temp_user = OTP.objects.get(user=user_email)
        if not temp_user.is_valid():
            return False, "OTP has expired"
        if temp_user.otp == user_otp:
            temp_user.verified = True
            temp_user.delete()
            return True, "Verified"
        else:
            return False, "Wrong OTP"
    except OTP.DoesNotExist:
        return False, "No OTP found for this email"
    except Exception as e:
        print(e)
        return False, "Verification failed"



def generate_temporary_password(length=12):
    characters = string.ascii_letters + string.digits 
    password = ''.join(random.choice(characters) for i in range(length))
    
    print(password)
    return password