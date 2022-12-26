from django import template

register = template.Library()


@register.inclusion_tag("common/navbar.html", takes_context=True)
def navbar(context):
    from serenity_qa.cms.models import Page
    from serenity_qa.questions.models import Video

    pages = Page.objects.published().order_by("-root_page", "title")
    videos = Video.objects.all().filter(question__isnull=False).distinct()

    return {"videos": videos, "pages": pages, "self": context.get("self")}
