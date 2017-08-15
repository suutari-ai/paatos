import re
from collections import namedtuple

import dateutil.parser
import lxml.html

DIRLIST_LINE_RX = re.compile(
    r'\s*'
    r'(?P<datetime>( ?\d|\d\d)/( ?\d|\d\d)/\d{4} ( ?\d|\d\d):\d\d (AM|PM))'
    r'\s+'
    r'(?P<size_or_dir>\d+|<dir>)'
    r'\s*')

DirEntry = namedtuple('DirEntry', ('href', 'mtime', 'size', 'type'))


def parse_dir_listing(content):
    """
    Parse Ahjo XML directory listing HTML to dir entries.

    :type content: bytes
    :param content: HTML formatted directory listing
    :rtype: Iterable[DirEntry]
    :return: Parsed data as DirEntry objects
    """
    root = lxml.html.fromstring(content)
    link_elems = root.xpath('//a')
    for link_elem in link_elems:
        if link_elem.text == '[To Parent Directory]':
            continue
        href = link_elem.get('href')
        prev = link_elem.getprevious()
        preceeding_text = (prev.tail if prev is not None else '')
        m = DIRLIST_LINE_RX.match(preceeding_text)
        if not m:
            raise ValueError(
                "Cannot parse preceeding text: {!r}".format(preceeding_text))
        mtime = dateutil.parser.parse(m.group('datetime'))
        size_or_dir = m.group('size_or_dir')
        if size_or_dir == '<dir>':
            size = None
            ftype = 'dir'
        else:
            size = int(size_or_dir)
            ftype = 'file'
        yield DirEntry(href=href, mtime=mtime, size=size, type=ftype)


FILENAME_RX = re.compile(
    r'(?P<org>.+)'
    r'%20(?P<date>\d{4}-\d\d-\d\d)'
    r'%20(?P<policymaker>.+)'
    r'%20(?P<meeting_nr>\d+)'
    r'%20(?P<doc_type_id>.+)'
    r'%20?(?P<language>[^.].+)?'
    r'\.zip$')

DOC_TYPES = {'Pk': 'minutes', 'El': 'agenda'}


def parse_file_path(path):
    (filepath, filename) = path.rsplit('/', 1)
    dirname = filepath.rsplit('/', 1)[-1]

    filename_match = FILENAME_RX.match(filename)

    if not filename_match:
        return None

    info = filename_match.groupdict()

    info['meeting_nr'] = int(info['meeting_nr'])
    info['year'] = int(info['date'].split('-')[0])
    policymaker_id = dirname.rsplit('_', 1)[-1].strip()
    info['policymaker_id'] = policymaker_id
    info['policymaker_abbr'] = info['policymaker']
    info['doc_type'] = DOC_TYPES[info['doc_type_id']]
    info['origin_id'] = (
        '{org}_{policymaker}_{year}-{meeting_nr}_{doc_type_id}'.format(**info))

    return info
