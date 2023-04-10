from django.contrib import admin

from serenity_qa.guestbook.models import GuestBookMessage, Avatar


@admin.register(GuestBookMessage)
class GuestBookMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "__str__", "flag", "ip_address", "hide", "created_on")
    list_display_links = ("id", "__str__")
    readonly_fields = (
        "user_agent",
        "parsed_user_agent",
        "created_on",
        "updated_on",
    )

    def parsed_user_agent(self, obj):
        return obj.parsed_user_agent()


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "width", "height", "image", "enabled", "created_on")
    list_display_links = ("slug", "name")
    readonly_fields = ("width", "height", "created_on", "image_tag")
    prepopulated_fields = {"slug": ("name",)}

    def image_tag(self, obj):
        return obj.image_tag()
