import factory
from common.tests.factories import UsuarioFactory


class ZonaFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'miembros.Zona'
        django_get_or_create = ('nombre',)

    nombre = 'zona 1'


class BarrioFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'miembros.Barrio'
        django_get_or_create = ('nombre',)

    nombre = 'prado'
    zona = factory.SubFactory(ZonaFactory)


class MiembroFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'miembros.Miembro'

    grupo_lidera = None
    email = factory.Faker('email')
    nombre = factory.Faker('first_name', locale='es')
    cedula = factory.sequence(lambda n: '112343%02d' % n)
    primer_apellido = factory.Faker('last_name', locale='es')
    grupo = factory.LazyAttribute(lambda o: o.grupo_lidera.parent if o.grupo_lidera else None)

    class Params:
        lider = factory.Trait(
            usuario=factory.SubFactory(UsuarioFactory, user_permissions=['es_lider'], miembro=None)
        )
        admin = factory.Trait(
            usuario=factory.SubFactory(UsuarioFactory, user_permissions=['es_administrador'], miembro=None)
        )
        pastor = factory.Trait(
            usuario=factory.SubFactory(UsuarioFactory, user_permissions=['es_pastor'], miembro=None)
        )
        lider_pastor = factory.Trait(
            usuario=factory.SubFactory(UsuarioFactory, user_permissions=['es_lider', 'es_pastor'], miembro=None)
        )
        admin_lider = factory.Trait(
            usuario=factory.SubFactory(UsuarioFactory, user_permissions=['es_lider', 'es_administrador'], miembro=None)
        )
