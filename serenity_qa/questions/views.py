from django.core import serializers
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView

from .models import Video, Tag, Question
from .utils import serializer_format_to_mimetype


def home(request):
    return HttpResponse("<h1>Page was found</h1>")


class ExportMixin:
    def export(self, data_format="json", **kwargs):
        context = self.get_context_data(**kwargs)
        serialized = serializers.serialize(
            data_format,
            self.export_queryset(context),
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            indent=2,
        )
        content_type = serializer_format_to_mimetype(data_format)
        return HttpResponse(serialized, content_type=content_type)

    def get(self, request, *args, **kwargs):
        data_format = (request.GET.get("format") or "").lower()
        if data_format in ("json", "jsonl", "xml", "yaml", "kdl"):
            return self.export(data_format, **kwargs)
        return super().get(request, *args, **kwargs)


class VideoDetailView(ExportMixin, TemplateView):
    template_name = "questions/video_detail.html"

    def get_video(self, video_key):
        try:
            video_date = parse_date(video_key)
            if not video_date:
                video_id = int(video_key)
                video = get_object_or_404(Video, id=video_id)
            else:
                video = get_object_or_404(Video, published=video_date)
        except ValueError:
            raise Http404(f"The video key should be a date or id.")
        return video

    def get_context_data(self, **kwargs):
        kw = super().get_context_data(**kwargs)
        video = self.get_video(kw["video"])
        kw["questions"] = video.question_set.order_by("timestamp")
        kw["video"] = kw["self"] = video
        return kw

    def export_queryset(self, context):
        yield context["video"]
        yield from context["questions"]


class TagsCSSView(TemplateView):
    template_name = "questions/tags.css"
    content_type = "text/css"

    def get_context_data(self, **kwargs):
        kw = super().get_context_data(**kwargs)
        kw["tags"] = Tag.objects.all()
        return kw


class VideoListView(TemplateView):
    template_name = "questions/video_list.html"
    extra_context = {"self": "video-list"}


class TagListView(TemplateView):
    template_name = "questions/tag_list.html"
    extra_context = {"self": "tag-list"}


class TagDetailView(ExportMixin, TemplateView):
    template_name = "questions/tag_detail.html"

    def get_context_data(self, **kwargs):
        kw = super().get_context_data(**kwargs)
        tag = get_object_or_404(Tag, slug=kwargs["slug"])
        kw["questions"] = tag.question_set.order_by("-video__published", "-timestamp")
        kw["tag"] = kw["self"] = tag
        return kw

    def export_queryset(self, context):
        yield context["tag"]
        yield from context["questions"]


class SearchView(ExportMixin, TemplateView):
    template_name = "questions/search.html"
    extra_context = {"self": "search"}

    def get_context_data(self, **kwargs):
        kw = super().get_context_data(**kwargs)
        query = kw["query"] = self.request.GET.get("q")
        qs = Question.objects.search(query).order_by("-video__published", "-timestamp")
        kw["questions"] = qs
        kw["results"] = qs.count()
        return kw

    def export_queryset(self, context):
        yield from context["questions"]
