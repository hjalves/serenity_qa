from functools import update_wrapper

from django import forms
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.admin.utils import unquote
from django.utils.http import urlencode
from django.utils.text import capfirst

from questions.forms import VideoQuestionForm
from questions.models import Video, Tag, Question
from questions.widgets import DurationWidget


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "link", "published", "questions", "duration")
    actions = ("download", "fill_metadata")
    readonly_fields = ("link", "questions")
    formfield_overrides = {models.DurationField: {"widget": DurationWidget}}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(question_count=Count("question"))

    def questions(self, obj):
        params = {"video__id__exact": obj.id}
        query_url = (
            reverse("admin:questions_question_changelist") + "?" + urlencode(params)
        )
        return format_html(
            "<a href='{url}'>{count}</a>", url=query_url, count=obj.question_count
        )

    questions.admin_order_field = "question_count"

    def link(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.url)

    def download(self, request, queryset):
        for obj in queryset.all():
            obj.download(only_audio=True)

    download.short_description = "Download audio"

    def fill_metadata(self, request, queryset):
        for obj in queryset.all():
            obj.fill_metadata()

    fill_metadata.short_description = "Fill metadata"

    def get_urls(self):
        from django.urls import path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                "<path:object_id>/questions/",
                wrap(self.questions_view),
                name="%s_%s_questions" % info,
            ),
            *super().get_urls(),
        ]

    def questions_view(self, request, object_id, extra_context=None):
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(
                request, model._meta, object_id
            )

        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        # Then get the history for this object.
        opts = model._meta
        app_label = opts.app_label

        form = VideoQuestionForm(initial={})

        context = {
            **self.admin_site.each_context(request),
            "title": "Questions: %s" % obj,
            "module_name": str(capfirst(opts.verbose_name_plural)),
            "object": obj,
            "opts": opts,
            "media": form.media,
            "preserved_filters": self.get_preserved_filters(request),
            "embed_url": obj.embed_url,
            "form": form,
            "video": obj,
            **(extra_context or {}),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.object_history_template
            or [
                "admin/%s/%s/video_questions.html" % (app_label, opts.model_name),
                "admin/%s/video_questions.html" % app_label,
                "admin/video_questions.html",
            ],
            context,
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class QuestionForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects, widget=forms.CheckboxSelectMultiple(), required=False
    )

    class Meta:
        model = Question
        fields = "__all__"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        video_field = self.fields["video"]
        timestamp_field = self.fields["timestamp"]
        last_question = Question.objects.last()
        if last_question:
            video_field.initial = last_question.video
            timestamp_field.initial = last_question.timestamp


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionForm
    list_display = ("__str__", "_timestamp_link", "_published", "_tags")
    list_filter = ("video", "tags")
    readonly_fields = ("_url", "duration")
    formfield_overrides = {models.DurationField: {"widget": DurationWidget}}
    ordering = ("-id",)
    actions = ("update_duration",)

    def _tags(self, obj):
        return ", ".join(map(str, obj.tags.all()))

    def _url(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.url())

    _url.short_description = "URL"

    def _timestamp_link(self, obj):
        return format_html(
            "<a href='{url}'>{timestamp}</a>", url=obj.url(), timestamp=obj.timestamp
        )

    _timestamp_link.short_description = "Timestamp"
    _timestamp_link.admin_order_field = "timestamp"

    def _published(self, obj):
        return obj.video.published

    _published.admin_order_field = "video__published"

    def update_duration(self, request, queryset):
        for obj in queryset.all():
            obj.duration = obj.compute_duration()
            obj.save(update_fields=["duration"])

    update_duration.short_description = "Update duration"
