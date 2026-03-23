from django.urls import path
from .views import ProductListCreateView, ProductDetailView

urlpatterns = [
    path("", ProductListCreateView.as_view(), name="product_list_create"),
    path("<uuid:pk>/", ProductDetailView.as_view(), name="product_detail"),
]