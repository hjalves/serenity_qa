import json
from traceback import format_exception_only

import magic
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
    file.seek(0)
    # "HOWMANY" constant in libmagic (bytes needed to find type): 65536
    mimetype = magic.from_buffer(file.read(65536), mime=True)
    file.seek(0)
    return mimetype


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


# redis streams


def get_job_log(job_id, redis_client=None):
    from serenity_qa.apps.common.jobs import get_job_redis_connection

    redis_client = redis_client or get_job_redis_connection()
    entries = redis_client.xrange(f"job:{job_id}")
    messages = []
    for timestamp, content in entries:
        messages.append(json.loads(content[b"message"]))
    return messages
