from time import sleep

from celery import shared_task

from serenity_qa.apps.common.jobs import JobTask


@shared_task(bind=True, base=JobTask, description="Progress Test Task")
def progress_task(self, n=3000):
    print("DEBUG: start")
    for i in range(n):
        self.set_progress(i, total=n, message=f"progress test task: {i}/{n}")
        sleep(1)
    self.set_progress(n, total=n, message=f"progress test task: done!")
    print("DEBUG: end")
