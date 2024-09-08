from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import SubscriptionModel, SubscriptionModelFeatures
from authentication.models import SystemAdmin
from .serializers import SubscriptionModelSerializer, SubscriptionModelFeaturesSerializer
import stripe
import os
from dotenv import load_dotenv
from authentication.permissions import IsSystemAdmin, IsOrganization, IsSupplier

load_dotenv()

stripe.api_key = os.getenv("STRIPE_KEY")

@api_view(['POST'])
@permission_classes([IsSystemAdmin])
def create_subscription_model(request):
    admin_id = request.data.get('admin_id')
    model_name = request.data.get('model_name')
    unit_amount = request.data.get('unit_amount')
    interval = request.data.get('interval', 'month')  
    currency = request.data.get('currency', 'usd')
    user = SystemAdmin.objects.get(id = admin_id)


    if SubscriptionModel.objects.filter(model_name=model_name).exists():
        return Response(f"Product with the name '{model_name}' already exists.", status=409)  
    try:
        product = stripe.Product.create(
            name=model_name,
            default_price_data={
                "unit_amount": unit_amount * 100,  
                "currency": currency,
                "recurring": {"interval": interval},
            },
            expand=["default_price"],
        )

        
        try:
                sub_model = SubscriptionModel(
                stripe_id=product.id,
                price_id=product.default_price.id,
                model_name=model_name,
                model_price=unit_amount,
                billing_period=interval.capitalize(),  
                created_by=user,
                last_modified_by= user
                )
                sub_model.save()

                return Response("Success", status=201)
        except Exception as e:
  
            stripe.Product.modify(
                        product.id,
                        active=False  
                    )
            
            return Response("Database saving failed", status=400)

    except stripe.error.StripeError as e:
        error_message = str(e)
        return Response("Stripe Error: " + error_message, status=500)

    except Exception as e:
        error_message = "An error occurred while creating the subscription model."
        return Response("Internal Server Error: " + error_message, status=500)


@api_view(["POST"])
@permission_classes([IsSystemAdmin])
def archive_product(request):
    admin_id = request.data.get('admin_id')

    try:
        product_id = request.data['product_id']

        stripe.Product.modify(
            str(product_id),
            active=False,
        )
        SubscriptionModel.objects.filter(stripe_id=product_id).delete()

        return Response("Product archived successfully.", status=200)
    except stripe.error.StripeError as e:
        return Response(f"Error: {e}", status=500)


@api_view(["GET"])
def get_subscription_models(request):
    try:
        models = SubscriptionModel.objects.all()
        serializer = SubscriptionModelSerializer(models, many=True)
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=404)
    
    
@api_view(["PUT"])
@permission_classes([IsSystemAdmin])
def update_subscription_model(request):
    try:
        admin_id = request.data.get('admin_id')
        product_id = request.data['product_id']
        new_price = request.data.get('new_price')
        new_name = request.data.get('model_name')
        currency = request.data.get('currency', 'usd')
        interval = request.data.get('interval', 'month')

        if new_price:
            # Create a new price in Stripe
            new_price_obj = stripe.Price.create(
                product=product_id,
                unit_amount=int(new_price) * 100,  
                currency=currency,
                recurring={"interval": interval},
            )

            # Update the product with the new default price in Stripe
            stripe.Product.modify(
                product_id,
                default_price=new_price_obj.id,
            )

        if new_name:
            # Update the product name in Stripe
            stripe.Product.modify(
                product_id,
                name=new_name,
            )

        # Update the product in your database
        subscription_models = SubscriptionModel.objects.filter(stripe_id=product_id)
        for subscription_model in subscription_models:
            if new_price:
                subscription_model.price_id = new_price_obj.id
                subscription_model.model_price = new_price
            if new_name:
                subscription_model.model_name = new_name
            subscription_model.last_modified_by_id = admin_id  # Assigning admin_id directly to ForeignKey field
            subscription_model.save()

        return Response("Subscription model updated successfully", status=200)
    except stripe.error.StripeError as e:
        error_message = str(e)
        print("Stripe Error:", error_message)
        return Response("Stripe Error: " + error_message, status=500)
    except Exception as e:
        error_message = "An error occurred while updating the subscription model."
        print("Error:", error_message, e)
        return Response("Internal Server Error: " + error_message, status=500)

@api_view(['POST'])
@permission_classes([IsSystemAdmin])
def create_feature(request):
    print(request.data)
    model_id = request.data.get('model')
    feature_name = request.data.get('feature')
    
    if SubscriptionModelFeatures.objects.filter(model=model_id, feature=feature_name).exists():
        return Response({"error": "Feature already exists for this model."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = SubscriptionModelFeaturesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsSystemAdmin])
def modify_feature(request, pk):
    try:
        feature = SubscriptionModelFeatures.objects.get(pk=pk)
        admin_id = request.data.get('userId')
        user = SystemAdmin.objects.get(id = admin_id)
        feature.feature = request.data.get('feature')
        feature.modified_by = user
        feature.save()
        return Response(status=204)
    except SubscriptionModelFeatures.DoesNotExist:
        return Response(status=404)
    
@api_view(['DELETE'])
@permission_classes([IsSystemAdmin])
def remove_feature(request, pk):
    try:
        feature = SubscriptionModelFeatures.objects.get(pk=pk)
    except SubscriptionModelFeatures.DoesNotExist:
        return Response(status=404)

    feature.delete()
    return Response(status=204)

@api_view(['GET'])
def get_features(request, model_id):
    try:
        features = SubscriptionModelFeatures.objects.filter(model=model_id)
        serializer = SubscriptionModelFeaturesSerializer(features, many=True)
        return Response(serializer.data)
    except SubscriptionModelFeatures.DoesNotExist:
        return Response(status=404)

