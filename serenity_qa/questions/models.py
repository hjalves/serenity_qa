import datetime
import json
import logging
import time
from collections import Counter
from datetime import timezone
from urllib.parse import urljoin

from django.conf import settings
from django.core.files import File
from django.db import models
from django.urls import reverse
from colorfield.fields import ColorField

from .livechat import parse_jsonl_live_chat
from .utils import trim_audio_file

logger = logging.getLogger(__name__)


class VideoManager(models.Manager):
    def get_by_natural_key(self, published):
        return self.get(published=published)


class Video(models.Model):
    code = models.CharField(max_length=12, unique=True)
    title = models.CharField(max_length=200, blank=True)
    published = models.DateField(null=True, blank=True)
    duration = models.DurationField(blank=True, null=True)
    finished = models.BooleanField("transcription finished", default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    objects = VideoManager()

    class Meta:
        verbose_name = "Q&A video"
        verbose_name_plural = "Q&A videos"
        ordering = ("-published",)

    def __str__(self):
        return self.title or self.code

    def save(self, *args, update_fields=None, **kwargs):
        super().save(*args, update_fields=update_fields, **kwargs)
        if not update_fields or "finished" in update_fields:
            if last := self.question_set.last():
                last.refresh_duration()

    def natural_key(self):
        return (self.published,)

    def get_absolute_url(self):
        return reverse("video", args=(self.id,))

    def question_count(self):
        if hasattr(self, "question__count"):
            return self.question__count
        return self.question_set.count()

    def questions(self):
        return self.question_set.order_by("-timestamp")

    def build_url(self, timestamp=None):
        return "{}&t={}s".format(self.url, int(timestamp.total_seconds()))

    @property
    def url(self):
        if self.code:
            return f"https://www.youtube.com/watch?v={self.code}"
        return ""

    @property
    def embed_youtube_url(self):
        if self.code:
            return f"https://www.youtube.com/embed/{self.code}?enablejsapi=1"
        return ""

    def existing_media_files(self):
        if not self.code:
            return {}

        media_files = [
            ("info", self.metadata_path(), self.metadata_url()),
            ("audio", self.audio_path(), self.audio_url()),
            ("subtitles", self.subtitles_path(), self.subtitles_url()),
            ("live_chat", self.live_chat_path(), self.live_chat_url()),
        ]
        return {file_type: url for file_type, path, url in media_files if path.exists()}

    def metadata_path(self):
        if self.code:
            return settings.DOWNLOAD_DIR / "metadata" / f"{self.code}.info.json"

    def metadata_url(self):
        if self.code:
            return urljoin(settings.DOWNLOAD_URL, f"metadata/{self.code}.info.json")

    def live_chat_path(self):
        if self.code:
            return settings.DOWNLOAD_DIR / "metadata" / f"{self.code}.live_chat.json"

    def live_chat_url(self):
        if self.code:
            return urljoin(settings.DOWNLOAD_URL, f"metadata/{self.code}.live_chat.json")

    def subtitles_path(self):
        if self.code:
            return settings.DOWNLOAD_DIR / "metadata" / f"{self.code}.en.vtt"

    def subtitles_url(self):
        if self.code:
            return urljoin(settings.DOWNLOAD_URL, f"metadata/{self.code}.en.vtt")

    def audio_path(self):
        if self.code:
            return settings.DOWNLOAD_DIR / "audio" / f"{self.code}.opus"

    def audio_url(self):
        if self.code:
            return urljoin(settings.DOWNLOAD_URL, f"audio/{self.code}.opus")

    def metadata_file_contents(self):
        if path := self.metadata_path():
            return json.loads(path.read_text())

    def live_chat_file_contents(self):
        if path := self.live_chat_path():
            return parse_jsonl_live_chat(path)

    def download_audio(self):
        from .tasks import download_audio

        directory = settings.DOWNLOAD_DIR / "audio"
        directory.mkdir(parents=True, exist_ok=True)

        return download_audio.delay(url=self.url, download_dir=str(directory))

    def download_metadata(self, live_chat=False, subtitles=False):
        from .tasks import download_metadata

        return download_metadata.apply_async(
            kwargs={
                "video_id": self.id,
                "live_chat": live_chat,
                "subtitles": subtitles,
            },
            description=download_metadata.description + f": {self.code}",
        )

    def import_metadata(self):
        metadata = self.metadata_file_contents()
        self.title = metadata["title"]
        upload_date = metadata["upload_date"]
        self.published = datetime.datetime.strptime(upload_date, "%Y%m%d").date()
        self.duration = datetime.timedelta(seconds=metadata["duration"])
        self.save()

    def import_livechat(self, delete_previous=False):
        livechat_questions = self.live_chat_file_contents()

        if delete_previous:
            self.livechatmessage_set.all().delete()

        timestamp_author_counter = Counter()
        created, updated = 0, 0
        for question in livechat_questions:
            counter_key = question["author"], question["timestamp"]
            _, was_created = LiveChatMessage.objects.update_or_create(
                video=self,
                timestamp=question["timestamp"],
                author=question["author"],
                counter=timestamp_author_counter[counter_key],
                defaults={"message": question["message"]},
            )
            timestamp_author_counter[counter_key] += 1
            if was_created:
                created += 1
            else:
                updated += 1
        return created, updated


class TagManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class Tag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    quiet = models.BooleanField(
        default=False, help_text="Put these questions in background"
    )
    color = ColorField(format="hex", blank=True, default="")
    emoji = models.CharField(max_length=4, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    objects = TagManager()

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.slug,)

    def question_count(self):
        return self.question_set.count()

    def full_color(self):
        if self.color:
            return f"{self.color}FF"

    def translucent_color(self):
        if self.color:
            return f"{self.color}80"


def question_audiofile_path(instance, filename):
    return "questions/{0}/{1}-{2}s.opus".format(
        instance.video.code,
        str(instance.timestamp).replace(":", "."),
        instance.duration_secs(),
    )


class QuestionManager(models.Manager):
    def get_by_natural_key(self, published, timestamp):
        return self.get(video__published=published, timestamp=timestamp)


class Question(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    timestamp = models.DurationField()
    duration = models.DurationField(blank=True, null=True)
    question = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    objects = QuestionManager()

    class Meta:
        verbose_name = "question"
        verbose_name_plural = "questions"
        ordering = (
            "video__published",
            "timestamp",
        )
        unique_together = ("video", "timestamp")

    def __str__(self):
        return f"[{self.timestamp}] {self.question_trunc()}"

    def save(self, *args, update_fields=None, **kwargs):
        super().save(*args, update_fields=update_fields, **kwargs)
        if not update_fields or "timestamp" in update_fields:
            self.refresh_duration()
            self.refresh_previous_duration()

    def refresh_duration(self):
        self.duration = self.compute_duration()
        self.save(update_fields=["duration"])

    def refresh_previous_duration(self):
        try:
            previous = self.get_previous()
        except Question.DoesNotExist:
            pass
        else:
            previous.refresh_duration()

    def compute_duration(self):
        try:
            next = self.get_next()
        except Question.DoesNotExist:
            if self.video.finished:
                return self.video.duration - self.timestamp
        else:
            return next.timestamp - self.timestamp

    def natural_key(self):
        return self.video.natural_key() + (self.timestamp,)

    def timestamp_secs(self):
        return int(self.timestamp.total_seconds())

    def duration_secs(self):
        if self.duration is not None:
            return int(self.duration.total_seconds())

    def question_trunc(self):
        return self.question[:80] + "..." if len(self.question) > 80 else self.question

    def get_absolute_url(self):
        return self.video.get_absolute_url() + f"#{self.element_id()}"

    def admin_url(self):
        return reverse("admin:questions_question_change", args=(self.pk,))

    def admin_delete_url(self):
        return reverse("admin:questions_question_delete", args=(self.pk,))

    def url(self):
        return self.video.build_url(self.timestamp)

    def element_id(self):
        return str(self.timestamp)

    def element_id_alt(self):
        return f"{self.video.published}-{self.timestamp}"

    def get_previous(self):
        return self._get_next_or_previous_by_FIELD(
            self._meta.get_field("timestamp"), is_next=False, video_id=self.video_id
        )

    def get_next(self):
        return self._get_next_or_previous_by_FIELD(
            self._meta.get_field("timestamp"), is_next=True, video_id=self.video_id
        )

    def generate_audio(self, delete_previous=True):
        input = self.video.audio_path()
        if not (duration := self.duration_secs()):
            raise Exception("Missing duration")
        path = trim_audio_file(input, self.timestamp_secs(), duration)
        if delete_previous and self.audio_file:
            self.audio_file.delete(save=True)
        with path.open(mode="rb") as f:
            self.audio_file = File(f, name=path.name)
            self.save()

    def quiet(self):
        return self.tags.filter(quiet=True).exists()


class QuestionAudio(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to=question_audiofile_path, blank=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "question audio"
        verbose_name_plural = "question audio"

    def __str__(self):
        return f"{self.audio_file}"


class LiveChatMessage(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    timestamp = models.DurationField()
    author = models.CharField(max_length=100)
    counter = models.IntegerField(blank=True, default=0)
    message = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.author}: {self.message_trunc()}"

    def natural_key(self):
        return self.video.natural_key() + (self.author, self.timestamp)

    def message_trunc(self):
        return self.message[:80] + "..." if len(self.message) > 80 else self.message

    class Meta:
        verbose_name = "livechat message"
        verbose_name_plural = "livechat messages"
        ordering = ("video__published", "timestamp", "counter", "id")


class YoutubePost(models.Model):
    entry_id = models.CharField("entry ID", max_length=100, unique=True)
    yt_videoid = models.CharField("YouTube video ID", max_length=50)
    yt_channelid = models.CharField("YouTube channel ID", max_length=50)
    link = models.URLField(blank=True)
    title = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True)
    author = models.CharField(max_length=100, blank=True)
    thumbnail_url = models.URLField("thumbnail URL", blank=True)
    published = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "YouTube RSS post"
        verbose_name_plural = "YouTube RSS posts"
        ordering = ("-published",)

    def __str__(self):
        return self.title

    @classmethod
    def update_or_create_from_feedparser_entry(cls, entry):
        published = updated = thumbnail_url = None
        if "published_parsed" in entry:
            naive_gmt_dt = time.mktime(entry.published_parsed)
            published = datetime.datetime.fromtimestamp(naive_gmt_dt, timezone.utc)
        if "updated_parsed" in entry:
            naive_gmt_dt = time.mktime(entry.updated_parsed)
            updated = datetime.datetime.fromtimestamp(naive_gmt_dt, timezone.utc)
        if "media_thumbnail" in entry:
            try:
                thumbnail_url = entry.media_thumbnail[0]["url"]
            except (KeyError, IndexError, TypeError):
                pass

        defaults = {
            "yt_videoid": entry.yt_videoid,
            "yt_channelid": entry.yt_channelid,
            "link": entry.link,
            "title": entry.title,
            "author": entry.author,
            "published": published,
            "updated": updated,
            "summary": entry.summary,
            "thumbnail_url": thumbnail_url or "",
        }
        return cls.objects.update_or_create(entry_id=entry.id, defaults=defaults)

    def get_or_create_video(self):
        video, created = Video.objects.get_or_create(
            code=self.yt_videoid,
            defaults={"title": self.title, "published": self.published.date()},
        )
        if not created:
            logger.info("YouTube Post already exist as a Q&A video, ID=%s", video.id)
        return video, created

    def is_qa_video(self):
        title = self.title.lower()
        return "office" in title and "hours" in title


class ProgressReport(models.Model):
    indicators = models.JSONField()
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "progress report"
        verbose_name_plural = "progress reports"
        ordering = ("-created_on",)
        get_latest_by = "created_on"

    def __str__(self):
        return f"{self.created_on}"
