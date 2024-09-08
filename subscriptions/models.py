from django.db import models
from datetime import datetime
from decimal import Decimal
from authentication.models import Organization
from subscription_models.models import SubscriptionModel
import uuid
from django.utils import timezone

class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    subscription_model = models.ForeignKey(SubscriptionModel, on_delete=models.CASCADE)
    subscription_id = models.CharField(max_length=100, unique=True)
    plan_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    billing_interval = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    payment_method = models.CharField(max_length=50)
    trial_period_days = models.IntegerField(default=0)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    auto_renewal = models.BooleanField(default=True)
    cancellation_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_current_period_paid(self):
        now = timezone.now()
        if self.next_billing_date and self.next_billing_date > now:
            latest_payment = self.payments.filter(payment_date__gte=self.start_date, payment_date__lte=self.next_billing_date).last()
            if latest_payment and latest_payment.status == 'paid':
                if latest_payment.amount_paid >= self.amount:
                    return True
        return False

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    payment_id = models.CharField(max_length=100)
    payment_date = models.DateTimeField()
    status = models.CharField(max_length=20)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
