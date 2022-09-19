from functools import update_wrapper
from urllib.parse import urljoin

from django import forms
from django.contrib import admin
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.contrib.admin.utils import unquote
from django.utils.http import urlencode
from django.utils.text import capfirst

from questions.forms import VideoQuestionForm
from questions.models import Video, Tag, Question, LiveChatMessage
from questions.widgets import DurationWidget


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "link",
        "published",
        "questions",
        "duration",
        "livechat_messages",
    )
    actions = ("download", "fill_metadata", "download_subtitles", "build_livechat")
    readonly_fields = (
        "link",
        "questions",
        "livechat_messages",
        "existing_files",
        "media_files",
    )
    formfield_overrides = {models.DurationField: {"widget": DurationWidget}}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            question_count=Count("question", distinct=True),
            livechat_message_count=Count("livechatmessage", distinct=True),
        )
        print(qs.query)
        return qs

    def existing_files(self, obj):
        return ", ".join(obj.existing_media_files()) or "-"

    existing_files.short_description = "Existing files"

    def questions(self, obj):
        if obj.id:
            params = {"video__id__exact": obj.id}
            query_url = (
                reverse("admin:questions_question_changelist") + "?" + urlencode(params)
            )
            return format_html(
                "<a href='{url}'>{count}</a>", url=query_url, count=obj.question_count
            )

    questions.admin_order_field = "question_count"

    def livechat_messages(self, obj):
        if obj.id:
            params = {"video__id__exact": obj.id}
            query_url = (
                reverse("admin:questions_livechatmessage_changelist")
                + "?"
                + urlencode(params)
            )
            return format_html(
                "<a href='{url}'>{count}</a>",
                url=query_url,
                count=obj.livechat_message_count,
            )

    livechat_messages.admin_order_field = "livechat_message_count"
    livechat_messages.short_description = "livechat"

    def link(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.url)

    def audio(self, obj):
        audio_url = obj.audio_url()
        return format_html("<a href='{url}'>{url}</a>", url=audio_url)

    def media_files(self, obj):
        urls = obj.existing_media_files().items()
        return format_html_join("\n", "<a href='{1}'>{0}: {1}</a><br>", urls)

    # Actions

    def download(self, request, queryset):
        for obj in queryset.all():
            obj.download(only_audio=True)

    download.short_description = "Download audio"

    def fill_metadata(self, request, queryset):
        for obj in queryset.all():
            obj.fill_metadata()

    fill_metadata.short_description = "Fill metadata"

    def download_subtitles(self, request, queryset):
        for obj in queryset.all():
            obj.download(skip_video=True, live_chat=True, subtitles=True)

    download_subtitles.short_description = "Download subtitles and live chat"

    def build_livechat(self, request, queryset):
        for obj in queryset.all():
            obj.build_livechat_questions()

    build_livechat.short_description = "Build livechat questions"

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
    list_display = ("__str__", "_timestamp_link", "duration", "_published", "_tags")
    list_filter = ("video", "tags")
    readonly_fields = ("_url", "duration", "audio_file")
    formfield_overrides = {models.DurationField: {"widget": DurationWidget}}
    ordering = ("-id",)
    actions = ("update_duration", "generate_audio")

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

    def generate_audio(self, request, queryset):
        for obj in queryset.all():
            obj.generate_audio()

    generate_audio.short_description = "Generate audio"


@admin.register(LiveChatMessage)
class LiveChatMessageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "_published", )

    def _published(self, obj):
        return obj.video.published

    _published.admin_order_field = "video__published"
