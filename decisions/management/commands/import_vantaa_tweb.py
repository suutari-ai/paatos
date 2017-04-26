from django.core.management.base import BaseCommand

from decisions.importer.paatos_scraper import PaatosScraperImporter


class Command(BaseCommand):
    help = 'Imports Vantaa Tweb data'

    def add_arguments(self, parser):
        parser.add_argument('zipfile', type=str)
        parser.add_argument('--flush', action='store_true', dest='flush', default=False,
                            help='Delete all existing objects first')

    def handle(self, *args, **options):
        defaults = dict(
            name='Vantaa Tweb'
        )
        importer = PaatosScraperImporter('vantaa_tweb', defaults, options)
        importer.import_data()
