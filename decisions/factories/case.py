import factory
from faker import Faker

from decisions.models import Action, Case, Function

from .event import EventFactory

fake = Faker()
fake.seed(7)


class FunctionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Function
    name = fake.text(max_nb_chars=20)


class CaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Case

    title = fake.text(max_nb_chars=50)
    register_id = factory.Sequence(lambda n: 'HEL 2016-{:0>6}'.format(n))
    function = factory.SubFactory(FunctionFactory)


class ActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Action

    title = fake.text(max_nb_chars=50)
    case = factory.SubFactory(CaseFactory)
    event = factory.SubFactory(EventFactory)
    resolution = 'proposed'
    ordering = factory.Sequence(lambda n: n)
