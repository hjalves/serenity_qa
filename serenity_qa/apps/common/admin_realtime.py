import time
from functools import update_wrapper, wraps

from django import forms
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django_htmx.http import HttpResponseClientRefresh


class ModelAdminRealtime(admin.ModelAdmin):
    autorefresh = None

    @property
    def media(self):
        return super().media + forms.Media(js=["js/htmx.min.js"])

    def get_urls(self):
        urls = super().get_urls()
        return self._get_realtime_urls() + urls

    def _get_realtime_urls(self):
        from django.urls import path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        app_label, model_name = self.model._meta.app_label, self.model._meta.model_name

        return [
            path(
                "<path:object_id>/getfield/",
                wrap(self.getfield_view),
                name=f"{app_label}_{model_name}_getfield",
            ),
            path(
                "<path:object_id>/refresh/",
                wrap(self.refresh_view),
                name=f"{app_label}_{model_name}_refresh",
            ),
        ]

    def get_autorefresh(self, object_id=None):
        autorefresh = self.autorefresh
        if isinstance(autorefresh, int):
            return f"{autorefresh}s"
        assert isinstance(autorefresh, str)
        return autorefresh

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(autorefresh=self.get_autorefresh(object_id))
        return super().change_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(autorefresh=self.get_autorefresh())
        return super().changelist_view(request, extra_context)

    def getfield_view(self, request, object_id, extra_context=None):
        field = request.GET.get("field")
        if not field:
            return HttpResponse(status=400)
        obj = self.get_object(request, unquote(object_id))
        if not obj:
            return HttpResponse(status=404)
        value = getattr(self, field)(obj)
        return HttpResponse(content=value)

    def refresh_view(self, request, object_id, extra_context=None):
        try:
            page_refresh_time = request.GET.get("last")
            if page_refresh_time:
                page_refresh_time = int(page_refresh_time)
        except ValueError:
            page_refresh_time = None
        last_refresh_time = self.last_refresh_time(object_id)
        if (
            not last_refresh_time
            or not page_refresh_time
            or page_refresh_time > last_refresh_time
        ):
            return HttpResponse(status=204)
        return HttpResponseClientRefresh()

    def getfield_url(self, object_id):
        info = self.model._meta.app_label, self.model._meta.model_name
        return reverse(
            "admin:%s_%s_getfield" % info,
            args=(object_id,),
            current_app=self.admin_site.name,
        )

    @classmethod
    def refresh_key(cls, model, object_id):
        app_label, model_name = model._meta.app_label, model._meta.model_name
        if object_id is None:
            return f"admin_refresh:{app_label}.{model_name}"
        return f"admin_refresh:{app_label}.{model_name}:{object_id}"

    @classmethod
    def perform_refresh(cls, model, object_id=None):
        refresh_key = cls.refresh_key(model, object_id)
        refresh_timestamp = int(time.time())
        cache.set(refresh_key, refresh_timestamp)

    def last_refresh_time(self, object_id=None):
        refresh_key = self.refresh_key(self.model, object_id)
        last_refresh = cache.get(refresh_key)
        return last_refresh

    def refresh_this_admin(self, object_id=None):
        self.perform_refresh(self.model, object_id)


def autoupdate(function=None, *, polling=1000, condition=None):
    def decorator(func):
        @wraps(func)
        def decorated(modeladmin, obj):
            result = func(modeladmin, obj)
            if condition and not condition(obj):
                return result
            get_link = modeladmin.getfield_url(obj.pk)
            get_link += "?" + urlencode({"field": func.__name__})
            hx_trigger = f"load delay:{polling}ms"
            html_div = '<div hx-get="{}" hx-trigger="{}" hx-swap="outerHTML">{}</div>'
            return format_html(html_div, get_link, hx_trigger, result)

        decorated.auto_update = True
        return decorated

    if function is None:
        return decorator
    else:
        return decorator(function)
