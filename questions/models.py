import datetime
import json

from django.conf import settings
from django.db import models

from questions.download import youtube_dl_download


class Video(models.Model):
    code = models.CharField(max_length=12, unique=True)
    title = models.CharField(max_length=200, blank=True)
    url = models.URLField("URL", blank=True)
    published = models.DateField(null=True, blank=True)
    duration = models.DurationField(blank=True, null=True)

    class Meta:
        verbose_name = "Q&A video"
        verbose_name_plural = "Q&A videos"
        ordering = ("-published",)

    def __str__(self):
        return self.title or self.code

    def metadata(self):
        info_file = settings.DOWNLOAD_DIR / f"{self.code}.info.json"
        return json.loads(info_file.read_text())

    def download(self, skip_video=False):
        directory = settings.DOWNLOAD_DIR
        directory.mkdir(parents=True, exist_ok=True)
        youtube_dl_download(self.url, download_dir=directory, skip_download=skip_video)

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

    def save(self, *a, **kw):
        if not self.url:
            self.url = f"https://www.youtube.com/watch?v={self.code}"
        super().save(*a, **kw)

    def build_url(self, timestamp=None):
        return "{}&t={}s".format(self.url, int(timestamp.total_seconds()))


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


class Question(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    timestamp = models.DurationField()
    duration = models.DurationField(blank=True, null=True)
    question = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        verbose_name = "question"
        verbose_name_plural = "questions"
        ordering = (
            "video__published",
            "timestamp",
        )

    def __str__(self):
        return f"[{self.timestamp}] {self.question_trunc()}"

    def question_trunc(self):
        return self.question[:80] + "..." if len(self.question) > 80 else self.question

    def url(self):
        return self.video.build_url(self.timestamp)

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
