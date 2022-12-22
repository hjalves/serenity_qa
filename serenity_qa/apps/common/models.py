from os.path import basename

from celery.result import AsyncResult
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from serenity_qa.apps.common.admin_realtime import ModelAdminRealtime
from serenity_qa.apps.common.utils import format_exception, get_object_admin_link, \
    discover_type


class Job(models.Model):
    READY_STATES = {
        "SUCCESS": "Success",
        "FAILURE": "Failure",
        "REVOKED": "Revoked",
    }

    task_id = models.CharField(max_length=255, unique=True)
    task_name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    state = models.CharField(max_length=100)
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

    def attach(self, django_file, content_type=None, description=None):
        if not content_type:
            content_type = discover_type(django_file)
        description = description or ""
        return JobAttachment.objects.create(
            job=self, file=django_file, type=content_type, description=description
        )


def attachment_path(instance, filename):
    job_id = instance.job.task_id[:8]
    created = instance.created_on or timezone.now()
    date = created.strftime("%Y%m%d")
    return f"jobs/{date}/{job_id}/{filename}"


class JobAttachment(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(max_length=500, upload_to=attachment_path)
    type = models.CharField(max_length=100, blank=True)
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
