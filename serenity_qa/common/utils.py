from traceback import format_exception_only

import user_agents
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html

suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]


def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def discover_type(file):
    try:
        import magic

        file.seek(0)
        # "HOWMANY" constant in libmagic (bytes needed to find type): 65536
        mimetype = magic.from_buffer(file.read(65536), mime=True)
        file.seek(0)
        return mimetype
    except ImportError:
        return None


def format_exception(ex):
    return format_exception_only(ex.__class__, ex)[-1].strip()


def get_object_admin_link(obj):
    try:
        return reverse(
            "admin:{}_{}_change".format(obj._meta.app_label, obj._meta.model_name),
            args=(obj.pk,),
        )
    except NoReverseMatch:
        return None


def get_user_agent(request):
    if not hasattr(request, "META"):
        return ""
    ua_string = request.META.get("HTTP_USER_AGENT", "")
    user_agent = user_agents.parse(ua_string)
    return user_agent


def format_link(url, show_scheme=False):
    display_url = url
    if not show_scheme:
        _, _, display_url = url.partition("://")
    return format_html(
        "<a href='{url}'>{display}</a>", url=url, display=display_url or url
    )
