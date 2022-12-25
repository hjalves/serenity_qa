from django.db.models import Sum, Max

from serenity_qa.apps.questions.models import Question, Video


def videos_total():
    return Video.objects.count()


def videos_worked():
    return Video.objects.filter(question__isnull=False).distinct().count()


def videos_done():
    return Video.objects.filter(finished=True).count()


def questions_added():
    return Question.objects.count()


def minutes_total():
    duration_sum = Video.objects.aggregate(Sum("duration"))["duration__sum"]
    return int(duration_sum.total_seconds()) // 60


def minutes_added():
    duration_sum = Question.objects.aggregate(Sum("duration"))["duration__sum"]
    return int(duration_sum.total_seconds()) // 60


def questions_tagged():
    return Question.objects.filter(tags__isnull=False).distinct().count()


def minutes_tagged():
    qs = Question.objects.filter(tags__isnull=False).distinct()
    duration_sum = qs.aggregate(Sum("duration"))["duration__sum"]
    return int(duration_sum.total_seconds()) // 60


def last_changed():
    return Question.objects.all().aggregate(Max("updated_on"))["updated_on__max"]
