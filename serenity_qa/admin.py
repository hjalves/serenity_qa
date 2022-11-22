from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class MyAdminSite(AdminSite):
    site_title = "SerenityOS Q&A"
    site_header = "SerenityOS Q&A"
    index_title = "Administration"


class MyAdminConfig(AdminConfig):
    default_site = "serenity_qa.admin.MyAdminSite"
