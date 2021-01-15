import factory, datetime
from common.tests.factories import UsuarioFactory


class EstudianteFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'instituto.Estudiante'

    nombres = factory.Faker('first_name', locale='es')
    apellidos = factory.Faker('last_name', locale='es')
    identificacion = factory.sequence(lambda n: '12344%02d' % n)
    grupo = factory.SubFactory('grupos.tests.factories.GrupoFactory')


class MateriaFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'instituto.Materia'

    grupos_minimo = 0
    dependencia = None
    nombre = factory.Faker('first_name', locale='es')


class SalonFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'instituto.Salon'

    nombre = factory.Faker('first_name', locale='es')
    capacidad = 0


class CursoFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'instituto.Curso'

    dia = ['0']
    precio = 0
    estado = 'A'
    hora_fin = factory.Faker('time')
    fecha_fin = factory.Faker('date')
    hora_inicio = factory.Faker('time')
    fecha_inicio = factory.Faker('date')
    salon = factory.SubFactory(SalonFactory)
    materia = factory.SubFactory(MateriaFactory)
    # profesor = factory.SubFactory('miembros.tests.factories.MiembroFactory')


class MatriculaFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'instituto.Matricula'

    paso = False
    curso = factory.SubFactory(CursoFactory)
    estudiante = factory.SubFactory(EstudianteFactory)
    fecha = factory.LazyFunction(datetime.datetime.now)