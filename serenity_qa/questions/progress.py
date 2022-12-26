from statistics import NormalDist

from django.db.models import Sum, Max

from serenity_qa.questions.models import Question, Video


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
    if duration_sum:
        return int(duration_sum.total_seconds()) // 60
    return 0


def questions_tagged():
    return Question.objects.filter(tags__isnull=False).distinct().count()


def minutes_tagged():
    qs = Question.objects.filter(tags__isnull=False).distinct()
    duration_sum = qs.aggregate(Sum("duration"))["duration__sum"]
    if duration_sum:
        return int(duration_sum.total_seconds()) // 60
    return 0


def last_changed():
    return Question.objects.all().aggregate(Max("updated_on"))["updated_on__max"]


def estimate_questions(confidence=0.95):
    total_s = minutes_total() * 60

    qs = Question.objects.filter(duration__isnull=False)
    durations_s = [x.total_seconds() for x in qs.values_list("duration", flat=True)]
    low, high = confidence_interval(durations_s, confidence)

    questions_min = total_s / high
    questions_max = total_s / low

    expected = questions_min + (questions_max - questions_min) / 2
    interval = questions_max - expected
    return int(round(expected, 0)), int(round(interval, 0))


def confidence_interval(data, confidence=0.95):
    """Use only when sample size if big enough (ie: more than ~100 points)"""

    dist = NormalDist.from_samples(data)
    z = NormalDist().inv_cdf((1 + confidence) / 2.0)
    h = dist.stdev * z / ((len(data) - 1) ** 0.5)
    return dist.mean - h, dist.mean + h
