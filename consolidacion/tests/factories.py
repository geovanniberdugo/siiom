import factory


class VisitaFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'consolidacion.Visita'

    genero = 'F'
    telefono = 3542345
    primer_nombre = factory.Faker('first_name', locale='es')
    primer_apellido = factory.Faker('last_name', locale='es')
