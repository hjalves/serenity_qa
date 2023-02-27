import tarfile
from functools import partial
from pathlib import Path
from statistics import StatisticsError
from tempfile import TemporaryFile, NamedTemporaryFile

import feedparser
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core import serializers
from django.utils import timezone

from serenity_qa.common.jobs import JobTask
from serenity_qa.questions import progress
from serenity_qa.questions.download import youtube_dl_download
from serenity_qa.questions.dumpdata import (
    ProgressWrapper,
    get_objects_from_querysets,
)
from serenity_qa.questions.models import Video, YoutubePost, ProgressReport, Tag
from serenity_qa.questions.utils import serializer_format_to_mimetype

logger = get_task_logger(__name__)


@shared_task(bind=True, base=JobTask, description="Download metadata")
def download_metadata(self, video_id, live_chat=True, subtitles=True):
    video = Video.objects.get(id=video_id)

    download_dir = video.metadata_path().parent
    logger.info(f"Will download into: {download_dir}")
    download_dir.mkdir(parents=True, exist_ok=True)

    youtube_dl_download(
        video.url,
        download_dir,
        info=True,
        skip_download=True,
        logger=logger,
        live_chat=live_chat,
        subtitles=subtitles,
    )

    imported = []

    if video.metadata_path().exists():
        video.import_metadata()
        imported.append(message := f"metadata for '{video}'")
        logger.info(f"Imported {message}")
        self.set_description(f"{self.description} [{video}]")

    if video.live_chat_path().exists():
        created, updated = video.import_livechat()
        message = f"livechat messages (created={created}, updated={updated})"
        imported.append(message)
        logger.info(f"Imported {message}")

    if not imported:
        return "Nothing to import"
    else:
        return "Imported " + ", ".join(imported)


@shared_task(bind=True, base=JobTask, description="Download audio")
def download_audio(self, url, download_dir=None):
    def progress_hook(info):
        status = info["status"]
        message = f"Status: {status}"
        self.log_progress(
            current=info.get("downloaded_bytes"),
            total=info.get("total_bytes"),
            message=message,
        )

    self.set_description(f"{self.description}: {url}")
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
            progress_output=ProgressWrapper(self.log_progress),
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


@shared_task()
def update_feed():
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
            if post.is_qa_video():
                video, video_created = post.get_or_create_video()
                if video_created:
                    logger.info("Q&A video created with code=%s", video.code)
    result = "{} new entries".format(new_entries if new_entries > 0 else "no")
    logger.info(result)
    return result


@shared_task()
def generate_progress_report():
    logger.info("Generating progress report...")
    try:
        questions_total_expected, questions_interval = progress.estimate_questions()
    except StatisticsError:
        questions_total_expected, questions_interval = 0, 0

    indicators = {
        "videos_total": progress.videos_total(),
        "videos_worked": progress.videos_worked(),
        "videos_done": progress.videos_done(),
        "questions_added": (questions_added := progress.questions_added()),
        "questions_tagged": progress.questions_tagged(),
        "minutes_total": (minutes_total := progress.minutes_total()),
        "minutes_added": (minutes_added := progress.minutes_added()),
        "minutes_tagged": (minutes_tagged := progress.minutes_tagged()),
        "percentage_added": round(minutes_added / minutes_total * 100, 1),
        "percentage_tagged": round(minutes_tagged / minutes_total * 100, 1),
        "questions_remaining": questions_total_expected - questions_added,
        "questions_interval": questions_interval,
    }

    try:
        previous_indicators = ProgressReport.objects.latest().indicators
    except ProgressReport.DoesNotExist:
        previous_indicators = {}

    if previous_indicators != indicators:
        logger.info("Will create a new progress report...")
        ProgressReport.objects.create(indicators=indicators)
    else:
        logger.info("The previous one is the same. Will not do anything.")


@shared_task()
def database_export(tar_path="database.tar.gz", data_format="json", extra=None):
    serializer_extra = {}
    if data_format == "json":
        serializer_extra = {"indent": 2}
    serializer_extra.update(extra or {})

    tar_path = Path(tar_path)
    valid_suffixes = [".tar"], [".tar", ".gz"], [".tar", ".bz2"], [".tar", ".xz"]
    assert tar_path.suffixes in valid_suffixes
    tar_mode = {
        ".tar": "w",
        ".gz": "w:gz",
        ".bz2": "w:bz2",
        ".xz": "w:xz",
    }[tar_path.suffix]

    assert data_format in ("json", "jsonl", "xml", "yaml")
    file_mode = "w+t"
    if data_format == "xml":
        file_mode = "w+b"

    def serialize_and_add_to_tar(tar_file, get_objects, file_name):
        logger.info(f"Exporting {file_name}...")
        with NamedTemporaryFile(mode=file_mode) as stream:
            serializers.serialize(
                data_format,
                get_objects(),
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
                stream=stream,
                object_count=sum(get_objects(count_only=True)),
                **serializer_extra,
            )
            stream.flush()
            tar_file.add(stream.name, file_name)

    def get_video_objects(video_id, count_only=False):
        queryset = Video.objects.all().filter(id=video_id)
        obj = queryset.get()
        return get_objects_from_querysets(
            queryset, obj.question_set.all(), count_only=count_only
        )

    def get_tag_objects(count_only=False):
        return get_objects_from_querysets(Tag.objects.all(), count_only=count_only)

    with tarfile.open(tar_path, tar_mode) as tar:
        for obj_id, published in Video.objects.values_list("id", "published"):
            name = f"video-{published}.{data_format}"
            serialize_and_add_to_tar(tar, partial(get_video_objects, obj_id), name)
        serialize_and_add_to_tar(tar, get_tag_objects, f"tags.{data_format}")

    logger.info(f"Database exported to tar file: {tar_path}")
