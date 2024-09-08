from django.db import models
import uuid
from authentication.models import User, SystemAdmin, Organization, Supplier

class AdminSupplierMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(SystemAdmin, on_delete=models.CASCADE, related_name='supplier_messages')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    user_role = models.CharField(max_length=20, default='unknown')  # New field for sender's role

    def __str__(self):
        return f'{self.admin} to {self.supplier}: {self.content}'

class AdminOrganizationMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(SystemAdmin, on_delete=models.CASCADE, related_name='organization_messages')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    user_role = models.CharField(max_length=20, default='unknown')  # New field for sender's role

    def __str__(self):
        return f'{self.admin} to {self.organization}: {self.content}'
