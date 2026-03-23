from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from collections import defaultdict
import uuid

from .models import Cart, CartItem, Order, VendorOrder, VendorOrderItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    OrderSerializer,
)
from products.models import Product
from payments.models import Payment


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(
            user=request.user, status="active"
        )
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(
            Product, id=serializer.validated_data["product_id"], is_active=True
        )
        quantity = serializer.validated_data["quantity"]

        if product.stock < quantity:
            return Response(
                {"error": f"Only {product.stock} units available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart, _ = Cart.objects.get_or_create(
            user=request.user, status="active"
        )
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart = get_object_or_404(Cart, user=request.user, status="active")
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        return Response(CartSerializer(cart).data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        cart = get_object_or_404(
            Cart, user=request.user, status="active"
        )
        items = list(
            cart.items.select_related("product").select_for_update()
        )

        if not items:
            return Response(
                {"error": "Your cart is empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # validate stock for ALL items first
        for item in items:
            if item.product.stock < item.quantity:
                return Response(
                    {"error": f"'{item.product.name}' only has {item.product.stock} units in stock"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # calculate total
        total = sum(item.product.price * item.quantity for item in items)

        # create the main order
        order = Order.objects.create(
            user=request.user,
            cart=cart,
            total_amount=total,
            status=Order.Status.CONFIRMED,
        )

        # split items by vendor
        vendor_map = defaultdict(list)
        for item in items:
            vendor_map[item.product.vendor_id].append(item)

        # create vendor orders + decrement stock
        for vendor_id, vendor_items in vendor_map.items():
            subtotal = sum(i.product.price * i.quantity for i in vendor_items)

            vendor_order = VendorOrder.objects.create(
                order=order,
                vendor_id=vendor_id,
                subtotal=subtotal,
                status=VendorOrder.Status.PENDING,
            )

            for item in vendor_items:
                VendorOrderItem.objects.create(
                    vendor_order=vendor_order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.price,
                )
                # decrement stock
                item.product.stock -= item.quantity
                item.product.save()

            # simulate payment
            payment_success = self._simulate_payment()
            Payment.objects.create(
                vendor_order=vendor_order,
                amount=subtotal,
                gateway_ref=str(uuid.uuid4()),
                status="success" if payment_success else "failed",
                paid_at=None if not payment_success else __import__("django.utils.timezone", fromlist=["now"]).now(),
            )
            if payment_success:
                vendor_order.status = VendorOrder.Status.PAID
                vendor_order.save()

        # mark cart as checked out
        cart.status = "checked_out"
        cart.save()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )

    def _simulate_payment(self):
        import random
        return random.random() < 0.9


class OrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related(
                "vendor_orders__items__product",
                "vendor_orders__payment",
            )
            .order_by("-placed_at")
        )


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "vendor_orders__items__product",
            "vendor_orders__payment",
        )