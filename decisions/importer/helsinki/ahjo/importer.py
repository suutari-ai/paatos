from .scanner import scan_dir


class Importer(object):
    def import_changes(self, root='/files'):
        """
        Detect changes on the server and import them.

        :type root: str
        :param root: The root directory of the files to import
        """
        doc_infos = scan_dir(root, max_depth=9999)
        for doc_info in doc_infos:
            old_mtime = self.get_file_mtime(doc_info.path)
            new_mtime = doc_info.mtime_text
            if not old_mtime:
                self.handle_document_added(doc_info)
                self.set_file_mtime(doc_info.path, new_mtime)
            elif old_mtime != new_mtime:
                self.handle_document_changed(doc_info)
                self.set_file_mtime(doc_info.path, new_mtime)

    def get_file_mtime(self, path):
        return None

    def set_file_mtime(self, path, mtime):
        pass

    def handle_document_added(self, doc_info):
        self.handle_document_changed(doc_info)

    def handle_document_changed(self, doc_info):
        pass
