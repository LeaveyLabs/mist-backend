import os

from celery import Celery
from celery.schedules import crontab
from decouple import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", config('DJANGO_SETTINGS_MODULE'))
app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Executes every day at 5:00PM PST
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        send_mistbox_notifications.s(),
    )

@app.task
def send_mistbox_notifications():
    from push_notifications.models import APNSDevice
    APNSDevice.objects.all().send_message(
        "Your mistbox is ready! See who wrote about you today 👀")
