from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .tasks import send_order_confirmation_email, send_vendor_notification


@receiver(post_save, sender=Order)
def order_confirmed_handler(sender, instance, created, **kwargs):
    if not created and instance.status == 'confirmed':
        send_order_confirmation_email.delay(
            order_id=str(instance.id),
            user_email=instance.user.email,
            total_amount=str(instance.total_amount),
        )
        for vendor_order in instance.vendor_orders.all():
            if hasattr(vendor_order.vendor, 'email'):
                send_vendor_notification.delay(
                    vendor_order_id=str(vendor_order.id),
                    vendor_email=vendor_order.vendor.email,
                    subtotal=str(vendor_order.subtotal),
                )