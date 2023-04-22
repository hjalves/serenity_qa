import json
from os.path import basename

import requests
from celery.result import AsyncResult
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from serenity_qa.common.admin_realtime import ModelAdminRealtime
from serenity_qa.common.utils import (
    format_exception,
    get_object_admin_link,
    discover_type,
)


class Job(models.Model):
    STATE_CHOICES = [
        ("PENDING", "Pending"),
        ("STARTED", "Started"),
        ("SUCCESS", "Success"),
        ("FAILURE", "Failure"),
        ("REVOKED", "Revoked"),
    ]
    READY_STATES = ("SUCCESS", "FAILURE", "REVOKED")

    task_id = models.CharField(max_length=32)
    task_name = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=500, blank=True)
    state = models.CharField(max_length=100, choices=STATE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "job"
        verbose_name_plural = "jobs"

    def __str__(self):
        return f"[{self.id}] {self.description or self.task_name}"

    @cached_property
    def async_result(self):
        return AsyncResult(self.task_id)

    def result_info(self):
        # TODO: save this info
        return self.async_result.info

    def realtime_state(self):
        state = self.state
        if state not in self.READY_STATES:
            return self.async_result.state
        return state

    def progress_percentage(self):
        state = self.realtime_state()
        if state == "SUCCESS":
            return 100
        if state == "FAILURE" or self.state == "REVOKED":
            return 0
        if state == "PROGRESS":
            return (self.result_info() or {}).get("percentage")

    def progress_message(self):
        state = self.realtime_state()
        if state == "PROGRESS":
            return (self.result_info() or {}).get("message")
        elif state in ("FAILURE", "SUCCESS"):
            result_info = self.result_info()
            if isinstance(result_info, Exception):
                return format_exception(result_info)
            return result_info

    def refresh_admin_page(self):
        ModelAdminRealtime.perform_refresh(self.__class__, self.pk)

    def admin_link(self):
        return get_object_admin_link(self)

    def attach(self, django_file, content_type=None, description=None, category=None):
        if not content_type:
            content_type = discover_type(django_file)
        description = description or ""
        category = category or JobAttachment.CATEGORY_FILE
        return JobAttachment.objects.create(
            job=self,
            file=django_file,
            type=content_type,
            description=description,
            category=category,
        )

    def elapsed(self):
        if self.started_at is None:
            return None
        if not self.finished_at and self.realtime_state() == "PENDING":
            return None
        to_time = self.finished_at or timezone.now()
        td = to_time - self.started_at
        secs = td.total_seconds()
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        return hours, mins, secs

    def elapsed_str(self):
        if elapsed := self.elapsed():
            hours, mins, secs = elapsed
            if hours > 0:
                return "%02d:%02d:%02d" % (hours, mins, secs)
            return "%02d:%02d" % (mins, secs)

    def job_log_redis_handler(self):
        from serenity_qa.common.jobs import JobLogRedisHandler

        return JobLogRedisHandler(task_id=self.task_id)

    def job_log(self):
        log = self.attachments.filter(category=JobAttachment.CATEGORY_LOG).first()
        if log:
            with log.file.open("rt") as f:
                return [json.loads(line) for line in f]
        return self.job_log_redis_handler().get_job_log()


def attachment_path(instance, filename):
    job_id = instance.job.task_id[:8]
    created = instance.created_on or timezone.now()
    date = created.strftime("%Y%m%d")
    return f"jobs/{date}/{job_id}/{filename}"


class JobAttachment(models.Model):
    CATEGORY_FILE = "file"
    CATEGORY_LOG = "log"
    CATEGORY_CHOICES = (
        (CATEGORY_FILE, "File"),
        (CATEGORY_LOG, "Log output"),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(max_length=500, upload_to=attachment_path)
    type = models.CharField(max_length=100, blank=True)
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default=CATEGORY_FILE
    )
    description = models.CharField(max_length=200, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "job attachment"
        verbose_name_plural = "job attachments"

    def __str__(self):
        if self.description:
            return self.description
        return f"Attachment: {self.name or '-'}"

    @property
    def name(self):
        if self.file:
            return basename(self.file.name)

    @property
    def size(self):
        try:
            if self.file:
                return self.file.size
        except FileNotFoundError:
            pass

    @property
    def url(self):
        if self.file:
            return self.file.url


class Notification(models.Model):
    username = models.CharField(max_length=100, blank=True)
    channel = models.CharField(max_length=50, blank=True)
    icon_emoji = models.CharField(max_length=50, blank=True)
    text = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    sent_on = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"

    def __str__(self):
        short_text = (self.text[:40] + "...") if len(self.text) >= 40 else self.text
        return f"{self.username}: {short_text}"

    def send(self):
        payload = {"text": self.text}
        if self.username:
            payload["username"] = self.username
        if self.channel:
            payload["channel"] = self.channel
        if self.icon_emoji:
            payload["icon_emoji"] = self.icon_emoji

        response = requests.post(settings.SLACK_WEBHOOK, json=payload)
        response.raise_for_status()

        self.sent_on = timezone.now()
        self.save(update_fields=["sent_on"])

    def send_async(self):
        from .tasks import send_notification

        return send_notification.delay(self.id)
