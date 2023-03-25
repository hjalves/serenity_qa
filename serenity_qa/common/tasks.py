import logging
from time import sleep

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from serenity_qa.common.gdrive import init_google_drive
from serenity_qa.common.jobs import JobTask


@shared_task(bind=True, base=JobTask, description="Progress Test Task")
def progress_task(self, n=30):
    print("print: start")
    for i in range(n):
        self.log_progress(current=i, total=n, message=f"test task: {i}/{n}", level=logging.INFO)
        sleep(1)
    self.log_progress(current=n, total=n, message=f"test task: done!", level=logging.INFO)
    print("print: end")


@shared_task()
def backup_sqlite_task(folder_id=None):
    folder_id = folder_id or settings.BACKUP_FOLDER_ID
    if not folder_id:
        raise KeyError("Need Folder ID")

    date_suffix = timezone.now().strftime("%Y%m%d-%H%M")
    metadata = {
        "parents": [{"id": folder_id}],
        "title": f"database.{date_suffix}.sqlite3",
        "description": "This is a backup of SerenityQA database in SQLite3 format.",
        "mimeType": "application/vnd.sqlite3",
    }
    database_path = settings.DATABASES['default']['NAME']
    print(f"Will backup database: {database_path}")

    drive = init_google_drive()
    file = drive.CreateFile(metadata=metadata)
    file.SetContentFile(database_path)
    file.Upload()
    print("Backup done.")
