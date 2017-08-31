import logging

from django.db import transaction

from ....models import DataSource, ImportedFile
from .importer import ChangeImporter

LOG = logging.getLogger(__name__)


class DatabaseImporter(ChangeImporter):
    """
    Importer that imports from Ahjo to the database.
    """
    def __init__(self, data_source=None):
        if data_source is None:
            (data_source, _created) = DataSource.objects.get_or_create(
                identifier='ahjo_xml', defaults={'name': 'Ahjo XML'})
        self.data_source = data_source

    def should_import(self, doc_info):
        # Currently only "minutes" are imported, "agenda" is not.
        should_import = (doc_info.doc_type == 'minutes')
        if not should_import:
            LOG.info("Skipping %s: %s", doc_info.doc_type, doc_info.origin_id)
        return should_import

    def _import_single(self, doc_info):
        with transaction.atomic():
            super(DatabaseImporter, self)._import_single(doc_info)

    def get_imported_version(self, doc_info):
        imported_file = ImportedFile.objects.filter(
            data_source=self.data_source, path=doc_info.path).first()
        return imported_file.imported_version if imported_file else None

    def set_imported_version(self, doc_info, version):
        ImportedFile.objects.update_or_create(
            data_source=self.data_source, path=doc_info.path, defaults={
                'imported_version': version})

    def handle_document_changed(self, doc_info):
        """
        Handle document change or a new document.

        Import or update the data from the document to the database.

        :type doc_info: .docinfo.DocumentInfo
        """
        LOG.info("Updating data from %s", doc_info.origin_id)
        doc = doc_info.get_document()
