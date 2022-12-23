from django.db.models.signals import post_save
from django.dispatch import receiver

from serenity_qa.apps.questions.models import Video


@receiver(post_save, sender=Video)
def auto_download_metadata(sender, instance, created, **kwargs):
    if created:
        instance.download_metadata(live_chat=True, subtitles=True)
