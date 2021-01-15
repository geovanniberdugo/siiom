import factory
from common.tests.factories import UsuarioFactory


class DepartamentoFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'organizacional.Departamento'
        django_get_or_create = ['nombre']

    nombre = 'Financiero'


class AreaFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'organizacional.Area'
        django_get_or_create = ['nombre']

    nombre = 'Contabilidad'
    departamento = factory.SubFactory(DepartamentoFactory)


class EmpleadoFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'organizacional.Empleado'

    cargo = 'Ing. de sistemas'
    usuario = factory.SubFactory(UsuarioFactory)
    cedula = factory.sequence(lambda n: '112343%02d' % n)
    primer_nombre = factory.Faker('first_name', locale='es')
    segundo_nombre = factory.Faker('first_name', locale='es')
    primer_apellido = factory.Faker('last_name', locale='es')
    segundo_apellido = factory.Faker('last_name', locale='es')

    class Params:
        admin = factory.Trait(
            usuario=factory.SubFactory(UsuarioFactory, user_permissions=['es_administrador_sgd'])
        )
