from celery.result import AsyncResult
from django.db import models
from django.utils.functional import cached_property

from serenity_qa.apps.common.admin_realtime import ModelAdminRealtime


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

    def refresh_admin_page(self):
        ModelAdminRealtime.perform_refresh(self.__class__, self.pk)
