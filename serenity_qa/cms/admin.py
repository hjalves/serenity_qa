from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from django.db import models

from serenity_qa.cms.models import Page, Section


class SectionInline(admin.StackedInline):
    model = Section
    extra = 0
    fields = ["component", "arguments", ("enabled", "ordering")]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    inlines = [SectionInline]
    list_display = (
        "title",
        "slug",
        "status",
        "root_page",
        "show_in_nav",
        "created_on",
        "updated_on",
    )
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_on", "updated_on")
    formfield_overrides = {
        models.TextField: {"widget": AdminTextareaWidget({"rows": 15})},
    }
