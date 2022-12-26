from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from .models import Video


def home(request):
    return HttpResponse("<h1>Page was found</h1>")


class VideoView(TemplateView):
    template_name = "questions/video.html"

    def get_context_data(self, **kwargs):
        video_id = kwargs["video"]
        video = get_object_or_404(Video, id=video_id)
        kw = super().get_context_data(**kwargs)
        kw["videos"] = Video.objects.all()
        kw["questions"] = video.question_set.order_by("timestamp")
        kw["video"] = kw["self"] = video
        return kw
