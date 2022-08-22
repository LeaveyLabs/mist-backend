from celery import shared_task
from push_notifications.models import APNSDevice

@shared_task()
def send_daily_mistbox_notifications():
    APNSDevice.objects.all().send_message(
        "Your mistbox is ready! See who wrote about you today 👀")