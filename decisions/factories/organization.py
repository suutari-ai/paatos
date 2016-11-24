import factory
from faker import Faker

from decisions.models import Organization, Post

fake = Faker()
fake.seed(7)


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = fake.company()
    classification = fake.company_suffix()
    founding_date = fake.date_time_this_century(before_now=True, after_now=False)


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    label = fake.word()
    organization = factory.SubFactory(OrganizationFactory)
    start_date = fake.date_time_this_century(before_now=True, after_now=False)
