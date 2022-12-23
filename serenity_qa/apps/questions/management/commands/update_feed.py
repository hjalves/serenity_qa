import logging

from django.core.management.base import BaseCommand

from serenity_qa.apps.questions.tasks import update_feed

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update RSS feed"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        update_feed()
