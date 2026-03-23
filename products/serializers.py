from rest_framework import serializers
from .models import Product
from users.models import Vendor


class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.store_name", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "vendor",
            "vendor_name",
            "name",
            "price",
            "stock",
            "is_active",
        )
        read_only_fields = ("id", "vendor")

    def create(self, validated_data):
        request = self.context["request"]
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            raise serializers.ValidationError("You must create a vendor profile first.")
        return Product.objects.create(vendor=vendor, **validated_data)