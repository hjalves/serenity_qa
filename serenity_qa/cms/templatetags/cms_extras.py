from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from markdown import Markdown

register = template.Library()
md = Markdown(extensions=["markdown.extensions.fenced_code", "smarty"])


@register.filter()
@stringfilter
def markdown(value):
    converted = md.convert(value)
    return mark_safe(converted)
