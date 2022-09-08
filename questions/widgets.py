from django.forms import TextInput


class DurationWidget(TextInput):
    class Media:
        js = ('js/duration-picker.js', )
        css = {'all': ('css/duration-picker.css', )}

    def __init__(self, attrs=None):
        super().__init__(attrs={'class': 'html-duration-picker', **(attrs or {})})

