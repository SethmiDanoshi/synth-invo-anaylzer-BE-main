from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
import stripe
import os
from dotenv import load_dotenv
from datetime import datetime
from .models import Subscription, Payment, Organization
from .serializers import SubscriptionSerializer
from subscription_models.models import SubscriptionModel
from subscription_models.serializers import SubscriptionModelSerializer
from django.utils.timezone import make_aware
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

load_dotenv()

stripe.api_key = os.getenv("STRIPE_KEY")


@api_view(['POST'])
def create_subscription(request):
    try:
        price_id = request.data['priceId']
        payment_method_id = request.data['paymentMethodId']
        email = request.data['email']
        organization_id = request.data.get('organizationId')
        
        customer = stripe.Customer.create(
            email=email,
            payment_method=payment_method_id,
            invoice_settings={'default_payment_method': payment_method_id},
            metadata={'organization_id': str(organization_id)}
        )
        
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            metadata={'organization_id': str(organization_id)},
            expand=['latest_invoice.payment_intent']
        )
        
        return JsonResponse({'status': 'success', 'subscriptionId': subscription.id}, status=200)
    
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@api_view(['POST'])
def stripe_webhook(request):
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_KEY")
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        print("ValueError:", e)
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError as e:
        print("SignatureVerificationError:", e)
        return HttpResponse("Invalid signature", status=400)

    event_type = event['type']
    
    try:
        if event_type == 'customer.subscription.created':
            handle_subscription_created(event)
        elif event_type == 'invoice.payment_succeeded':
            handle_payment_succeeded(event)
        elif event_type == 'invoice.payment_failed':
            handle_payment_failed(event)
    except Exception as e:
        print(f"Error handling event {event_type}: {e}")
        return HttpResponse(f"Error handling event {event_type}", status=500)

    return HttpResponse(status=200)

def handle_subscription_created(event_json):
    try:
        subscription_data = event_json['data']['object']
        subscription_id = subscription_data['id']
        organization_id = subscription_data['metadata'].get('organization_id')
        plan_id = subscription_data['plan']['id']
        status = subscription_data['status']
        stripe_id = subscription_data['plan']['product']

        start_date = make_aware(datetime.fromtimestamp(subscription_data['start_date']))
        next_billing_date = make_aware(datetime.fromtimestamp(subscription_data['current_period_end']))
        
        if not organization_id:
            raise ValueError("Organization ID not found in metadata")

        organization = Organization.objects.get(id=organization_id)
        subscription_model = SubscriptionModel.objects.get(stripe_id=stripe_id)
        
        subscription_obj = Subscription.objects.create(
            subscription_id=subscription_id,
            organization=organization,
            plan_id=plan_id,
            status=status,
            start_date=start_date,
            next_billing_date=next_billing_date,
            billing_interval=subscription_data['plan']['interval'],
            amount=subscription_data['plan']['amount'] / 100, 
            currency=subscription_data['plan']['currency'].upper(),
            payment_method='card',
            subscription_model=subscription_model,
            trial_period_days=subscription_data.get('trial_period_days', 0),
        )
        
        subscription_obj.save()
        print(f"Subscription created: {subscription_obj}")
    
    except Exception as e:
        print(f"Error saving subscription: {e}")
        raise


def handle_payment_succeeded(event_json):
    try:
        payment_data = event_json['data']['object']
        subscription_id = payment_data['subscription']
        
        subscription_obj = Subscription.objects.get(subscription_id=subscription_id)
        payment_date = make_aware(datetime.fromtimestamp(payment_data['created']))

        if 'total' in payment_data:
            amount_paid = payment_data['total'] 
        elif 'amount_due' in payment_data:
            amount_paid = payment_data['amount_due'] 
        else:
            raise KeyError("Could not determine amount_paid from event data")

        payment_obj = Payment.objects.create(
            subscription=subscription_obj,
            payment_id=payment_data['id'],
            payment_date=payment_date,
            status=payment_data['status'],
            amount_paid=amount_paid,
            invoice_id=payment_data.get('invoice', "N/A"),
        )
        print(f"Payment succeeded: {payment_obj}")
    
    except Subscription.DoesNotExist:
        print(f"Subscription with id {subscription_id} does not exist")
    except KeyError as e:
        print(f"Error accessing payment data: {e}")
        raise
    except Exception as e:
        print(f"Error saving payment: {e}")
        raise

def handle_payment_failed(event_json):
    try:
        payment_data = event_json['data']['object']
        subscription_id = payment_data['subscription']
        
        subscription_obj = Subscription.objects.get(subscription_id=subscription_id)
        payment_date = make_aware(datetime.fromtimestamp(payment_data['created']))

        amount_paid = payment_data.get('amount_paid', 0) / 100.0  

        payment_obj = Payment.objects.create(
            subscription=subscription_obj,
            payment_id=payment_data['id'],
            payment_date=payment_date,
            status=payment_data['status'],
            amount_paid=amount_paid,
            invoice_id=payment_data.get('invoice', "N/A"),
        )
        print(f"Payment failed: {payment_obj}")
    
    except Subscription.DoesNotExist:
        print(f"Subscription with id {subscription_id} does not exist")
    except Exception as e:
        print(f"Error saving payment failed record: {e}")
        raise


@api_view(['GET'])
def get_current_subscription(request, user_id):
    try:
        subscription = Subscription.objects.get(organization=user_id)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=200)
    except Subscription.DoesNotExist:
        return Response({"error": "Subscription not found"}, status=404)


@api_view(['GET'])
def get_available_plans(request):
    plans = SubscriptionModel.objects.all()
    serializer = SubscriptionModelSerializer(plans, many=True)
    return Response(serializer.data, status=200)


@api_view(['PUT'])
def change_plan(request):
    user_id = request.data.get('userId')
    new_price_id = request.data.get('priceId')

    try:
      
        subscription = Subscription.objects.get(organization__id=user_id)
        
     
        stripe_subscription = stripe.Subscription.retrieve(subscription.subscription_id)
        
       
        subscription_item_id = stripe_subscription['items']['data'][0]['id']
        
        
        updated_subscription = stripe.Subscription.modify(
            subscription.subscription_id,
            items=[{
                'id': subscription_item_id,
                'price': new_price_id,
            }]
        )
        

        new_price = stripe.Price.retrieve(new_price_id)
        new_amount = new_price.unit_amount / 100  
        new_product_id = new_price.product  
        
      
        subscription_model = SubscriptionModel.objects.get(stripe_id=new_product_id)

   
        subscription.plan_id = new_price_id
        subscription.amount = new_amount
        subscription.subscription_model = subscription_model
        subscription.save()

        return Response({"status": "success", "message": "Subscription updated successfully"}, status=200)
    
    except Subscription.DoesNotExist:
        return Response({"error": "Subscription not found"}, status=404)
    
    except SubscriptionModel.DoesNotExist:
        return Response({"error": "Subscription model not found"}, status=404)
    
    except stripe.error.InvalidRequestError as e:
        print(f"InvalidRequestError: {str(e)}")
        return Response({"error": str(e)}, status=400)

    except Exception as e:
        print(f"Error: {str(e)}")
        return Response({"error": str(e)}, status=500)



from django.db.models.functions import TruncMonth
from django.utils import timezone

@api_view(['GET'])
def monthly_subscriptions(request):
    monthly_data = Subscription.objects.annotate(
        month=TruncMonth('created_at', tzinfo=timezone.utc)
    ).values('month').annotate(count=Count('id')).order_by('month')
    data = [{'month': item['month'].strftime('%Y-%m'), 'count': item['count']} for item in monthly_data]
    return Response(data)


@api_view(['GET'])
def subscription_model_users(request):
    model_data = SubscriptionModel.objects.annotate(user_count=Count('subscription')).values('model_name', 'user_count')
    data = list(model_data)
    return Response(data)



@api_view(['GET'])
def monthly_revenue(request):
    revenue_data = Payment.objects.filter(status='paid').annotate(
        month=TruncMonth('payment_date', tzinfo=timezone.utc)
    ).values('month').annotate(revenue=Sum('amount_paid')).order_by('month')
    
    data = [
        {
            'month': item['month'].strftime('%Y-%m'),
            'revenue': float(item['revenue']) if item['revenue'] is not None else 0
        } 
        for item in revenue_data
    ]
    return Response(data)


