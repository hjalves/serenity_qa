from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import AdminForm
from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Count, OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.http import urlencode
from django_object_actions import DjangoObjectActions

from serenity_qa.common.decorators import action_view
from .forms import VideoTaskForm
from .models import (
    Video,
    Tag,
    Question,
    LiveChatMessage,
    YoutubePost,
    QuestionAudio,
    ProgressReport,
)
from .tasks import video_dump_data
from .widgets import DurationWidget
from ..common.utils import format_link


@admin.register(Video)
class VideoAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = (
        "id",
        "__str__",
        "short_link",
        "published",
        "questions",
        "duration",
        "livechat_messages",
    )
    list_filter = ("finished", "published")
    list_display_links = (
        "id",
        "__str__",
    )
    actions = (
        "download_metadata",
        "download_audio",
        "import_metadata",
    )
    readonly_fields = (
        "short_link",
        "link",
        "questions",
        "livechat_messages",
        "media_files",
    )
    formfield_overrides = {models.DurationField: {"widget": DurationWidget}}
    change_actions = ("timestamp_questions", "dumpdata")
    date_hierarchy = "published"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            question__count=Count("question", distinct=True),
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
                "<a href='{url}'>{count}</a>", url=query_url, count=obj.question__count
            )

    questions.admin_order_field = "question__count"

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

    def short_link(self, obj):
        return format_link(obj.short_url)

    def link(self, obj):
        return format_link(obj.url, show_scheme=True)

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

    download_metadata.short_description = "Download metadata"

    def import_metadata(self, request, queryset):
        for obj in queryset.all():
            if obj.metadata_path().exists():
                obj.import_metadata()
            if obj.live_chat_path().exists():
                obj.import_livechat()

    import_metadata.short_description = "Import metadata"

    @action_view(
        label="Timestamp questions",
        description="Open a Youtube player and transcribe/timestamp questions",
    )
    def timestamp_questions(self, request, obj):
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
    list_display = (
        "id",
        "name",
        "slug",
        "emoji",
        "serenity_emoji",
        "color",
    )
    list_display_links = (
        "id",
        "name",
    )
    list_editable = ("color",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("serenity_emoji_preview",)

    def serenity_emoji(self, obj):
        return format_html('<span class="serenity-emoji">{}</span>', obj.emoji)

    def serenity_emoji_preview(self, obj):
        return format_html('<span class="serenity-emoji-preview">{}</span>', obj.emoji)


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


class QuestionAudioAdmin(admin.TabularInline):
    model = QuestionAudio
    readonly_fields = ("audio_file", "updated_on")
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionAudioAdmin]
    form = QuestionForm
    list_display = ("id", "__str__", "_timestamp_link", "duration", "_published", "_tags")
    list_display_links = (
        "id",
        "__str__",
    )
    list_filter = ("video", "tags")
    readonly_fields = ("_url", "duration", "created_on", "updated_on")
    fields = (
        "video",
        ("timestamp", "duration"),
        "question",
        "tags",
        "_url",
        "created_on",
        "updated_on",
    )
    formfield_overrides = {
        models.DurationField: {"widget": DurationWidget},
        models.TextField: {"widget": AdminTextareaWidget({"rows": 4})},
    }
    ordering = (
        "-video__published",
        "-timestamp",
    )
    actions = ("update_duration", "generate_audio")
    date_hierarchy = "video__published"

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
            obj.refresh_duration()

    update_duration.short_description = "Refresh duration"

    def generate_audio(self, request, queryset):
        for obj in queryset.all():
            obj.generate_audio()

    generate_audio.short_description = "Generate audio"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            try:
                extra_context["previous"] = obj.get_previous()
            except ObjectDoesNotExist:
                extra_context["previous"] = None
            try:
                extra_context["next"] = obj.get_next()
            except ObjectDoesNotExist:
                extra_context["next"] = None
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )


@admin.register(LiveChatMessage)
class LiveChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "__str__",
        "_published",
    )
    list_display_links = (
        "id",
        "__str__",
    )

    def _published(self, obj):
        return obj.video.published

    _published.admin_order_field = "video__published"

    def has_add_permission(self, request):
        return False


@admin.register(YoutubePost)
class YoutubePostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "published",
        "updated",
        "created_on",
        "is_qa_video",
        "video_id",
    )
    list_display_links = ("id", "title")
    readonly_fields = ("created_on", "updated_on", "is_qa_video", "video_id")
    actions = ["add_as_video"]
    date_hierarchy = "published"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        subquery = Video.objects.filter(code=OuterRef("yt_videoid")).values("id")[:1]
        return qs.annotate(video_id=Subquery(subquery))

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

    def video_id(self, obj):
        return obj.video_id


@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_on",
        "videos_total",
        "questions_added",
        "percentage_added",
        "questions_remaining",
    )
    list_display_links = (
        "id",
        "created_on",
    )
    readonly_fields = (
        "created_on",
        "indicators",
    )
    date_hierarchy = "created_on"

    def percentage_added(self, obj):
        return obj.indicators.get("percentage_added")

    def videos_total(self, obj):
        return obj.indicators.get("videos_total")

    def questions_added(self, obj):
        return obj.indicators.get("questions_added")

    def questions_remaining(self, obj):
        return obj.indicators.get("questions_remaining")

    def has_add_permission(self, request):
        return False
