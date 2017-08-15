import pytz
import re
import logging
import json

from lxml import etree
from datetime import datetime, date

RESOLUTION_MAP = {
    'hyväksytty': 'accepted'
}

LOCAL_TZ = pytz.timezone('Europe/Helsinki')


class ParseError(Exception):
    pass


class AhjoDocument:
    @staticmethod
    def parse_name(name):
        if ', ' in name:
            name = name.split(', ')
            name = '{} {}'.format(name[1], name[0])

        return name

    @staticmethod
    def parse_guid(raw):
        guid_match = re.fullmatch(r'\{([A-F0-9]{8}-(?:[A-F0-9]{4}-){3}[A-F0-9]{12})\}', raw)
        if guid_match is not None:
            return guid_match.group(1).lower()
        else:
            raise ParseError("Invalid GUID format")

    @staticmethod
    def parse_datetime(raw):
        date = None

        # it's important here that the 12h versions are before 24h versions
        formats = [
            '%m/%d/%Y %I:%M:%S %p',
            '%m/%d/%Y %H:%M:%S',

            '%d.%m.%Y %I:%M:%S %p',
            '%d.%m.%Y %H:%M:%S',
        ]

        for fmt in formats:
            try:
                date = datetime.strptime(raw, fmt)
                break
            except ValueError as r:
                pass

        if date is None:
            raise ParseError('Unknown timestamp')

        return LOCAL_TZ.localize(date)

    def log(self, severity, msg):
        human_readable = '{} (File: {}, Action: {})'.format(msg, self.filename, self.current_action)
        self.logger.log(severity, human_readable)

        attrs = ['current_document', 'current_action']

        state = {attr: getattr(self, attr) for attr in attrs}
        state['filename'] = self.filename

        self.errors.append({
            'msg': msg,
            'severity': severity,
            'state': state
        })

        if severity >= self.except_treshold:
            raise ParseError(msg)

    def critical(self, msg):
        self.log(logging.CRITICAL, msg)

    def error(self, msg):
        self.log(logging.ERROR, msg)

    def warning(self, msg):
        self.log(logging.WARNING, msg)

    def info(self, msg):
        self.log(logging.INFO, msg)

    def debug(self, msg):
        self.log(logging.DEBUG, msg)

    def import_attendees(self, lasnaolotiedot):
        ret = []

        attendee_group_els = lasnaolotiedot.findall('.//Osallistujaryhma')

        for attendee_group_el in attendee_group_els:
            title_el = attendee_group_el.find('OsallistujaryhmaOtsikko')
            attendees = attendee_group_el.findall('Osallistujat')
            attendee_group = {'members': []}
            if title_el is not None:
                attendee_group['title'] = title_el.text
            for attendee in attendees:
                a_attrs = {}

                name = attendee.find('Nimi')
                if name is not None:
                    a_attrs['name'] = AhjoDocument.parse_name(name.text)
                else:
                    self.warning("Attendee doesn't have a name")
                    continue

                opts = attendee.find('OsallistujaOptiot')
                if opts is not None:
                    role = opts.find('Rooli')
                    if role is not None:
                        a_attrs['role'] = role.text

                title = attendee.find('Titteli')
                if title is not None:
                    a_attrs['title'] = title.text

                attendee_group['members'].append(a_attrs)

            ret.append(attendee_group)

        return ret

    def import_event(self, event_data):
        attrs = {}

        date_el = event_data.find('Paivays')
        date = datetime.strptime(date_el.text, '%Y-%m-%d')
        attrs['start_date'] = date
        attrs['end_date'] = date

        return attrs

    def import_content(self, content):
        chapters = content.findall('.//Kappale')
        if chapters is not None:
            text = ''
            for chapter in chapters:
                chapter_text = chapter.find('KappaleTeksti')
                if chapter_text is not None:
                    text += '<p>{}</p>\n'.format(chapter_text.text)
        else:
            self.error("Content doesn't have chapters")

        attrs = {
            'hypertext': text
        }

        return attrs

    def import_action(self, action):
        attrs = {}

        metadata = action.find('KuvailutiedotOpenDocument')

        title_el = metadata.find('Otsikko')
        attrs['title'] = title_el.text

        self.current_action = title_el.text

        action_class_el = metadata.find('AsiakirjallinenTieto')
        if action_class_el is not None:
            attrs['action_class'] = action_class_el.text.split(' ')
        else:
            self.warning("Action doesn't have a class")

        case_guid_el = metadata.find('AsiaGuid')
        if case_guid_el is not None:
            attrs['case_guid'] = AhjoDocument.parse_guid(case_guid_el.text)
        else:
            if 'action_class' in attrs and attrs['action_class'][-1].lower() != 'vakiopäätös':
                self.error("Action doesn't have an associated case")

        date_el = metadata.find('Paatospaiva')
        if date_el is not None:
            attrs['date'] = AhjoDocument.parse_datetime(date_el.text)
        else:
            self.error("Action doesn't have a date")

        article_number_el = metadata.find('Pykala')
        if article_number_el is not None:
            attrs['article_number'] = int(article_number_el.text)
        else:
            self.warning("Action doesn't have an ordering number")

        resolution_el = metadata.find('Asiakirjantila')

        if resolution_el is not None:
            try:
                attrs['resolution'] = RESOLUTION_MAP[resolution_el.text.lower()]
            except KeyError:
                self.warning("Unknown resolution type: {}".format(resolution_el.text))
        else:
            self.warning("Action doesn't have a resolution")

        content = action.find('SisaltoSektioToisto')
        attrs['content'] = [self.import_content(cs) for cs in content]

        return attrs

    def import_document(self, root):
        attrs = {}

        actions = root.find('Paatokset')
        metadata = root.find('Kuvailutiedot')

        guid_el = metadata.find('DhId')
        attrs['guid'] = AhjoDocument.parse_guid(guid_el.text)
        self.current_document = attrs['guid']

        event_data = root.find('YlatunnisteSektio')
        event_metadata = root.find('PkKansilehtiSektio')

        if event_data is not None:
            attrs['event'] = self.import_event(event_data)
            if event_metadata is not None:
                lasnaolotiedot = event_metadata.find('KansilehtiToisto/Lasnaolotiedot')
                attrs['event']['attendees'] = self.import_attendees(lasnaolotiedot)
        else:
            self.critical("No event data")

        attrs['event']['actions'] = [self.import_action(ac) for ac in actions]

        #signatures = root.find('SahkoinenAllekirjoitusSektio')
        #chairman = signatures.find('PuheenjohtajaSektio').find('PuheenjohtajaToisto')
        #attrs['chairman'] = chairman.find('Puheenjohtajanimi').text

        return attrs

    def import_esityslista(self, root):
        pass
        # attrs = {}

        # actions = root.find('KasiteltavatAsiat')

    def __init__(self, filename, except_treshold=logging.CRITICAL):
        self.logger = logging.getLogger(__name__)
        self.errors = []

        self.filename = filename
        self.except_treshold = except_treshold

        self.current_document = None
        self.current_action = None

        with open(filename, encoding='utf-8') as f:
            xml = f.read()
            root = etree.fromstring(xml)

            if root.tag == 'Poytakirja':
                self.document = self.import_document(root)

            if root.tag == 'Esityslista':
                self.document = self.import_esityslista(root)

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
