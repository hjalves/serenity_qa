from django.db.models.signals import post_save
from django.dispatch import receiver

from serenity_qa.questions.models import Video, Tag
from serenity_qa.questions.utils import get_or_set_tag_colors_version


@receiver(post_save, sender=Video)
def auto_download_metadata(sender, instance, created, **kwargs):
    if created:
        instance.download_metadata(live_chat=True, subtitles=True)


@receiver(post_save, sender=Tag)
def refresh_tag_colors_css(*args, **kwargs):
    get_or_set_tag_colors_version(force_set=True)
