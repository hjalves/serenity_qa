from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import AdminForm
from django.db import models
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.http import urlencode
from django_object_actions import DjangoObjectActions

from .forms import VideoTaskForm
from .models import Video, Tag, Question, LiveChatMessage, YoutubePost
from .tasks import video_dump_data
from .widgets import DurationWidget
from ..common.decorators import action_view


@admin.register(Video)
class VideoAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = (
        "__str__",
        "link",
        "published",
        "questions",
        "duration",
        "livechat_messages",
    )
    actions = (
        "download_audio",
        "download_metadata",
        "fill_metadata",
        "build_livechat",
    )
    readonly_fields = (
        "link",
        "questions",
        "livechat_messages",
        "media_files",
    )
    formfield_overrides = {models.DurationField: {"widget": DurationWidget}}
    change_actions = ("transcribe_questions", "dumpdata")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            question_count=Count("question", distinct=True),
            livechat_message_count=Count("livechatmessage", distinct=True),
        )
        return qs

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

    def download_audio(self, request, queryset):
        for obj in queryset.all():
            obj.download_audio()

    download_audio.short_description = "Download audio"

    def download_metadata(self, request, queryset):
        for obj in queryset.all():
            obj.download_metadata(live_chat=True, subtitles=True)

    download_metadata.short_description = "Download metadata, subtitles, live chat"

    def fill_metadata(self, request, queryset):
        for obj in queryset.all():
            obj.fill_metadata()

    fill_metadata.short_description = "Fill metadata"

    def build_livechat(self, request, queryset):
        for obj in queryset.all():
            obj.build_livechat_questions()

    build_livechat.short_description = "Build livechat questions"

    @action_view(
        label="Transcription",
        description="Open a Youtube player and transcribe questions",
    )
    def transcribe_questions(self, request, obj):
        return {
            "video": obj,
        }

    @action_view(label="Dump data")
    def dumpdata(self, request, obj):
        if request.method == "POST":
            form = VideoTaskForm(data=request.POST)
            if form.is_valid():
                data = form.cleaned_data
                file_format = data["format"].upper()
                description = f"{file_format} data export for: {obj}"
                result = video_dump_data.apply_async(
                    args=(obj.id, data["models"], data["format"]),
                    kwargs={"indent": data["indent"]},
                    description=description,
                )
                return HttpResponseRedirect(result.job.admin_link() + "?download")
        else:
            data = request.GET
            form = VideoTaskForm(initial=data)

        fieldsets = [(None, {"fields": ["models", "format", "indent"]})]
        return {
            "subtitle": "Choose which kind of data to export",
            "adminform": AdminForm(form, fieldsets, {}),
        }


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
    list_display = (
        "__str__",
        "_published",
    )

    def _published(self, obj):
        return obj.video.published

    _published.admin_order_field = "video__published"


@admin.register(YoutubePost)
class YoutubePostAdmin(admin.ModelAdmin):
    list_display = ("title", "published", "updated", "created_on", "is_qa_video")
    readonly_fields = ("created_on", "updated_on", "is_qa_video")
    actions = ["add_as_video"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def add_as_video(self, request, queryset):
        for obj in queryset.all():
            video, created = obj.get_or_create_video()

    add_as_video.short_description = "Add as Q&A video"

    def is_qa_video(self, obj):
        return obj.is_qa_video()

    is_qa_video.short_description = "QA?"
    is_qa_video.boolean = True
