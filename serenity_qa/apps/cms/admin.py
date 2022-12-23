from django.contrib import admin

from serenity_qa.apps.cms.models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status', 'root_page', 'show_in_nav', 'created_on', 'updated_on')
    prepopulated_fields = {'slug': ('title', )}
    readonly_fields = ('created_on', 'updated_on')

