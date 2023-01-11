import json
import logging
from tempfile import TemporaryFile

import celery.states
from celery.app.task import Task
from celery.utils.log import get_task_logger, get_logger
from django.core.cache import cache
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone
from kombu.utils import uuid
from pythonjsonlogger.jsonlogger import JsonFormatter

from .models import Job, JobAttachment

logger = get_task_logger(__name__)


def get_job_redis_connection():
    return cache._cache.get_client()


class JobLogRedisHandler(logging.Handler):
    STREAM_EXPIRE_TIME = 3600

    @classmethod
    def setup_logger_redirection(cls, task_request):
        redis_handler = cls(task_request.id)
        redis_handler.install_in(get_logger("celery.task"))
        redis_handler.install_in(get_logger("celery.redirected"))
        return redis_handler

    @classmethod
    def uninstall_cls_from(cls, target_logger):
        for h in list(target_logger.handlers):
            if isinstance(h, cls):
                target_logger.removeHandler(h)

    @classmethod
    def clean_logger_redirection(cls):
        cls.uninstall_cls_from(get_logger("celery.task"))
        cls.uninstall_cls_from(get_logger("celery.redirected"))

    def __init__(
        self,
        task_id,
        redis_client=None,
        level=logging.NOTSET,
    ):
        super(JobLogRedisHandler, self).__init__(level)
        # self.task_id = task_request.id
        self.task_id = task_id
        # self.task_name = task_request.get("task")
        self.stream_name = f"job:{self.task_id}"
        self.redis_client = redis_client or get_job_redis_connection()
        self.formatter = JsonFormatter(reserved_attrs=())
        self.installed_in = []

    def emit(self, record):
        msg = self.format(record)
        self.redis_client.xadd(self.stream_name, {"message": msg})
        self.redis_client.expire(self.stream_name, self.STREAM_EXPIRE_TIME)

    def delete_stream(self):
        self.redis_client.delete(self.stream_name)

    def install_in(self, target_logger):
        if not any(isinstance(h, self.__class__) for h in target_logger.handlers):
            target_logger.addHandler(self)
            self.installed_in.append(target_logger)

    def uninstall(self):
        for target_logger in self.installed_in:
            target_logger.removeHandler(self)
        self.installed_in = []

    def get_job_log(self):
        entries = self.redis_client.xrange(f"job:{self.task_id}")
        messages = []
        for timestamp, content in entries:
            messages.append(json.loads(content[b"message"]))
        return messages

    def save_to_file(self, stream, iter_size=100):
        start = "-"
        client = self.redis_client
        while entries := client.xrange(self.stream_name, min=start, count=iter_size):
            timestamp = None
            for timestamp, content in entries:
                stream.write(content[b"message"].decode())
                stream.write("\n")
            start = f"({timestamp.decode()}" if timestamp else "-"


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
        self.log_handler = JobLogRedisHandler.setup_logger_redirection(self.request)
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
        self.log_handler.uninstall()
        with TemporaryFile("w+t") as temp_file:
            self.log_handler.save_to_file(temp_file)
            temp_file.seek(0)
            self.attach_file(
                temp_file,
                name=f"joblog-{self.request.job.id}.jsonl",
                content_type="application/jsonlines",
                description="Job log output",
                category=JobAttachment.CATEGORY_LOG,
            )
        self.log_handler.delete_stream()

    def on_success(self, retval, task_id, args, kwargs):
        job = self.request.job
        job.state = celery.states.SUCCESS
        job.finished_at = timezone.now()
        job.save()
        job.refresh_admin_page()
        logger.info(f"Job '{job}' completed successfully in {job.elapsed_str()}.")

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

    def attach_file(
        self, file, name=None, content_type=None, description=None, category=None
    ):
        django_file = File(file, name)
        return self.request.job.attach(django_file, content_type, description, category)

    def attach_content(
        self, content, name, content_type=None, description=None, category=None
    ):
        django_file = ContentFile(content, name)
        return self.request.job.attach(django_file, content_type, description, category)
