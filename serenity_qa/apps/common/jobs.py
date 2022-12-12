import celery.states
from celery.app.task import Task
from celery.utils.log import get_task_logger
from django.utils import timezone
from kombu.utils import uuid

from .models import Job

logger = get_task_logger(__name__)


class JobTask(Task):
    track_started = True
    description = None

    def apply_async(self, args=None, kwargs=None, task_id=None, **extra):
        task_id = task_id or uuid()
        job = Job.objects.create(
            task_id=task_id,
            task_name=self.name,
            state=celery.states.PENDING,
            description=self.description or "",
        )
        result = super().apply_async(args, kwargs, task_id, **extra)
        result.job = job
        return result

    def __call__(self, *args, **kwargs):
        job, _ = Job.objects.update_or_create(
            task_id=self.request.id,
            defaults={
                "state": celery.states.STARTED,
                "started_at": timezone.now(),
                "task_name": self.request.task,
                "description": self.description or "",
            },
        )
        self.request.job = job
        return super(JobTask, self).__call__(*args, **kwargs)

    def on_success(self, retval, task_id, args, kwargs):
        job = self.request.job
        job.state = celery.states.SUCCESS
        job.finished_at = timezone.now()
        job.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job = self.request.job
        job.state = celery.states.FAILURE
        job.finished_at = timezone.now()
        job.save()

    def set_progress(self, current=None, total=None, message=None):
        meta = {}
        if current is not None:
            meta["current"] = current
        if total is not None:
            meta["total"] = total
        if current is not None and total is not None:
            meta["percentage"] = round(100.0 * current / total, 1)
        if message is not None:
            meta["message"] = message
        self.update_state(state="PROGRESS", meta=meta)
        logger.info(" ".join(f"{key}={value!r}" for key, value in meta.items()))

    # def attach_file(self, file, name=None, content_type=None, description=None):
    #     django_file = File(file, name)
    #     return self.request.job.attach(django_file, content_type, description)
    #
    # def attach_content(self, content, name, content_type=None, description=None):
    #     django_file = ContentFile(content, name)
    #     return self.request.job.attach(django_file, content_type, description)
