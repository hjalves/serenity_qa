import datetime
import json
import time
from datetime import timezone, datetime
from urllib.parse import urljoin

from django.conf import settings
from django.core.files import File
from django.db import models
from django.urls import reverse

from .download import youtube_dl_download
from .utils import trim_audio_file, parse_jsonl_live_chat


class VideoManager(models.Manager):
    def get_by_natural_key(self, code, published):
        return self.get(code=code, published=published)


class Video(models.Model):
    code = models.CharField(max_length=12, unique=True)
    title = models.CharField(max_length=200, blank=True)
    published = models.DateField(null=True, blank=True)
    duration = models.DurationField(blank=True, null=True)

    objects = VideoManager()

    class Meta:
        verbose_name = "Q&A video"
        verbose_name_plural = "Q&A videos"
        ordering = ("-published",)

    def __str__(self):
        return self.title or self.code

    def natural_key(self):
        return self.code, self.published

    def questions(self):
        return self.question_set.order_by("-timestamp")

    def existing_media_files(self):
        if not self.code:
            return {}

        parent_dir = settings.DOWNLOAD_DIR
        media_dir = settings.DOWNLOAD_URL

        info_file = f"{self.code}.info.json"
        audio_file = f"{self.code}.opus"
        chat_file = f"{self.code}.live_chat.json"
        subs_file = f"{self.code}.en.vtt"

        media_files = [
            ("info", parent_dir / info_file, urljoin(media_dir, info_file)),
            ("audio", parent_dir / audio_file, urljoin(media_dir, audio_file)),
            ("subtitles", parent_dir / subs_file, urljoin(media_dir, subs_file)),
            ("live_chat", parent_dir / chat_file, urljoin(media_dir, chat_file)),
        ]
        return {file_type: url for file_type, path, url in media_files if path.exists()}

    def metadata(self):
        info_file = settings.DOWNLOAD_DIR / f"{self.code}.info.json"
        return json.loads(info_file.read_text())

    def live_chat(self):
        info_file = settings.DOWNLOAD_DIR / f"{self.code}.live_chat.json"
        return parse_jsonl_live_chat(info_file)

    def audio_path(self):
        if self.code:
            return settings.DOWNLOAD_DIR / f"{self.code}.opus"

    def audio_url(self):
        if self.code:
            return urljoin(settings.DOWNLOAD_URL, f"{self.code}.opus")

    def download(
        self, skip_video=False, only_audio=True, live_chat=False, subtitles=False
    ):
        directory = settings.DOWNLOAD_DIR
        directory.mkdir(parents=True, exist_ok=True)
        youtube_dl_download(
            self.url,
            download_dir=directory,
            skip_download=skip_video,
            only_audio=only_audio,
            live_chat=live_chat,
            subtitles=subtitles,
        )

    def download_audio(self):
        from .tasks import youtube_download_audio

        directory = settings.DOWNLOAD_DIR / "audio"
        directory.mkdir(parents=True, exist_ok=True)

        return youtube_download_audio.delay(url=self.url, download_dir=str(directory))

    def download_metadata(self, live_chat=False, subtitles=False):
        from .tasks import youtube_download_metadata

        directory = settings.DOWNLOAD_DIR / "metadata"
        directory.mkdir(parents=True, exist_ok=True)

        return youtube_download_metadata.delay(
            url=self.url,
            download_dir=str(directory),
            live_chat=live_chat,
            subtitles=subtitles,
        )

    def fill_metadata(self, download=True):
        try:
            metadata = self.metadata()
        except FileNotFoundError:
            if download:
                self.download(skip_video=True)
                metadata = self.metadata()
            else:
                raise
        self.title = metadata["title"]
        upload_date = metadata["upload_date"]
        self.published = datetime.datetime.strptime(upload_date, "%Y%m%d").date()
        self.duration = datetime.timedelta(seconds=metadata["duration"])
        self.save()

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
            return f"http://www.youtube.com/embed/{self.code}?enablejsapi=1"
        return ""

    def build_livechat_questions(self):
        self.livechatmessage_set.all().delete()
        livechat_questions = self.live_chat()
        for question in livechat_questions:
            LiveChatMessage.objects.create(
                video=self,
                timestamp=question["timestamp"],
                author=question["author"],
                message=question["message"],
            )


class Tag(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"
        ordering = ("name",)

    def __str__(self):
        return self.name


def question_audiofile_path(instance, filename):
    return "questions/{0}/{1}-{2}s.opus".format(
        instance.video.code,
        str(instance.timestamp).replace(":", "."),
        instance.duration_secs(),
    )


class QuestionManager(models.Manager):
    def get_by_natural_key(self, code, published, timestamp):
        return self.get(
            video__code=code, video__published=published, timestamp=timestamp
        )


class Question(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    timestamp = models.DurationField()
    duration = models.DurationField(blank=True, null=True)
    question = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    audio_file = models.FileField(upload_to=question_audiofile_path, blank=True)

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

    def natural_key(self):
        return self.video.natural_key() + (self.timestamp,)

    def timestamp_secs(self):
        return int(self.timestamp.total_seconds())

    def duration_secs(self):
        if self.duration is not None:
            return int(self.duration.total_seconds())

    def question_trunc(self):
        return self.question[:80] + "..." if len(self.question) > 80 else self.question

    def admin_url(self):
        return reverse("admin:questions_question_change", args=(self.pk,))

    def admin_delete_url(self):
        return reverse("admin:questions_question_delete", args=(self.pk,))

    def url(self):
        return self.video.build_url(self.timestamp)

    def element_id(self):
        return str(self.timestamp)

    def get_previous(self):
        return self._get_next_or_previous_by_FIELD(
            self._meta.get_field("timestamp"), is_next=False, video_id=self.video_id
        )

    def get_next(self):
        return self._get_next_or_previous_by_FIELD(
            self._meta.get_field("timestamp"), is_next=True, video_id=self.video_id
        )

    def compute_duration(self):
        try:
            next = self.get_next()
        except Question.DoesNotExist:
            return self.video.duration - self.timestamp
        else:
            return next.timestamp - self.timestamp

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


class LiveChatMessage(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    timestamp = models.DurationField()
    author = models.CharField(max_length=100)
    message = models.TextField(blank=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.author}: {self.message_trunc()}"

    def natural_key(self):
        return self.video.natural_key() + (self.author, self.timestamp)

    def message_trunc(self):
        return self.message[:80] + "..." if len(self.message) > 80 else self.message

    class Meta:
        verbose_name = "livechat message"
        verbose_name_plural = "livechat messages"
        ordering = (
            "video__published",
            "timestamp",
        )


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
        verbose_name = "YouTube post"
        verbose_name_plural = "YouTube posts"
        ordering = ("-published",)

    def __str__(self):
        return self.title

    @classmethod
    def add_from_feedparser_entry(cls, entry):
        published = updated = thumbnail_url = None
        if "published_parsed" in entry:
            naive_gmt_dt = time.mktime(entry.published_parsed)
            published = datetime.fromtimestamp(naive_gmt_dt, timezone.utc)
        if "updated_parsed" in entry:
            naive_gmt_dt = time.mktime(entry.updated_parsed)
            updated = datetime.fromtimestamp(naive_gmt_dt, timezone.utc)
        if "media_thumbnail" in entry:
            try:
                thumbnail_url = entry.media_thumbnail[0]['url']
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
        post, _ = cls.objects.update_or_create(entry_id=entry.id, defaults=defaults)
        return post
