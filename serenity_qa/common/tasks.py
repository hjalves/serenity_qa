import logging
import sqlite3
from shutil import make_archive
from time import sleep

from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.utils import timezone

from serenity_qa.common.gdrive import init_google_drive
from serenity_qa.common.jobs import JobTask
from serenity_qa.common.models import Notification


@shared_task
def clear_sessions():
    return call_command("clearsessions")


@shared_task(bind=True, base=JobTask, description="Progress Test Task")
def progress_task(self, n=30):
    print("print: start")
    for i in range(n):
        self.log_progress(
            current=i, total=n, message=f"test task: {i}/{n}", level=logging.INFO
        )
        sleep(1)
    self.log_progress(current=n, total=n, message=f"test task: done!", level=logging.INFO)
    print("print: end")


@shared_task()
def backup_sqlite_task(folder_id=None):
    folder_id = folder_id or settings.BACKUP_FOLDER_ID
    if not folder_id:
        raise KeyError("Need Folder ID")

    date_suffix = timezone.now().strftime("%Y%m%d-%H%M")
    sqlite3_filename = f"database.{date_suffix}.sqlite3"
    zip_filename = f"serenity-qa.{date_suffix}.zip"
    zip_path = settings.BACKUP_LOCAL_FOLDER / zip_filename
    metadata = {
        "parents": [{"id": folder_id}],
        "title": zip_filename,
        "description": "This is a backup of SerenityOS Q&A database in SQLite3 format.",
        "mimeType": "application/zip",
    }
    destination_dir = settings.BACKUP_LOCAL_FOLDER / date_suffix
    destination_dir.mkdir(parents=True, exist_ok=True)

    print(f"Will backup database to: {sqlite3_filename}")
    target_connection = sqlite3.connect(destination_dir / sqlite3_filename)
    try:
        with target_connection:
            with connection.cursor() as cursor:
                cursor.connection.backup(target_connection)
    finally:
        target_connection.close()

    print("Making ZIP archive...")
    make_archive(zip_path.with_suffix(""), "zip", destination_dir)

    print("Uploading to Google Drive...")
    drive = init_google_drive()
    file = drive.CreateFile(metadata=metadata)
    file.SetContentFile(zip_path)
    file.Upload()

    print("Backup done.")


@shared_task()
def send_notification(notification_id):
    notification = Notification.objects.get(id=notification_id)
    notification.send()
