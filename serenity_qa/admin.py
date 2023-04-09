from collections import defaultdict
import pprint

from django.conf import settings
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.admin.apps import AdminConfig
from django.utils.html import format_html


class MyAdminConfig(AdminConfig):
    default_site = "serenity_qa.admin.MyAdminSite"


class MyAdminSite(AdminSite):
    site_title = "SerenityOS Q&A"
    site_header = "SerenityOS Q&A"
    index_title = "Administration"

    def __init__(self, *a, **kw):
        from django.contrib.sessions.models import Session

        class SessionAdmin(ModelAdmin):
            def _session_data(self, obj):
                formatted = pprint.pformat(obj.get_decoded())
                return format_html("<pre>{}</pre>", formatted)

            _session_data.short_description = "Session data"

            list_display = ["session_key", "expire_date"]
            readonly_fields = ["_session_data"]
            exclude = ["session_data"]
            date_hierarchy = "expire_date"

        super().__init__(*a, **kw)
        self.register(Session, SessionAdmin)

    def each_context(self, request):
        context = super().each_context(request)
        available_apps = self.customize_sidebar(context["available_apps"])
        context["available_apps"] = available_apps
        return context

    def customize_sidebar(self, available_apps):
        sidebar_exclude = getattr(settings, "SIDEBAR_EXCLUDE", [])
        apps = []
        exclude_apps = set()
        exclude_models = defaultdict(set)

        for name in sidebar_exclude:
            name = name.lower()
            app_label, sep, object_name = name.partition(".")
            if sep:
                exclude_models[app_label].add(object_name)
            else:
                exclude_apps.add(name)

        for app in available_apps:
            if app["app_label"] in exclude_apps:
                continue
            app = dict(app)
            app["models"] = [
                m
                for m in app["models"]
                if m["object_name"].lower() not in exclude_models[app["app_label"]]
            ]
            apps.append(app)
        return apps
