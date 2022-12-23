from tempfile import TemporaryFile

import feedparser
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core import serializers
from django.utils import timezone

from serenity_qa.apps.common.jobs import JobTask
from serenity_qa.apps.questions.download import youtube_dl_download
from serenity_qa.apps.questions.dumpdata import (
    ProgressWrapper,
    get_objects_from_querysets,
)
from serenity_qa.apps.questions.models import Video, YoutubePost
from serenity_qa.apps.questions.utils import serializer_format_to_mimetype

logger = get_task_logger(__name__)


@shared_task(bind=True, base=JobTask, description="Download metadata")
def youtube_download_metadata(
    self, url, download_dir=None, live_chat=True, subtitles=True
):
    self.description = f"{self.description}: {url}"
    return youtube_dl_download(
        url,
        download_dir,
        info=True,
        skip_download=True,
        logger=logger,
        live_chat=live_chat,
        subtitles=subtitles,
    )


@shared_task(bind=True, base=JobTask, description="Download audio")
def youtube_download_audio(self, url, download_dir=None):
    def progress_hook(info):
        status = info["status"]
        message = f"Status: {status}"
        self.log_progress(
            current=info.get("downloaded_bytes"),
            total=info.get("total_bytes"),
            message=message,
        )

    self.description = f"{self.description}: {url}"
    return youtube_dl_download(
        url,
        download_dir,
        info=False,
        skip_download=False,
        progress_hooks=[progress_hook],
        only_audio=True,
        logger=logger,
    )


@shared_task(bind=True, base=JobTask, description="Video dump data")
def video_dump_data(self, video_id, models, format, **extra):
    def get_objects(count_only=False):
        queryset = Video.objects.get_queryset().filter(id=video_id)
        obj = queryset.get()
        querysets = []
        if "video" in models:
            querysets.append(queryset)
        if "question" in models:
            querysets.append(obj.question_set.all())
        if "livechat" in models:
            querysets.append(obj.livechatmessage_set.all())
        return get_objects_from_querysets(*querysets, count_only=count_only)

    with TemporaryFile(mode="w+t") as stream:
        result = serializers.serialize(
            format,
            get_objects(),
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            stream=stream,
            progress_output=ProgressWrapper(self),
            object_count=sum(get_objects(count_only=True)),
            **extra,
        )
        obj = Video.objects.get(id=video_id)
        now = timezone.now().strftime("%Y%m%d-%H%M%S")
        self.attach_file(
            stream,
            name=f"{'-'.join(models)}-{obj.code}-{now}.{format}",
            description=f"{format.upper()} exported file ({', '.join(models)})",
            content_type=serializer_format_to_mimetype(format),
        )
    return result


@shared_task(bind=True, base=JobTask, description="Update YouTube feed")
def update_feed(self):
    parsed = feedparser.parse(settings.YOUTUBE_RSS)
    new_entries = 0
    for entry in parsed.entries:
        post, created = YoutubePost.update_or_create_from_feedparser_entry(entry)
        logger.debug(
            "%s: %s - %s (published %s)",
            "created" if created else "updated",
            entry.id,
            entry.title,
            entry.published,
        )
        if created:
            new_entries += 1
            video, video_created = post.get_or_create_video()
            if video_created:
                logger.info("Q&A video created with code=%s", video.code)
    result = "{} new entries".format(new_entries if new_entries > 0 else "no")
    logger.info(result)
    self.description = f"{self.description}: {result}"
    return result
