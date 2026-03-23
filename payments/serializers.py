from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    vendor_order_id = serializers.UUIDField(source="vendor_order.id", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "vendor_order_id",
            "amount",
            "gateway_ref",
            "status",
            "paid_at",
        ]