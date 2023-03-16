import bleach
import markdown as md
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

ALLOWED_QUESTION_TAGS = frozenset(("a", "abbr", "code", "em", "strong"))

register = template.Library()


@register.filter
def format_duration(duration):
    if not duration:
        return None
    seconds = duration.total_seconds()
    assert seconds < 3600
    mm, ss = divmod(seconds, 60)
    return "%dmin %ds" % (mm, ss)


@register.filter()
@stringfilter
def format_question(value):
    text = md.markdown(value, extensions=["abbr"])
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_QUESTION_TAGS,
        strip=True,
    )
    return mark_safe(cleaned)
