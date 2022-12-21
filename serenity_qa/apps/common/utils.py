import json

from django.urls import NoReverseMatch, reverse

from serenity_qa.apps.common.jobs import get_job_redis_connection


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
    redis_client = redis_client or get_job_redis_connection()
    entries = redis_client.xrange(f"job:{job_id}")
    messages = []
    for timestamp, content in entries:
        messages.append(json.loads(content[b"message"]))
    return messages
