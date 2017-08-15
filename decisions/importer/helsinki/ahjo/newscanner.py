import logging

import pytz
import requests

from .parse_dirlist import parse_dir_listing, parse_file_path

LOG = logging.getLogger(__name__)

BASE_URL = 'http://openhelsinki.hel.fi'
SERVER_TIMEZONE = pytz.timezone('EET')

PATHS_TO_SKIP = []
DOCS_TO_SKIP = []
MIN_FILESIZE = 500


def scan_dir(path, max_depth=0):
    response = requests.get(BASE_URL + path)
    if response.status_code != 200:
        raise IOError("Failed to fetch directory: {}".format(path))

    for dir_entry in parse_dir_listing(response.content):
        print('processing', dir_entry)
        if dir_entry.type == 'dir':
            if dir_entry.href.endswith('.zip/'):
                LOG.debug("Skipping directory ending with .zip: %s",
                          dir_entry.href)
                continue
            if max_depth:
                for info in scan_dir(dir_entry.href, max_depth=(max_depth - 1)):
                    yield info
        elif dir_entry.type == 'file' and dir_entry.href.endswith('.zip'):
            if dir_entry.size < MIN_FILESIZE:
                LOG.warn("File too small: %s %d",
                         dir_entry.href, dir_entry.size)
                continue
            if dir_entry.href in PATHS_TO_SKIP:
                LOG.warn("Skipping document on path skip list: %s",
                         dir_entry.href)
                continue

            info = parse_file_path(dir_entry.href)

            if not info:
                LOG.warn("Skipping invalid filename: %s", dir_entry.href)
                continue

            if not info['language']:
                LOG.warn("Language field missing in %s", path)
                info['language'] = 'Su'

            if info['language'] != 'Su':
                # Skip non-Finnish documents (i.e. Swedish)
                continue

            if info['origin_id'] in DOCS_TO_SKIP:
                LOG.warn("Skipping document on skip list: %s",
                         info['origin_id'])
                continue

            info['last_modified'] = SERVER_TIMEZONE.localize(dir_entry.mtime)
            info['url'] = BASE_URL + dir_entry.href

            yield info
