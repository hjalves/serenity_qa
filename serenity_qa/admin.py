from collections import defaultdict

from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class MyAdminConfig(AdminConfig):
    default_site = "serenity_qa.admin.MyAdminSite"


class MyAdminSite(AdminSite):
    site_title = "SerenityOS Q&A"
    site_header = "SerenityOS Q&A"
    index_title = "Administration"

    def __init__(self, *a, **kw):
        from django.contrib.sessions.models import Session

        super().__init__(*a, **kw)
        self.register(Session)

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
