import datetime
import json
from urllib.parse import urljoin

from django.conf import settings
from django.core.files import File
from django.db import models
from django.urls import reverse

from questions.download import youtube_dl_download
from questions.sound import trim_audio_file


class Video(models.Model):
    code = models.CharField(max_length=12, unique=True)
    title = models.CharField(max_length=200, blank=True)
    published = models.DateField(null=True, blank=True)
    duration = models.DurationField(blank=True, null=True)

    class Meta:
        verbose_name = "Q&A video"
        verbose_name_plural = "Q&A videos"
        ordering = ("-published",)

    def __str__(self):
        return self.title or self.code

    def questions(self):
        return self.question_set.order_by("-timestamp")

    def metadata(self):
        info_file = settings.DOWNLOAD_DIR / f"{self.code}.info.json"
        return json.loads(info_file.read_text())

    def live_chat(self):
        info_file = settings.DOWNLOAD_DIR / f"{self.code}.live_chat.json"
        return json.loads(info_file.read_text())

    def existing_media_files(self):
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
        return f"https://www.youtube.com/watch?v={self.code}"

    @property
    def embed_url(self):
        return f"http://www.youtube.com/embed/{self.code}?enablejsapi=1"


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

    def timestamp_secs(self):
        return int(self.timestamp.total_seconds())

    def duration_secs(self):
        if self.duration is not None:
            return int(self.duration.total_seconds())

    def question_trunc(self):
        return self.question[:80] + "..." if len(self.question) > 80 else self.question

    def admin_url(self):
        return reverse("admin:questions_question_change", args=(self.pk,))

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
