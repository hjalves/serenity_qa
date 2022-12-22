import logging

from celery import shared_task
from celery.utils.log import get_task_logger

from serenity_qa.apps.common.jobs import JobTask
from serenity_qa.apps.questions.download import youtube_dl_download

logger = get_task_logger(__name__)


@shared_task(bind=True, base=JobTask, description="Youtube metadata download")
def youtube_download_metadata(
    self, url, download_dir=None, live_chat=True, subtitles=True
):
    self.description = f"Youtube metadata download: {url}"
    return youtube_dl_download(
        url,
        download_dir,
        info=True,
        skip_download=True,
        logger=logger,
        live_chat=live_chat,
        subtitles=subtitles,
    )


@shared_task(bind=True, base=JobTask, description="Youtube audio download")
def youtube_download_audio(self, url, download_dir=None):
    def progress_hook(info):
        status = info["status"]
        message = f"Status: {status}"
        self.log_progress(
            current=info.get("downloaded_bytes"),
            total=info.get("total_bytes"),
            message=message,
        )

    return youtube_dl_download(
        url,
        download_dir,
        info=False,
        skip_download=False,
        progress_hooks=[progress_hook],
        only_audio=True,
        logger=logger,
    )
