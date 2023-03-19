import datetime

from django import template
from django.core.cache import cache
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from serenity_qa.questions.models import Tag
from serenity_qa.questions.utils import get_or_set_tag_colors_version

register = template.Library()


@register.inclusion_tag("common/navbar.html", takes_context=True)
def navbar(context):
    from serenity_qa.cms.models import Page
    from serenity_qa.questions.models import Video

    pages = Page.objects.published().order_by("-root_page", "title")
    videos = Video.objects.all().filter(question__isnull=False).distinct()[:8]
    tags = Tag.objects.all().order_by('-id')[:5]

    return {
        "videos": videos,
        "tags": tags,
        "pages": pages,
        "self": context.get("self"),
        "query": context.get("query"),
        "in_root": context.get("in_root"),
        "max_responsive": 4
    }


@register.simple_tag(name="load_emoji_fonts", takes_context=True)
def load_emoji_fonts(context):
    request = context["request"]
    ua = request.user_agent
    if "Safari" in ua.browser.family:
        return ""
    href = "https://linusg.github.io/serenityos-emoji-font/SerenityOS-Emoji.css"
    return mark_safe(f'<link href="{href}" rel="stylesheet">')


@register.simple_tag(name="tag_colors_css")
def tag_colors_css():
    value = get_or_set_tag_colors_version()
    css_href = reverse("tag-colors")
    return mark_safe(f'<link href="{css_href}?{value}" rel="stylesheet">')
