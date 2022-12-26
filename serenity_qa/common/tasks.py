from time import sleep

from celery import shared_task

from serenity_qa.common.jobs import JobTask


@shared_task(bind=True, base=JobTask, description="Progress Test Task")
def progress_task(self, n=3000):
    print("print: start")
    for i in range(n):
        self.log_progress(current=i, total=n, message=f"test task: {i}/{n}")
        sleep(1)
    self.log_progress(current=n, total=n, message=f"test task: done!")
    print("print: end")
