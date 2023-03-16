from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag("common/navbar.html", takes_context=True)
def navbar(context):
    from serenity_qa.cms.models import Page
    from serenity_qa.questions.models import Video

    pages = Page.objects.published().order_by("-root_page", "title")
    videos = Video.objects.all().filter(question__isnull=False).distinct()[:8]

    return {
        "videos": videos,
        "pages": pages,
        "self": context.get("self"),
        "query": context.get("query"),
    }

@register.simple_tag(name="load_emoji_fonts", takes_context=True)
def load_emoji_fonts(context):
    request = context['request']
    ua = request.user_agent
    if "Safari" in ua.browser.family:
        return ""
    href = "https://linusg.github.io/serenityos-emoji-font/SerenityOS-Emoji.css"
    return mark_safe(f'<link href="{href}" rel="stylesheet">')
