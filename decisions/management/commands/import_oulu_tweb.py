from django.core.management.base import BaseCommand

from decisions.importer.oulu_tweb import OuluTwebImporter


class Command(BaseCommand):
    help = 'Imports Open Ahjo data'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str)
        parser.add_argument('--flush', action='store_true', dest='flush', default=False,
                            help='Delete all existing objects first')

    def handle(self, *args, **options):
        importer = OuluTwebImporter(options)
        importer.import_data()
