from django import forms
from django.forms import TextInput

from questions.widgets import DurationWidget


class VideoQuestionForm(forms.Form):
    timestamp = forms.DurationField(required=True, widget=forms.HiddenInput)
    question = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"size": 50})
    )
