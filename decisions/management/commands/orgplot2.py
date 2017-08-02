from django.core.management.base import BaseCommand

from decisions.models.organization import Organization


class Command(BaseCommand):
    def print_nested(self, org, level):
        print('    ' * level + org.name)
        for child in org.organization_set.all():
            self.print_nested(child, level + 1)
        for post in org.posts.all():
            print('    ' * (level + 1) + post.label)

    def handle(self, *args, **opts):
        orgs = Organization.objects.all()
        for org in orgs:
            if not org.parent:
                self.print_nested(org, 0)
