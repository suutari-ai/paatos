# -*- coding: utf-8 -*-
import json
import os
import os.path
import dateutil.parser
from django.utils.text import slugify

from decisions.models import (
    Action, Attachment, Case, Content, DataSource, Event, Organization, Function, CaseGeometry
)

from .base import Importer

TYPE_MAP = {
    'Valtuusto': 'council',
    'Hallitus': 'board',
    'Jaosto': 'board_division',
    'Lautakunta': 'committee',
    'Toimiala': 'field',
    'Virasto': 'department',
    'Osasto': 'division',
    'Esittelijä': 'introducer',
    'Esittelijä (toimiala)': 'introducer_field',
    'Viranhaltija': 'office_holder',
    'Kaupunki': 'city',
    'Yksikkö': 'unit',
    'Toimikunta': 'working_group',
}

class OuluTwebImporter(Importer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source, created = DataSource.objects.get_or_create(
            identifier='oulu_tweb',
            defaults={'name': 'Oulu Tweb'}
        )
        if created:
            self.logger.debug('Created new data source "oulu_tweb"')
        self.meeting_to_org = None

    def _import_organization(self, data):
        classification = data['classification'].title()
        if classification not in TYPE_MAP:
            return
        org = dict(origin_id=data['sourceId'])
        org['classification'] = classification
        org_type = TYPE_MAP[classification]

        org['name'] = data['name']
        org['slug'] = slugify(org['origin_id'])

        org['founding_date'] = None
        org['dissolution_date'] = None
        
        #TODO: use mapping file to find parent
        org['parent'] = None

        self.save_organization(org)

    def _import_function(self, name, source_id):
        self.logger.info('Importing functions...')

        defaults = dict(
            name=name,
            function_id=source_id
        )

        function, created = Function.objects.update_or_create(
            origin_id=source_id,
            data_source=self.data_source,
            defaults=defaults
        )

        if created:
            self.logger.info('Created function %s' % function)

    def _import_event(self, data, organization_source_id):
        self.logger.info('Importing event...')

        defaults = dict(
            start_date= dateutil.parser.parse(data['startDate']).date(),
            end_date= dateutil.parser.parse(data['endDate']).date(),
            name=data['name']
        )

        try:
            organization = Organization.objects.get(origin_id=organization_source_id)
            defaults['organization'] = organization
        except Organization.DoesNotExist:
            self.logger.error('Organization %s does not exist' % organization_source_id)
            return

        event, created = Event.objects.update_or_create(
            data_source=self.data_source,
            origin_id=data['sourceId'],
            defaults=defaults
        )

        if created:
            self.logger.info('Created event %s' % event)

    def _import_case(self, data):
        self.logger.info('Importing case...')

        defaults = dict(
            title=data['title'],
            register_id=data['registerId'],
        )

        try:
          defaults['function'] = Function.objects.get(origin_id='oulu-tweb')
        except Function.DoesNotExist:
          self.logger.error('Function does not exist')
          return

        case, created = Case.objects.update_or_create(
            data_source=self.data_source,
            origin_id=data['sourceId'],
            defaults=defaults,
        )

        if created:
            self.logger.info('Created case %s' % case)


    def _import_actions_and_contents(self, data, organization_source_id, case_source_id, event_source_id):
        self.logger.info('Importing actions...')

        for action_data in data:
            org = Organization.objects.get(origin_id=organization_source_id)
            if not org:
                self.logger.error('Organization %s does not exist' % organization_source_id)
                return

            defaults = dict(
                title=action_data['title'],
                ordering=action_data['order']
            )
            try:
                case = Case.objects.get(origin_id=case_source_id)
                defaults['case'] = case
            except Case.DoesNotExist:
                self.logger.error('Case %s does not exist' % case_source_id)
                continue
            try:
                event = Event.objects.get(origin_id=event_source_id)
                defaults['event'] = event
            except Event.DoesNotExist:
                self.logger.error('Event %s does not exist' % event_source_id)
                continue

            action, created = Action.objects.update_or_create(
                data_source=self.data_source,
                origin_id='action-' + str(action_data['order']) + '-' + case_source_id,
                defaults=defaults
            )

            if created:
                self.logger.info('Created action %s' % action)
            
            content_defaults = dict(
                hypertext=action_data['content'],
                type= '',
                ordering=action_data['order'],
                action=action
            )
            
            content, created = Content.objects.update_or_create(
                data_source=self.data_source,
                origin_id='content-' + str(action_data['order']) + '-' + case_source_id,
                defaults=content_defaults
            )

            if created:
                self.logger.info('Created content %s' % content)

    def _import_contents(self, data):
        self.logger.info('Importing contents...')

        for content_section_data in data['content_sections']:
            defaults = dict(
                hypertext=content_section_data['text'],
                type=content_section_data['type'],
                ordering=content_section_data['index'],
            )

            action_id = content_section_data.get('agenda_item')
            try:
                action = Action.objects.get(origin_id=action_id)
                defaults['action'] = action
            except Action.DoesNotExist:
                self.logger.error('Action %s does not exist' % action_id)
                continue

            content, created = Content.objects.update_or_create(
                data_source=self.data_source,
                origin_id=content_section_data['id'],
                defaults=defaults
            )

            if created:
                self.logger.info('Created content %s' % content)

    def _import_attachments(self, data):
        self.logger.info('Importing attachments...')

        for attachment_data in data:
            defaults = dict(
                name=attachment_data['name'] or '',
                url=attachment_data['url'],
                number=attachment_data['number'],
                public=attachment_data['public'],
                confidentiality_reason=None,
            )

            try:
                action = Action.objects.get(origin_id=attachment_data['actionId'])
                defaults['action'] = action
            except Action.DoesNotExist:
                self.logger.error('Action %s does not exist' % attachment_data['actionId'])
                continue

            attachment, created = Attachment.objects.update_or_create(
                data_source=self.data_source,
                origin_id=attachment_data['id'],
                defaults=defaults
            )

            if created:
                self.logger.info('Created attachment %s' % attachment)

    def import_data(self):
        self.logger.info('Importing oulu tweb data...')

        if self.options['flush']:
            self.logger.info('Deleting all objects first...')
            Function.objects.all().delete()
            Event.objects.all().delete()
            CaseGeometry.objects.all().delete()
            Action.objects.all().delete()
            Content.objects.all().delete()
            Attachment.objects.all().delete()

        self._import_function('oulu-tweb', 'oulu-tweb')
        
        for organization_source_id in os.listdir(self.options['filepath'] + '/organizations'):
            current_path = self.options['filepath'] + '/organizations/' + organization_source_id
            if os.path.isfile(current_path + '/index.json'):
                with open(current_path + '/index.json', 'r') as org_file: 
                    self._import_organization(json.load(org_file))
                if os.path.exists(current_path + '/events'):
                    for event_source_id in os.listdir(current_path + '/events'):
                        if os.path.isfile(current_path + '/events/' + event_source_id + '/index.json'):
                            with open(current_path + '/events/' + event_source_id + '/index.json', 'r') as event_file: 
                                self._import_event(json.load(event_file), organization_source_id)
                            if os.path.exists(current_path + '/events/' + event_source_id + '/cases'):
                                for case_source_id in os.listdir(current_path + '/events/' + event_source_id + '/cases'):
                                    case_path = current_path + '/events/' + event_source_id + '/cases/' + case_source_id + '/index.json'
                                    action_path = current_path + '/events/' + event_source_id + '/cases/' + case_source_id + '/actions.json'
                                    attachment_path = current_path + '/events/' + event_source_id + '/cases/' + case_source_id + '/attachments.json'
                                    if os.path.isfile(case_path):
                                        with open(case_path, 'r') as case_file: 
                                            self._import_case(json.load(case_file))
                                    if os.path.isfile(action_path):
                                        with open(action_path, 'r') as action_file:
                                            self._import_actions_and_contents(json.load(action_file), organization_source_id, case_source_id, event_source_id)
                                    if os.path.isfile(attachment_path):
                                        with open(attachment_path, 'r') as attachment_file:
                                            self._import_attachments(json.load(attachment_file));

        self.logger.info('Import done!')
