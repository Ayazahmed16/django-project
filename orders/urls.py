from django.urls import path
from .views import (
    CartView,
    AddToCartView,
    RemoveFromCartView,
    CheckoutView,
    OrderListView,
    OrderDetailView,
)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/", AddToCartView.as_view(), name="cart-add"),
    path("cart/remove/<uuid:item_id>/", RemoveFromCartView.as_view(), name="cart-remove"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("", OrderListView.as_view(), name="order-list"),
    path("<uuid:pk>/", OrderDetailView.as_view(), name="order-detail"),
]