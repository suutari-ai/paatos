from ....models import ImportedFile
from .importer import Importer


class DatabaseImporter(Importer):
    """
    Importer that imports from Ahjo to the database.
    """
    def __init__(self, data_source):
        self.data_source = data_source

    def get_file_mtime(self, path):
        imported_file = ImportedFile.objects.filter(
            data_source=self.data_source, path=path).first()
        return imported_file.last_import_mtime if imported_file else None

    def set_file_mtime(self, path, mtime):
        (imported_file, created) = ImportedFile.objects.get_or_create(
            data_source=self.data_source, path=path, defaults={
                'last_import_mtime': mtime})
        if not created:
            imported_file.last_import_mtime = mtime
            imported_file.save(update_fields=['last_import_mtime'])

    def handle_document_changed(self, doc_info):
        print("Updating data from {}".format(doc_info))
        data = doc_info.get_document().document
