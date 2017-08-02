from django.core.management.base import BaseCommand

from decisions.importer.helsinki.ahjoxml import AhjoDocument


class Command(BaseCommand):
    help = 'Imports'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)

    def handle(self, *args, **options):
        importer = AhjoDocument(options['filename'])
        print(importer.json)
