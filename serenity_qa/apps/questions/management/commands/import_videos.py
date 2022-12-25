import argparse
import logging

from django.core.management.base import BaseCommand

from serenity_qa.apps.questions.models import Video

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import videos"

    def add_arguments(self, parser):
        parser.add_argument('infile', type=argparse.FileType('r'))

    def handle(self, *args, **options):
        infile = options['infile']
        for line in infile.readlines():
            url, sep, rem = line.partition('?v=')
            if rem := rem.strip():
                Video.objects.get_or_create(code=rem)
