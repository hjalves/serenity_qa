from django import forms
from django.core.serializers import (
    get_public_serializer_formats,
    get_serializer_formats,
)
from django.forms import CheckboxSelectMultiple


class VideoQuestionForm(forms.Form):
    timestamp = forms.DurationField(required=True, widget=forms.HiddenInput)


class VideoTaskForm(forms.Form):
    MODEL_CHOICES = [
        ("video", "Q&A video"),
        ("question", "Questions"),
        ("livechat", "Livechat messages"),
    ]
    FORMAT_CHOICES = [
        ("json", "JSON"),
        ("jsonl", "JSONL"),
        ("xml", "XML"),
        ("yaml", "YAML"),
        ("python", "Python"),
    ]
    # FORMAT_CHOICES = [(k, k.upper()) for k in get_public_serializer_formats()]
    models = forms.MultipleChoiceField(
        choices=MODEL_CHOICES,
        widget=CheckboxSelectMultiple,
        initial=["video", "question"],
    )
    format = forms.ChoiceField(choices=FORMAT_CHOICES, initial=["json"])
    indent = forms.IntegerField(min_value=0, required=False, initial=4)
