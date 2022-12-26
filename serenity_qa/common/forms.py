from django import forms


class DumpDataForm(forms.Form):
    MODELNAME_CHOICES = [
        ("questions.Video", "questions.Video"),
    ]
    model_name = forms.ChoiceField(choices=MODELNAME_CHOICES)
    arguments = forms.CharField(max_length=250, required=False)
