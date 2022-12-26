from django.contrib import admin

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
