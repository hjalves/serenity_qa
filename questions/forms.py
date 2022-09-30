from django import forms


class VideoQuestionForm(forms.Form):
    timestamp = forms.DurationField(required=True, widget=forms.HiddenInput)

