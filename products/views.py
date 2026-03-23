from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from .models import Product
from .serializers import ProductSerializer


class IsVendor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "vendor"


class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/products/ — list all active products (public)
    POST /api/products/ — vendor creates a product (vendor only)
    """
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [IsVendor()]

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related("vendor")
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def get_serializer_context(self):
        return {"request": self.request}


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/products/<id>/ — product detail (public)
    PUT    /api/products/<id>/ — vendor updates their product
    DELETE /api/products/<id>/ — vendor deletes their product
    """
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [IsVendor()]

    def get_queryset(self):
        return Product.objects.all().select_related("vendor")

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_update(self, serializer):
        product = self.get_object()
        if product.vendor != self.request.user.vendor_profile:
            raise PermissionDenied("You can only edit your own products.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.vendor != self.request.user.vendor_profile:
            raise PermissionDenied("You can only delete your own products.")
        instance.delete()