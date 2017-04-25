# -*- coding: utf-8 -*-
import json
import os
import os.path
import tempfile
import zipfile
import dateutil.parser
from django.utils.text import slugify

from decisions.models import (
    Action, Attachment, Case, Content, DataSource, Event, Organization, Function, CaseGeometry
)

from .base import Importer


class PaatosScraperImporter(Importer):
    def __init__(self, identifier, defaults, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_source, created = DataSource.objects.get_or_create(
            identifier=identifier,
            defaults=defaults
        )
        if created:
            self.logger.debug('Created new data source "%s"' % identifier)

    def _import_organization(self, data):
        classification = data['classification'].title()
        org = dict(origin_id=data['sourceId'])
        org['classification'] = classification

        org['name'] = data['name']
        org['slug'] = slugify(org['origin_id'])

        org['founding_date'] = data['founding_date']
        org['dissolution_date'] = data['dissolution_date']

        org['parent'] = data['parent']

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

        return function

    def _import_event(self, data, organization_source_id):
        self.logger.info('Importing event...')

        defaults = dict(
            start_date=dateutil.parser.parse(data['startDate']).date(),
            end_date=dateutil.parser.parse(data['endDate']).date(),
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
            defaults['function'] = Function.objects.get(origin_id=data['functionId'])
        except Function.DoesNotExist:
            defaults['function'] = self._import_function(data['functionId'], data['functionId'])

        case, created = Case.objects.update_or_create(
            data_source=self.data_source,
            origin_id=data['registerId'],
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

            action_title = action_data['title']
            if (len(action_data['title']) > 255):
                action_title = action_title[:255]
                self.logger.warning('Truncated action title %s' % action_data['title'])

            defaults = dict(
                title=action_title,
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
                origin_id=self._create_action_id(action_data, case_source_id),
                defaults=defaults
            )

            if created:
                self.logger.info('Created action %s' % action)

            content_defaults = dict(
                hypertext=action_data['content'],
                type='',
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

    def _import_attachments(self, data, action_source_id):
        self.logger.info('Importing attachments...')

        for attachment_data in data:
            defaults = dict(
                name=attachment_data['name'] or '',
                url=attachment_data['url'],
                number=attachment_data['number'],
                public=attachment_data['public'],
                confidentiality_reason=attachment_data['confidentialityReason'] or '',
            )

            try:
                action = Action.objects.get(origin_id=action_source_id)
                defaults['action'] = action
            except Action.DoesNotExist:
                self.logger.error('Action %s does not exist' % attachment_data['actionId'])
                continue

            attachment, created = Attachment.objects.update_or_create(
                data_source=self.data_source,
                origin_id=attachment_data['sourceId'],
                defaults=defaults
            )

            if created:
                self.logger.info('Created attachment %s' % attachment)

    def _create_action_id(self, action_data, case_source_id):
        return 'action-' + str(action_data['order']) + '-' + case_source_id

    def _handle_organization(self, organization_path):
        if os.path.isfile(organization_path):
            with open(organization_path, 'r') as org_file:
                self._import_organization(json.load(org_file))

    def _handle_organization_events(self, events_path, organization_source_id):
        if os.path.exists(events_path):
            for event_source_id in os.listdir(events_path):
                event_json_path = events_path + '/' + event_source_id + '/index.json'
                if os.path.isfile(event_json_path):
                    with open(event_json_path, 'r') as event_file:
                        self._import_event(json.load(event_file), organization_source_id)
                        case_folder = events_path + '/' + event_source_id + '/cases'
                        self._handle_organization_event_cases(
                            case_folder,
                            organization_source_id,
                            event_source_id)

    def _handle_organization_event_cases(self, case_path, organization_source_id, event_source_id):
        if os.path.exists(case_path):
            for case_folder in os.listdir(case_path):
                case_json_path = case_path + '/' + case_folder + '/index.json'
                action_path = case_path + '/' + case_folder + '/actions.json'
                attachment_path = case_path + '/' + case_folder + '/attachments.json'
                if os.path.isfile(case_json_path):
                    with open(case_json_path, 'r') as case_file:
                        case_data = json.load(case_file)
                        case_source_id = case_data['registerId']
                        if case_source_id:
                            self._import_case(case_data)
                            self._handle_organization_event_case_actions_and_contents(
                                action_path,
                                attachment_path,
                                organization_source_id,
                                case_source_id,
                                event_source_id)

    def _handle_organization_event_case_actions_and_contents(
      self, action_file_path, attachment_file_path,
      organization_source_id, case_source_id, event_source_id):
        if os.path.isfile(action_file_path):
            with open(action_file_path, 'r') as action_file:
                action_data = json.load(action_file)
                action_data_first = next(iter(action_data or []), None)
                self._import_actions_and_contents(action_data, organization_source_id, case_source_id, event_source_id)
                self._handle_attachments(
                    attachment_file_path,
                    self._create_action_id(action_data_first, case_source_id))

    def _handle_attachments(self, attachment_path, action_id):
        if os.path.isfile(attachment_path):
            with open(attachment_path, 'r') as attachment_file:
                self._import_attachments(json.load(attachment_file), action_id)

    def import_data(self):
        self.logger.info('Importing data...')

        if self.options['flush']:
            self.logger.info('Deleting all objects first...')
            Function.objects.all().delete()
            Event.objects.all().delete()
            CaseGeometry.objects.all().delete()
            Action.objects.all().delete()
            Content.objects.all().delete()
            Attachment.objects.all().delete()

        with tempfile.TemporaryDirectory() as temp_dirpath:
            zip_ref = zipfile.ZipFile(self.options['zipfile'], 'r')
            zip_ref.extractall(temp_dirpath)
            zip_ref.close()
            for organization_source_id in os.listdir(temp_dirpath + '/organizations'):
                current_path = temp_dirpath + '/organizations/' + organization_source_id
                self._handle_organization(current_path + '/index.json')
                self._handle_organization_events(current_path + '/events', organization_source_id)

            self.logger.info('Import done!')
