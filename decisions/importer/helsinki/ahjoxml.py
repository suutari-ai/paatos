import pytz
import re
import logging
import json

from lxml import etree
from datetime import datetime, date

RESOLUTION_MAP = {
    'hyväksytty': 'accepted'
}

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10


class ParseError(Exception):
    pass


class AhjoDocument:
    @staticmethod
    def parse_guid(raw):
        guid_match = re.fullmatch(r'\{([A-F0-9]{8}-(?:[A-F0-9]{4}-){3}[A-F0-9]{12})\}', raw)
        if guid_match is not None:
            return guid_match.group(1).lower()
        else:
            raise ParseError()

    @staticmethod
    def parse_datetime(raw):
        t = {}
        raw = raw.split(' ')
        date = raw.pop(0)
        time = raw.pop(0)

        separator = None
        separators = '-./'
        for sep in separators:
            if sep in date:
                separator = sep

        date = date.split(separator)
        if len(str(date[0])) == 4:
            t['year'] = date[0]
            t['month'] = date[1]
            t['day'] = date[2]
        elif len(str(date[2])) == 4:
            t['year'] = date[2]
            t['month'] = date[1]
            t['day'] = date[0]

        if ':' in time:
            time = time.split(':')
            t['hour'] = time[0]
            t['minute'] = time[1]
            t['second'] = time[2]

        for key in t:
            t[key] = int(t[key])

        if False in [key in t for key in ['year', 'month', 'day', 'minute', 'hour', 'second']]:
            raise ParseError()

        if len(raw) > 0:
            # just why would anyone store times in the 12-hour format
            ampm = raw.pop(0)
            if 'pm' in ampm.lower() and t['hour'] != 12:
                t['hour'] += 12
            elif 'am' in ampm.lower() and t['hour'] == 12:
                t['hour'] = 0

        date = datetime(**t)
        tz = pytz.timezone('Europe/Helsinki')
        date = tz.localize(date)

    def log(self, severity, msg):
        human_readable = '{} (File: {}, Action: {})'.format(msg, self.document_guid, self.action_guid)
        self.logger.log(severity, human_readable)

        attrs = ['document_guid', 'action_guid']
        self.errors.append({
            'msg': msg,
            'severity': severity,
            'state': {
                attr: getattr(self, attr) for attr in attrs
            }
        })

        if severity >= self.except_treshold:
            raise ParseError()

    def import_event(self, event_data, metadata):
        attrs = {}

        date_el = event_data.find('Paivays')
        if date_el is not None:
            try:
                date = datetime.strptime(date_el.text, '%Y-%m-%d')
                attrs['start_date'] = date
                attrs['end_date'] = date
            except:
                self.log(WARNING, "Unrecognized timestamp {}".format(date_el.text))
        else:
            self.log(ERROR, "Event doesn't have a timestamp")

        return attrs

    def import_content(self, content):
        assert content.tag == 'SisaltoSektio'

        chapters = content.findall('.//Kappale')
        if chapters is not None:
            text = ''
            for chapter in chapters:
                text += '<p>{}</p>\n'.format(chapter.find('KappaleTeksti').text)
        else:
            self.log(ERROR, "Content doesn't have chapters")

        attrs = {
            'hypertext': text
        }

        return attrs

    def import_action(self, action):
        attrs = {}

        metadata = action.find('KuvailutiedotOpenDocument')
        if not metadata:
            self.log(CRITICAL, "Action doesn't have KuvailutiedotOpenDocument section")

        case_guid_el = metadata.find('AsiaGuid')
        if case_guid_el is not None:
            try:
                attrs['case_guid'] = AhjoDocument.parse_guid(case_guid_el.text)
            except ParseError:
                self.log(ERROR, "Invalid case guid {}".format(case_guid_el.text))
        else:
            self.log(ERROR, "Action doesn't have an associated case")

        title_el = metadata.find('Otsikko')
        if title_el is not None:
            attrs['title'] = title_el.text
        else:
            self.log(ERROR, "Action doesn't have a title")

        date_el = metadata.find('Paatospaiva')
        if date_el is not None:
            try:
                attrs['date'] = AhjoDocument.parse_datetime(date_el.text)
            except ParseError:
                self.log(WARNING, "Couldn't read timestamp {}".format(date_el.text))
        else:
            self.log(WARNING, "Action doesn't have a datetime")

        article_number_el = metadata.find('Pykala')
        if article_number_el is not None:
            attrs['article_number'] = int(article_number_el.text)
        else:
            self.log(WARNING, "Action doesn't have an article number")

        resolution = metadata.find('Asiakirjantila')
        try:
            attrs['resolution'] = RESOLUTION_MAP[resolution.text.lower()]
        except KeyError:
            self.log(WARNING, 'Unknown resolution type: {}'.format(resolution.text))

        content = action.find('SisaltoSektioToisto')
        if not content:
            self.log(CRITICAL, "Action doesn't have SisaltoSektioToisto section")

        content = [self.import_content(cs) for cs in content]
        if content:
            attrs['content'] = content
        else:
            self.log(ERROR, "Action doesn't have any content")

        return attrs

    def import_document(self, root):
        attrs = {}

        actions = root.find('Paatokset')
        if actions is None:
            self.log(CRITICAL, "Couldn't find Paatokset section")

        metadata = root.find('Kuvailutiedot')
        if metadata is None:
            self.log(CRITICAL, "Couldn't find Kuvailutiedot section")

        event_data = root.find('YlatunnisteSektio')
        if event_data is None:
            self.log(CRITICAL, "Couldn't find YlatunnisteSektio")

        event_metadata = root.find('PkKansilehtiSektio')
        if event_metadata is None:
            self.log(CRITICAL, "Couldn't find PkKansilehtiSektio")

        guid_el = metadata.find('DhId')
        if guid_el is not None:
            attrs['guid'] = AhjoDocument.parse_guid(guid_el.text)
            self.document_guid = attrs['guid']
        else:
            self.log(CRITICAL, "Document doesn't have a GUID")

        attrs['event'] = self.import_event(event_data, event_metadata)
        attrs['event']['actions'] = [self.import_action(ac) for ac in actions]

        return attrs

    def __init__(self, filename, except_treshold=CRITICAL):
        self.logger = logging.getLogger(__name__)
        self.errors = []
        self.except_treshold = except_treshold

        self.document_guid = None
        self.action_guid = None

        with open(filename, encoding='utf-8') as f:
            xml = f.read()
            root = etree.fromstring(xml)

            if root.tag == 'Poytakirja':
                self.document = self.import_document(root)

    @property
    def json(self):
        # https://stackoverflow.com/a/22238613

        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""

            if isinstance(obj, (datetime, date)):
                serial = obj.isoformat()
                return serial
            raise TypeError("Type %s not serializable" % type(obj))

        ret = {
            'document': self.document,
            'errors': self.errors
        }

        return json.dumps(ret, indent=4, ensure_ascii=False, default=json_serial)
