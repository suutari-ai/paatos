# -*- coding: utf-8 -*-
import logging

from decisions.models import Membership, Organization, Person, Post


class Importer(object):
    def __init__(self, options):
        super(Importer, self).__init__()
        self.options = options
        self.verbosity = options['verbosity']
        self.logger = logging.getLogger(__name__)

        self.setup()

    def setup(self):
        pass

    def _get_or_create_person(self, info):
        person, created = Person.objects.get_or_create(
            data_source=self.data_source,
            origin_id=info['origin_id'],
            defaults=info
        )
        if created:
            self.logger.info('Created person {}'.format(person))

        return person

    def _save_membership(self, info, organization):
        person_info = info.pop('person')
        person = self._get_or_create_person(person_info)

        membership = Membership.objects.create(
            data_source=self.data_source,
            person=person,
            organization=organization,
            role=info['role'],
            start_date=info['start_date'],
            end_date=info['end_date'],
        )
        self.logger.info('Created membership {}'.format(membership))

        return membership

    def save_organization(self, info):
        membership_infos = info.pop('memberships', [])

        defaults = {
            'name': info['name'],
            'founding_date': info['founding_date'],
            'classification': info['classification'],
            'dissolution_date': info['dissolution_date'],
        }

        parent = info['parent']
        if parent:
            try:
                defaults['parent'] = Organization.objects.get(origin_id=parent)
            except Organization.DoesNotExist:
                self.logger.error('Cannot set parent for org %s, org with origin_id %s does not exist'
                                  % (info['name'], parent))

        organization, created = Organization.objects.update_or_create(
            data_source=self.data_source,
            origin_id=info['origin_id'],
            defaults=defaults,
        )
        verb = 'Created' if created else 'Updated'
        self.logger.info('{} organization {}'.format(verb, organization))

        organization.memberships.all().delete()
        for membership_info in membership_infos:
            self._save_membership(membership_info, organization)

        return organization

    def save_post(self, info):
        defaults = {
            'label': info['name'],
            'start_date': info['founding_date'],
            'end_date': info['dissolution_date'],
        }

        organization_id = info['parent']
        if not organization_id:
            self.logger.error('Cannot create post %s, it does not seem to have a parent organization' % info['name'])
            return

        try:
            defaults['organization'] = Organization.objects.get(origin_id=organization_id)
        except Organization.DoesNotExist:
            self.logger.error('Cannot set org for %s, org with origin_id %s does not exist' %
                              (info['name'], organization_id))

        post, created = Post.objects.update_or_create(
            data_source=self.data_source,
            origin_id=info['origin_id'],
            defaults=defaults,
        )
        verb = 'Created' if created else 'Updated'
        self.logger.info('{} post {}'.format(verb, post))
