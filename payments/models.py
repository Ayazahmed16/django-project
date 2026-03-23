import uuid
from django.db import models
from orders.models import VendorOrder


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor_order = models.OneToOneField(
        VendorOrder, on_delete=models.CASCADE, related_name="payment"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    gateway_ref = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    paid_at = models.DateTimeField(null=True, blank=True)