from django.core.management.base import BaseCommand

from decisions.importer.open_ahjo import OpenAhjoImporter


class Command(BaseCommand):
    help = 'Imports Open Ahjo data'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)
        parser.add_argument('--flush', action='store_true', dest='flush', default=False,
                            help='Delete all existing objects first')

    def handle(self, *args, **options):
        importer = OpenAhjoImporter(options)
        importer.import_data()
