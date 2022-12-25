import logging

import celery.states
from celery.app.task import Task
from celery.utils.log import get_task_logger, get_logger
from django.core.cache import cache
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone
from kombu.utils import uuid
from pythonjsonlogger.jsonlogger import JsonFormatter

from .models import Job

logger = get_task_logger(__name__)


def get_job_redis_connection():
    return cache._cache.get_client()


class JobLogRedisHandler(logging.Handler):
    STREAM_EXPIRE_TIME = 3600

    def __init__(
        self,
        task_request,
        redis_client=None,
        level=logging.NOTSET,
    ):
        super(JobLogRedisHandler, self).__init__(level)
        self.task_id = task_request.id
        self.task_name = task_request.get("task")
        self.redis_stream = f"job:{self.task_id}"
        self.redis_client = redis_client or get_job_redis_connection()
        self.formatter = JsonFormatter(reserved_attrs=())

    def emit(self, record):
        msg = self.format(record)
        self.redis_client.xadd(self.redis_stream, {"message": msg})
        self.redis_client.expire(self.redis_stream, self.STREAM_EXPIRE_TIME)


def setup_logger_redirection(task_request):
    redis_handler = JobLogRedisHandler(task_request)
    task = get_logger("celery.task")
    redirected = get_logger("celery.redirected")
    if not any(isinstance(h, JobLogRedisHandler) for h in task.handlers):
        task.addHandler(redis_handler)
    if not any(isinstance(h, JobLogRedisHandler) for h in redirected.handlers):
        redirected.addHandler(redis_handler)


def clean_logger_redirection():
    task = get_logger("celery.task")
    redirected = get_logger("celery.redirected")
    for h in list(task.handlers):
        if isinstance(h, JobLogRedisHandler):
            task.removeHandler(h)
    for h in list(redirected.handlers):
        if isinstance(h, JobLogRedisHandler):
            redirected.removeHandler(h)


class JobTask(Task):
    track_started = True
    description = None

    def apply_async(self, args=None, kwargs=None, task_id=None, **extra):
        task_id = task_id or uuid()
        description = self.description
        if "description" in extra:
            description = extra["description"]
        job = Job.objects.create(
            task_id=task_id,
            task_name=self.name,
            state=celery.states.PENDING,
            description=description or "",
        )
        result = super().apply_async(args, kwargs, task_id, **extra)
        result.job = job
        return result

    def __call__(self, *args, **kwargs):
        setup_logger_redirection(task_request=self.request)
        properties = self.request.get("properties") or {}
        description = properties.get("description")
        if self.request.get("task"):
            # Only when in celery worker (task execution context)
            job, _ = Job.objects.update_or_create(
                task_id=self.request.id,
                defaults={
                    "state": celery.states.STARTED,
                    "started_at": timezone.now(),
                    "task_name": self.request.task,
                    "description": description or self.description or "",
                },
            )
            self.request.job = job
        return super(JobTask, self).__call__(*args, **kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        clean_logger_redirection()

    def on_success(self, retval, task_id, args, kwargs):
        job = self.request.job
        job.state = celery.states.SUCCESS
        job.finished_at = timezone.now()
        job.save()
        job.refresh_admin_page()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        try:
            job = self.request.job
        except AttributeError:
            pass
        else:
            job.state = celery.states.FAILURE
            job.finished_at = timezone.now()
            job.save()
            job.refresh_admin_page()

    def set_description(self, description):
        job = self.request.job
        job.description = description
        job.save()

    def log_progress(
        self,
        message,
        *args,
        current=None,
        total=None,
        extra=None,
        level=logging.NOTSET,
        **kwargs,
    ):
        meta = {}
        if current is not None:
            meta["current"] = current
        if total is not None:
            meta["total"] = total
        if current is not None and total is not None:
            meta["percentage"] = round(100.0 * current / total, 1)
        extra = {**(extra or {}), **meta}
        logger.log(level, message, *args, **kwargs, extra=extra)

        meta["message"] = message
        self.update_state(state="PROGRESS", meta=meta)

    def attach_file(self, file, name=None, content_type=None, description=None):
        django_file = File(file, name)
        return self.request.job.attach(django_file, content_type, description)

    def attach_content(self, content, name, content_type=None, description=None):
        django_file = ContentFile(content, name)
        return self.request.job.attach(django_file, content_type, description)
