from django import template
from django.contrib.admin.templatetags.base import InclusionAdminNode

register = template.Library()


@register.tag(name="submit_row")
def submit_row_tag(parser, token):
    return InclusionAdminNode(
        parser,
        token,
        func=lambda context: context,
        template_name="action_submit_line.html",
    )
