from miembros.tests.factories import MiembroFactory
from common.tests.base import BaseTest
from ..models import Estudiante
from .factories import EstudianteFactory, MateriaFactory, CursoFactory, MatriculaFactory


class EstudianteModelTest(BaseTest):
    """
    Pruebas para el modelo de Estudiante.
    """

    def setUp(self):
        self.crear_arbol()

    def test_atributos_de_instancia_retornan_valores_validos(self):
        """
        Prueba que los atributos de la instancia sean correctamente obtenidos a partir del metodo
        getattr debido a la sobreescritura del metodo __getattr__
        """
        estudiante = EstudianteFactory()

        for attr in estudiante.__dict__:
            self.assertTrue(hasattr(estudiante, attr))
            self.assertNotEqual(getattr(estudiante, attr, 'INVALID'), 'INVALID')

    def test_atributos_random_retornan_error(self):
        """
        Prueba que cuando se intentan obtener atributos que no son de la instancia, arroja el
        debido error, debido a la sobreescritura del metodo __getattr__
        """
        import string, random
        attrs = [
            ''.join(random.SystemRandom().choice(string.ascii_lowercase) for _ in list(range(
                random.randrange(1, 13)))) for x in list(range(1, 6))
        ]
        estudiante = EstudianteFactory()

        for attr in attrs:
            with self.assertRaises(AttributeError):
                getattr(estudiante, attr)

    def test_atributos_nota_materia_numero_retorna_algo(self):
        """
        Prueba que no arroje error cuando se consulta una materia que no está en la matricula.
        """
        import random
        estudiante = EstudianteFactory()

        pks = list(range(random.randint(1, 15), random.randint(15, 30)))

        for pk in pks:
            self.assertEqual(getattr(estudiante, 'nota_materia_{}'.format(pk)), '')

    def test_nota_materia_metodo_con_materia_pasada_retorna_x(self):
        """
        Prueba que el metodo nota_materia_x retorne una x si paso la materia.
        """

        estudiante = EstudianteFactory()
        materia = MateriaFactory()
        curso = CursoFactory(materia=materia)

        matricula = MatriculaFactory(estudiante=estudiante, curso=curso, paso=True)

        self.assertEqual(getattr(estudiante, 'nota_materia_{}'.format(materia.id)), 'X')

        materia2 = MateriaFactory()
        curso2 = CursoFactory(materia=materia2)

        matricula = MatriculaFactory(estudiante=estudiante, curso=curso2, paso=False)

        self.assertEqual(getattr(estudiante, 'nota_materia_{}'.format(materia2.id)), '')
