from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Vendor


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("email", "password", "password2", "role")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if attrs.get("role") == User.Role.ADMIN:
            raise serializers.ValidationError({"role": "Cannot register as admin."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role", "created_at")
        read_only_fields = ("id", "created_at")


class VendorSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = ("id", "owner", "store_name", "bank_account", "is_verified")
        read_only_fields = ("id", "owner", "is_verified")


class VendorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ("store_name", "bank_account")

    def create(self, validated_data):
        user = self.context["request"].user
        if hasattr(user, "vendor_profile"):
            raise serializers.ValidationError("Vendor profile already exists.")
        return Vendor.objects.create(owner=user, **validated_data)