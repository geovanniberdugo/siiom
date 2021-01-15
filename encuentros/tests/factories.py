import factory
from grupos.tests.factories import GrupoFactory
from miembros.tests.factories import MiembroFactory


class EncuentroFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'encuentros.Encuentro'

    hotel = 'Hotel del Prado'
    tesorero = factory.SubFactory(MiembroFactory)
    coordinador = factory.SubFactory(MiembroFactory)
    fecha_final = factory.Faker('date_time_this_decade', after_now=True)
    fecha_inicial = factory.Faker('date_time_this_decade', before_now=True)


class EncontristaFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'encuentros.Encontrista'

    genero = 'F'
    email = factory.Faker('email')
    grupo = factory.SubFactory(GrupoFactory)
    encuentro = factory.SubFactory(EncuentroFactory)
    primer_nombre = factory.Faker('first_name', locale='es')
    primer_apellido = factory.Faker('last_name', locale='es')
    identificacion = factory.sequence(lambda n: '112343%02d' % n)
