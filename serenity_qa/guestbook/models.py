import user_agents
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geoip2 import GeoIP2
from django.db import models
from django.utils.safestring import mark_safe
from geoip2.errors import AddressNotFoundError

from serenity_qa.guestbook.flags import FLAG_MODEL_CHOICES, get_flag_emoji
from serenity_qa.questions.models import Question


class Avatar(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    image = models.ImageField(
        upload_to="avatars/", height_field="height", width_field="width"
    )
    width = models.IntegerField(blank=True, null=True, editable=False)
    height = models.IntegerField(blank=True, null=True, editable=False)
    enabled = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "avatar"
        verbose_name_plural = "avatars"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def image_tag(self):
        return mark_safe(f'<img src="{self.image.url}" alt="{self.name}">')


class GuestBookMessage(models.Model):
    name = models.CharField(max_length=50, blank=True)
    flag = models.CharField(max_length=12, blank=True, choices=FLAG_MODEL_CHOICES)
    avatar = models.ForeignKey(Avatar, blank=True, null=True, on_delete=models.SET_NULL)
    message = models.TextField(blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField("IP address", blank=True, null=True)
    hide = models.BooleanField(blank=True, default=False)
    hide_user_agent = models.BooleanField(blank=True, default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "message"
        verbose_name_plural = "messages"
        ordering = ('-created_on', )

    def __str__(self):
        name = self.name or "<Anon>"
        message = self.message[:50] + "..." if len(self.message) > 50 else self.message
        return f"[{name}] {message}"

    def parsed_user_agent(self):
        return user_agents.parse(self.user_agent)

    def ip_address_country_code(self):
        geoip = GeoIP2()
        try:
            return geoip.country_code(self.ip_address)
        except AddressNotFoundError:
            return None

    def display_name(self):
        return self.name or "Anonymous pal"

    def display_user_agent(self):
        if self.hide_user_agent:
            return "an unknown client"
        parsed = self.parsed_user_agent()
        return f"{parsed.browser.family} on {parsed.os.family}"

    def display_flag(self):
        if self.flag:
            return get_flag_emoji(self.flag)
        return ""
