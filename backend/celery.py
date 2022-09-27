import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ['DJANGO_SETTINGS_MODULE'])

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from mist_worker.tasks import reset_mistbox_opens_task, reset_prompts_task, send_daily_prompts_notification_task
    sender.add_periodic_task(crontab(hour=17, minute=0), reset_mistbox_opens_task.s())
    sender.add_periodic_task(crontab(hour=18, minute=15), send_daily_prompts_notification_task.s())
    # sender.add_periodic_task(10.0, send_daily_prompts_notification_task.s())
    sender.add_periodic_task(15.0, reset_prompts_task.s())
    # sender.add_periodic_task(crontab(day_of_week=[1, 3, 5], hour=17, minute=0), schedule_make_your_day_mist_notifications_task.s())