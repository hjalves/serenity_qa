from django import forms
from django.urls import reverse

from serenity_qa.guestbook.flags import FLAG_FORM_CHOICES
from serenity_qa.guestbook.models import GuestBookMessage, Avatar


class GuestBookMessageForm(forms.ModelForm):
    flag = forms.ChoiceField(
        choices=FLAG_FORM_CHOICES, initial=lambda: "", required=False
    )
    avatar = forms.ModelChoiceField(
        queryset=Avatar.objects.filter(enabled=True),
        initial=Avatar.objects.filter(enabled=True).first,
        empty_label=None,
        to_field_name="slug",
        widget=forms.Select(
            attrs={
                "hx-get": lambda: reverse("guestbook-avatar"),
                "hx-target": "#avatar img",
                "hx-swap": "outerHTML",
            }
        ),
    )
    message = forms.CharField(
        max_length=500, widget=forms.Textarea(attrs={"rows": "3"}), required=True
    )

    class Meta:
        model = GuestBookMessage
        fields = ["name", "flag", "avatar", "message", "hide_user_agent"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Anonymous pal"}),
        }
