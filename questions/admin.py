from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.utils.html import format_html

from questions.models import Video, Tag, Question
from questions.widgets import DurationWidget


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "link", "published", "questions", "duration")
    actions = ('download', 'fill_metadata')
    readonly_fields = ('questions', )
    formfield_overrides = {
        models.DurationField: {'widget': DurationWidget}
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(question_count=Count('question'))

    def questions(self, obj):
        return obj.question_count

    questions.admin_order_field = 'question_count'

    def link(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.url)

    def download(self, request, queryset):
        for obj in queryset.all():
            obj.download()

    download.short_description = 'Download'

    def fill_metadata(self, request, queryset):
        for obj in queryset.all():
            obj.fill_metadata()

    fill_metadata.short_description = 'Fill metadata'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class QuestionForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects,
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    class Meta:
        model = Question
        fields = '__all__'

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        video_field = self.fields['video']
        timestamp_field = self.fields['timestamp']
        last_question = Question.objects.last()
        if last_question:
            video_field.initial = last_question.video
            timestamp_field.initial = last_question.timestamp
#            timestamp_field.widget.attrs['class'] = 'html-duration-picker'
#            print(timestamp_field.widget)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionForm
    list_display = ('__str__', 'timestamp_link', '_published', '_tags')
    list_filter = ('video', 'tags')
    readonly_fields = ('_url', 'duration')
    formfield_overrides = {
        models.DurationField: {'widget': DurationWidget}
    }
    ordering = ('-id', )
    actions = ('update_duration', )

    def _tags(self, obj):
        return ', '.join(map(str, obj.tags.all()))

    def _url(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.url())

    _url.short_description = "URL"

    def timestamp_link(self, obj):
        return format_html("<a href='{url}'>{timestamp}</a>", url=obj.url(),
                           timestamp=obj.timestamp)

    timestamp_link.short_description = "Timestamp"
    timestamp_link.admin_order_field = 'timestamp'

    def _published(self, obj):
        return obj.video.published

    _published.admin_order_field = 'video__published'

    def update_duration(self, request, queryset):
        for obj in queryset.all():
            obj.duration = obj.compute_duration()
            obj.save(update_fields=['duration'])

    update_duration.short_description = 'Update duration'
