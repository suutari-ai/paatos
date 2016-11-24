import factory
from faker import Faker

from decisions.models import Event

fake = Faker()
fake.seed(7)


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    name = fake.text(max_nb_chars=20)
    start_date = fake.date()
