import feedparser
from django.conf import settings
from django.core.management.base import BaseCommand

from serenity_qa.apps.questions.models import YoutubePost


class Command(BaseCommand):
    help = "Update RSS feed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        parsed = feedparser.parse(settings.YOUTUBE_RSS)
        for entry in parsed.entries:
            YoutubePost.add_from_feedparser_entry(entry)
