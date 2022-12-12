from collections.abc import Mapping
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponseBase
from django.template.response import TemplateResponse
from django.utils.text import capfirst


def action_view(
    function=None, *, permissions=None, label=None, description=None, template=None
):
    def decorator(func):
        @wraps(func)
        def decorated(modeladmin, request, obj_or_qs, **extra_context):
            model = modeladmin.model

            if isinstance(obj_or_qs, QuerySet):
                # This should be improved somewhat
                obj = None
                # obj = obj_or_qs.first()
            else:
                assert isinstance(obj_or_qs, model)
                obj = obj_or_qs

            if not modeladmin.has_view_or_change_permission(request, obj):
                raise PermissionDenied

            opts = model._meta
            app_label = opts.app_label
            tool_name = func.__name__
            tool_label = label or tool_name.replace("_", " ").capitalize()

            context = {
                **modeladmin.admin_site.each_context(request),
                "title": f"{tool_label}: {obj}" if obj else tool_label,
                "subtitle": None,
                "module_name": str(capfirst(opts.verbose_name_plural)),
                "object": obj,
                "opts": opts,
                "preserved_filters": modeladmin.get_preserved_filters(request),
                "action_label": tool_label,
                **(extra_context or {}),
            }
            request.current_app = modeladmin.admin_site.name

            ret = func(modeladmin, request, obj)
            if isinstance(ret, HttpResponseBase) or not isinstance(ret, Mapping):
                return ret

            context.update(ret)
            context_template = context.get("template")

            fallback_template = "admin/action.html"
            if context.get("adminform"):
                fallback_template = "admin/action_form.html"

            return TemplateResponse(
                request,
                template
                or context_template
                or [
                    "admin/%s/%s/actions/%s.html"
                    % (app_label, opts.model_name, tool_name),
                    "admin/%s/actions/%s.html" % (app_label, tool_name),
                    "admin/actions/%s.html" % tool_name,
                    fallback_template,
                ],
                context,
            )

        if permissions is not None:
            decorated.allowed_permissions = permissions
        if label is not None:
            decorated.label = label
        if description is not None:
            decorated.short_description = description
        return decorated

    if function is None:
        return decorator
    else:
        return decorator(function)
