import logging

from django.core.management.base import BaseCommand

from serenity_qa.questions.tasks import generate_progress_report

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update RSS feed"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        generate_progress_report(options["force"])
