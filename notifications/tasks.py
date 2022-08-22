from celery import shared_task

@shared_task(name="send_mistbox_notifications")
def send_mistbox_notifications():
    from push_notifications.models import APNSDevice
    APNSDevice.objects.all().send_message(
        "Your mistbox is ready! See who wrote about you today 👀")