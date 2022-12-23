import logging

import feedparser
from django.conf import settings
from django.core.management.base import BaseCommand

from serenity_qa.apps.questions.models import YoutubePost

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update RSS feed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        parsed = feedparser.parse(settings.YOUTUBE_RSS)
        new_entries = 0
        for entry in parsed.entries:
            post, created = YoutubePost.update_or_create_from_feedparser_entry(entry)
            logger.debug(
                "%s: %s - %s (published %s)",
                "created" if created else "updated",
                entry.id,
                entry.title,
                entry.published,
            )
            if created:
                new_entries += 1
        logger.info("%s new entries", new_entries if new_entries > 0 else "no")
