import re
import zipfile

from .document import AhjoDocument
from .http_file import HttpFetchedFile
from .scanner import scan_for_changes


class AhjoXml(object):
    def __init__(self, last_state=None):
        self.last_state = last_state or {}

    def get_all_documents(self):
        return self.get_changed_documents({})

    def get_changed_documents(self, last_state=None):
        if last_state is None:
            last_state = self.last_state
        result = scan_for_changes(last_state)
        self.last_state = result.state
        return result.changed

    def get_document(self, doc_or_url):
        xml_file = self.open_xml_file_of(doc_or_url)
        return AhjoDocument(xml_file)

    def open_xml_file_of(self, doc_or_url):
        url = getattr(doc_or_url, 'url', doc_or_url)
        remote_file = HttpFetchedFile(url)
        zipf = zipfile.ZipFile(remote_file)
        name_list = zipf.namelist()
        xml_names = [x for x in name_list if x.endswith('.xml')]
        if len(xml_names) == 0:
            # FIXME: Workaround for a silly bug
            xml_names = [x for x in name_list if re.match(r'\w+\d+xml_', x)]
            if len(xml_names) != 1:
                raise IOError("No XML file in ZIP: {}".format(url))
        if len(xml_names) > 1:
            raise IOError("Too many XML files in ZIP: {}".format(url))
        return zipf.open(xml_names[0])
