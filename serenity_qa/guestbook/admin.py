from django.contrib import admin
from django.contrib.gis.geoip2 import GeoIP2Exception

from serenity_qa.common.utils import format_exception
from serenity_qa.guestbook.flags import get_flag_emoji
from serenity_qa.guestbook.models import GuestBookMessage, Avatar


@admin.register(GuestBookMessage)
class GuestBookMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "__str__", "flag", "ip_address_cc", "hide", "created_on")
    list_display_links = ("id", "__str__")
    readonly_fields = (
        "country_code",
        "user_agent",
        "parsed_user_agent",
        "created_on",
        "updated_on",
    )

    def parsed_user_agent(self, obj):
        return obj.parsed_user_agent()

    def country_code(self, obj):
        try:
            return obj.ip_address_country_code() or "-"
        except GeoIP2Exception as e:
            return "[Error] %s" % format_exception(e)

    country_code.short_description = "IP country code"

    def ip_address_cc(self, obj):
        try:
            cc = obj.ip_address_country_code()
        except Exception:
            cc = None
        emoji = get_flag_emoji(cc) if cc else ""
        return f"{emoji} {obj.ip_address}"

    ip_address_cc.short_description = "IP address"


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "width", "height", "image", "enabled", "created_on")
    list_display_links = ("slug", "name")
    readonly_fields = ("width", "height", "created_on", "image_tag")
    prepopulated_fields = {"slug": ("name",)}

    def image_tag(self, obj):
        return obj.image_tag()
