from .. import forms, models

from common.tests.base import BaseTest
from grupos.models import Grupo
from .factories import MateriaFactory


class ReporteInstitutoFormTest(BaseTest):

    def setUp(self):
        self.crear_arbol()

    def test_get_materia_sin_materias_retorna_todas_las_materias(self):
        """
        Prueba que el metodo get_materias pueda retornar todas las materias cuando se envia vacio
        """
        [MateriaFactory() for x in range(10)]

        grupo = Grupo.objects.get(id=100)
        data = {'grupo': grupo.id}

        form = forms.ReporteInstitutoForm(data=data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_materias().count(), 10)

    def test_get_materia_retorna_solo_materias_seleccionadas(self):
        """
        Prueba que el metodo get_materias retorne solo las materias que fueron escogidas
        por el usuario.
        """
        [MateriaFactory() for x in range(10)]

        materias = list(models.Materia.objects.all().values_list('id', flat=True))[:4]

        grupo = Grupo.objects.get(id=100)
        data = {'grupo': grupo.id, 'materias': materias}

        form = forms.ReporteInstitutoForm(data=data)

        self.assertTrue(form.is_valid())

        materias_formulario = form.get_materias()
        self.assertEqual(materias_formulario.count(), len(materias))

        for materia in materias_formulario:
            self.assertIn(materia.id, materias)

    def test_get_lideres_retorna_los_miembros_a_partir_de_grupo(self):
        """
        Prueba que los lideres retornados sean todos los lideres debajo del
        grupo escogido.
        """
        grupo = Grupo.objects.get(id=300)  # ._grupos_red.values_list('lideres__id')

        form = forms.ReporteInstitutoForm(data={'grupo': grupo.id})

        self.assertTrue(form.is_valid())

        lideres = form.get_lideres()
        miembros = list(grupo._grupos_red.values_list('lideres__id', flat=True))

        self.assertEqual(lideres.count(), len(miembros))
        for lider in lideres:
            self.assertIn(lider.id, miembros)


class CursoFormTest(BaseTest):

    def setUp(self):
        self.crear_arbol()
