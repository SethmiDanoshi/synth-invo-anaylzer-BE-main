from rest_framework import serializers
from .models import SubscriptionModelFeatures
from rest_framework import serializers
from .models import SubscriptionModel, SubscriptionModelFeatures


class SubscriptionModelFeaturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionModelFeatures
        fields = ['id', 'feature', 'model', 'created_at', 'created_by', 'modified_at', 'modified_by']
        read_only_fields = ['created_at', 'modified_at', 'created_by', 'modified_by']

class SubscriptionModelSerializer(serializers.ModelSerializer):
    features = SubscriptionModelFeaturesSerializer(many=True, read_only=True)

    class Meta:
        model = SubscriptionModel
        fields = ['model_id', 'stripe_id', 'price_id', 'model_name', 'model_price', 'billing_period', 'features', 'created_by', 'last_modified_by']
        read_only_fields = ['created_at', 'last_modified_at', 'created_by', 'last_modified_by']
