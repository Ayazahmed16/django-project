from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id, user_email, total_amount):
    try:
        send_mail(
            subject=f'Order Confirmed - #{order_id[:8].upper()}',
            message=f'Your order {order_id} for ${total_amount} has been confirmed!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return f'Email sent to {user_email}'
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_vendor_notification(vendor_order_id, vendor_email, subtotal):
    send_mail(
        subject=f'New Order - #{vendor_order_id[:8].upper()}',
        message=f'New order {vendor_order_id} received. Subtotal: ${subtotal}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[vendor_email],
        fail_silently=True,
    )
    return f'Vendor notified: {vendor_email}'


@shared_task
def cleanup_abandoned_carts():
    from django.utils import timezone
    from datetime import timedelta
    from orders.models import Order
    cutoff = timezone.now() - timedelta(hours=24)
    abandoned = Order.objects.filter(status='active', placed_at__lt=cutoff)
    count = abandoned.count()
    abandoned.delete()
    return f'Deleted {count} abandoned carts'