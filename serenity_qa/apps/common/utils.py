from django.urls import NoReverseMatch, reverse


def get_object_admin_link(obj):
    try:
        return reverse(
            "admin:{}_{}_change".format(obj._meta.app_label, obj._meta.model_name),
            args=(obj.pk,),
        )
    except NoReverseMatch:
        return None
