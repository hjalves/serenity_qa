from django import forms


class VideoQuestionForm(forms.Form):
    timestamp = forms.DurationField(required=True, widget=forms.HiddenInput)


class VideoTaskForm(forms.Form):
    CHOICES = [
        ('choice1', 'Choice 1'),
        ('choice2', 'Choice 2'),
    ]
    task_name = forms.ChoiceField(choices=CHOICES)
    arguments = forms.CharField(max_length=250)
