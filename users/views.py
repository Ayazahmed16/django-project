from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, Vendor
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    VendorSerializer,
    VendorCreateSerializer,
)


class RegisterView(generics.CreateAPIView):
    """POST /auth/register/ — register a new buyer or vendor user"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    """POST /auth/login/ — returns access + refresh JWT tokens"""
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """GET /auth/me/ — returns current authenticated user profile"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class VendorProfileView(APIView):
    """
    GET  /auth/vendor/profile/ — get vendor profile
    POST /auth/vendor/profile/ — create vendor profile (vendor role only)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            return Response(
                {"detail": "Vendor profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = VendorSerializer(vendor)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != "vendor":
            return Response(
                {"detail": "Only users with vendor role can create a vendor profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = VendorCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        vendor = serializer.save()
        return Response(VendorSerializer(vendor).data, status=status.HTTP_201_CREATED)