import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "serenity_qa.settings")

app = Celery("serenity_qa")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


