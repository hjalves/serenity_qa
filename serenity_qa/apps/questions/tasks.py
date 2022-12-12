from celery import shared_task
from serenity_qa import celery_app


@shared_task
def debug_task():
    print("Debug: This task works!")
