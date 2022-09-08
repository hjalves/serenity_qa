from collections import defaultdict

from django.conf import settings
from django.contrib.admin import AdminSite


class MyAdminSite(AdminSite):
    site_title = "SerenityOS Q&A"
    site_header = "SerenityOS Q&A"
    index_title = "Administration"
