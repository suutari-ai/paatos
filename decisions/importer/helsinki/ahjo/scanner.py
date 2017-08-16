import logging

import pytz
import requests
from django.utils.functional import cached_property

from ._scanner_consts import DOCS_TO_SKIP, PATHS_TO_SKIP
from .parse_dirlist import parse_dir_listing, parse_file_path

LOG = logging.getLogger(__name__)

BASE_URL = 'http://openhelsinki.hel.fi'
SERVER_TIMEZONE = pytz.timezone('EET')


class ChangeScanResult(object):
    def __init__(self, changed, deleted, state):
        """
        Initialize result of a change scanning.

        :type changed: Iterable[DocumentInfo]
        :type deleted: Iterable[str]
        :type state: dict
        """
        self.changed = changed
        self.deleted = deleted
        self.state = state


def scan_for_changes(last_state=None, root='/files'):
    """
    Scan for changes on the server.

    Will create a list of changed and deleted files compared to given
    last state.  The list of changed files will include also all new
    files.  If no last state is given, will compare against empty state,
    i.e. all files are considered new.

    :type last_state: dict|None
    :param last_state: State from the last scan to compare against
    :rtype: ChangeScanResult
    :return: Changed and deleted files and updated state for next scan
    """
    if last_state is None:
        last_state = {}

    new_state = dict(last_state)
    doc_infos = scan_dir(root, max_depth=9999)
    changed = []
    deleted = set(last_state)
    for doc_info in doc_infos:
        deleted.discard(doc_info.path)
        if last_state.get(doc_info.path) != doc_info.mtime_text:
            new_state[doc_info.path] = doc_info.mtime_text
            changed.append(doc_info)

    for path in deleted:
        new_state.pop(path, None)

    return ChangeScanResult(changed, deleted, new_state)


class _DocumentInfoDataProperty(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance._data[self.name]


class DocumentInfo(object):
    def __init__(self, base_url, dir_entry):
        """
        Initialize document info from directory entry.

        :type dir_entry: .parse_dirlist.DirEntry
        """
        self.base_url = base_url
        self.dir_entry = dir_entry
        self.path = dir_entry.href
        self.url = base_url + self.path
        self._data = self._parse_path(self.path)

    def _parse_path(self, path):
        data = parse_file_path(path)
        if not data:
            raise ValueError("Invalid filename: {}".format(path))
        if not data.get('language'):
            LOG.debug("Language field missing in %s", path)
            data['language'] = 'Su'
        return data

    def __repr__(self):
        return '<DocumentInfo: {}>'.format(self.path)

    org = _DocumentInfoDataProperty('org')
    date = _DocumentInfoDataProperty('date')
    policymaker = _DocumentInfoDataProperty('policymaker')
    meeting_nr = _DocumentInfoDataProperty('meeting_nr')
    doc_type_id = _DocumentInfoDataProperty('doc_type_id')
    language = _DocumentInfoDataProperty('language')
    year = _DocumentInfoDataProperty('year')
    policymaker_id = _DocumentInfoDataProperty('policymaker_id')
    policymaker_abbr = _DocumentInfoDataProperty('policymaker_abbr')
    doc_type = _DocumentInfoDataProperty('doc_type')
    origin_id = _DocumentInfoDataProperty('origin_id')

    @cached_property
    def last_modified(self):
        return SERVER_TIMEZONE.localize(self.dir_entry.mtime)

    @property
    def mtime_text(self):
        return self.dir_entry.mtime_text


def scan_dir(path, max_depth=0):
    return Scanner().scan_dir(path, max_depth)


class Scanner(object):
    def __init__(self, base_url=BASE_URL, min_filesize=500,
                 docs_to_skip=DOCS_TO_SKIP, paths_to_skip=PATHS_TO_SKIP):
        self.base_url = base_url
        self.min_filesize = min_filesize
        self.docs_to_skip = docs_to_skip
        self.paths_to_skip = paths_to_skip

    def scan_dir(self, path, max_depth=0):
        dir_listing = self.get_contents(path)
        for dir_entry in parse_dir_listing(dir_listing):
            if self._should_skip_dir_entry(dir_entry):
                continue

            if dir_entry.type == 'dir':
                if max_depth > 0:  # Recurse to the subdirectory
                    path = dir_entry.href
                    for doc_info in self.scan_dir(path, max_depth - 1):
                        yield doc_info
            else:
                try:
                    doc_info = DocumentInfo(self.base_url, dir_entry)
                except ValueError:
                    LOG.debug("Skipping invalid filename: %s", dir_entry.href)
                    continue

                if self._should_skip_document(doc_info):
                    continue

                yield doc_info

    def get_contents(self, path):
        response = requests.get(self.base_url + path)
        if response.status_code != 200:
            raise IOError("Failed to fetch: {}".format(self.base_url + path))
        return response.content

    def _should_skip_dir_entry(self, dir_entry):
        if dir_entry.type == 'dir' and dir_entry.href.endswith('.zip/'):
            LOG.debug("Skipping directory ending with .zip: %s", dir_entry.href)
            return True
        elif dir_entry.type == 'dir':
            return False  # Other directories should be processed
        elif not dir_entry.href.endswith('.zip'):
            return True  # Skip non-zip files
        elif dir_entry.size < self.min_filesize:
            LOG.warn("File too small: %s %d", dir_entry.href, dir_entry.size)
            return True
        elif dir_entry.href in self.paths_to_skip:
            reason = self.paths_to_skip[dir_entry.href]
            LOG.info("Skipping document (%s): %s", reason, dir_entry.href)
            return True
        return False

    def _should_skip_document(self, doc_info):
        if doc_info.language != 'Su':
            # Skip non-Finnish documents (i.e. Swedish)
            return True
        if doc_info.origin_id in self.docs_to_skip:
            reason = self.docs_to_skip[doc_info.origin_id] or 'unknown reason'
            LOG.info("Skipping document (%s): %s", reason, doc_info.origin_id)
            return True
        return False
