from django.core.serializers.base import ProgressBar


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
        self.task.log_progress(current=current, total=total, message="Exporting...")

    def flush(self):
        pass


def get_objects_from_querysets(*querysets, count_only=False):
    for queryset in querysets:
        if count_only:
            yield queryset.order_by().count()
        else:
            yield from queryset.iterator()
