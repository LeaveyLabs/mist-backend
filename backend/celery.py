import os, ssl

from celery import Celery
from celery.schedules import crontab

from mist_worker.tasks import tally_random_upvotes_task

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ['DJANGO_SETTINGS_MODULE'])

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from mist_worker.tasks import reset_mistbox_swipecount_task, send_mistbox_notifications_task
    sender.add_periodic_task(crontab(hour=17, minute=0), reset_mistbox_swipecount_task.s())
    sender.add_periodic_task(crontab(hour=17, minute=0), send_mistbox_notifications_task.s())
    sender.add_periodic_task(3600, tally_random_upvotes_task.s())
