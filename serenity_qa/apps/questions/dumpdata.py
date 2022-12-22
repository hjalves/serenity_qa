import sys

from django.core import serializers
from django.core.management.commands import dumpdata
from django.core.serializers.base import ProgressBar

from serenity_qa.apps.questions.models import Video


class ProgressWrapper:
    progress_width = ProgressBar.progress_width

    def __init__(self, task=None):
        self.task = task

    def write(self, s):
        current = s.count(".")
        total = self.progress_width
        if not self.task:
            print(s)
            return
        self.task.log_progress(current=current, total=total, message="Writing...")

    def flush(self):
        pass


def questions_dumpdata(question_id, models, format, indent=None):
    def get_objects(count_only=False):
        queryset = Video.objects.get_queryset().filter(id=question_id)
        obj = queryset.get()
        if "video" in models:
            if count_only:
                yield queryset.order_by().count()
            else:
                yield from queryset.iterator()

        if "question" in models:
            queryset = obj.question_set.all()
            if count_only:
                yield queryset.order_by().count()
            else:
                yield from queryset.iterator()

        if "livechat" in models:
            queryset = obj.livechatmessage_set.all()
            if count_only:
                yield queryset.order_by().count()
            else:
                yield from queryset.iterator()

    with open("output.json", "wt") as stream:
        serializers.serialize(
            format,
            get_objects(),
            indent=indent,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            stream=stream,
            progress_output=ProgressWrapper(),
            object_count=sum(get_objects(count_only=True)),
        )
