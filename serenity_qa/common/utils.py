from traceback import format_exception_only

from django.urls import NoReverseMatch, reverse

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
