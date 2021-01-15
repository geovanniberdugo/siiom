from django.test import tag
from unittest import mock, skip
from ..forms import DesvincularLiderGrupoForm
from ..models import Miembro
from .factories import MiembroFactory
from common.tests.base import BaseTest
from grupos.models import Grupo, HistorialEstado


class DesvincularLiderGrupoFormTest(BaseTest):
    """Pruebas unitarias para el formulario de DesvincularLiderGrupoForm."""

    def setUp(self):
        self.crear_arbol()
        self.form = DesvincularLiderGrupoForm
        self.grupo = Grupo.objects.get(id=300)
        self.miembro = MiembroFactory(lider=True, grupo=self.grupo.parent)

    def asigna_grupo_miembro(self, grupo=None):
        if not grupo:
            grupo = self.grupo
        self.miembro.grupo_lidera = grupo
        # self.miembro.grupo = grupo.lideres.first().grupo
        self.miembro.save()
        return self.miembro

    def test_formulario_invalido_si_no_lider(self):
        """
        Verifica que el formulario retorne error si no se envia un lider.
        """

        datos = {'grupo': 300, 'grupo_destino': 200, 'nuevo_lider': 120, 'seleccionados': ['200', '100']}
        form = self.form(data=datos)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('lider', code='required'))

    def test_formulario_invalido_si_grupos_red_y_no_nuevo_lider(self):
        """
        Verifica que el formulario retorne un error en el caso que el grupo tenga discipulos y no se haya escogido
        un lider de reemplazo cuando solo hay un lider.
        """

        lider = self.grupo.lideres.first()
        self.grupo.lideres.clear()
        self.grupo.lideres.add(lider)

        self.assertTrue(self.grupo.lideres.count() == 1, "Asegurate que el tamaño de lideres de grupo sea igual a 1")

        datos = {'lider': lider.id}
        form = self.form(data=datos)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('nuevo_lider', code='required'))

    def test_formulario_invalido_si_seleccionados_y_no_grupo_destino(self):
        """
        Verifica que el formulario sea invalido si no se especifica el grupo de destino y si se escogen miembros.
        """

        lider = self.grupo.lideres.all()[0]
        self.grupo.lideres.clear()
        self.grupo.lideres.add(lider)

        datos = {
            'lider': lider.id,
            'seleccionados': list(map(str, Grupo.objects.get(id=300).miembros.all().values_list('id', flat=1)))
        }

        form = self.form(data=datos)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('grupo_destino', code='sin_destino'))

    def prueba_estado_lider(self, miembro):
        """
        Verifica que el lider sea inactivo si el formulario es valido.
        """

        self.assertEqual(miembro.estado, Miembro.INACTIVO)

    def test_lider_reemplazado_si_se_escoge_reemplazar_lider(self):
        """
        Verifica que con la opcion de nuevo_lider, se pueda reemplazar el lider.
        """

        miembro = self.miembro
        lider = self.grupo.lideres.first()

        datos = {'lider': lider.id, 'nuevo_lider': miembro.id}

        form = self.form(data=datos)

        self.assertTrue(form.is_valid())

        form.desvincular_lider()

        self.assertIn(miembro.id, self.grupo.lideres.all().values_list('id', flat=1))
        lider.refresh_from_db()  # debe actualizar
        self.prueba_estado_lider(lider)

    def test_grupo_archivado_si_solo_hay_un_lider_y_no_descendientes(self):
        """
        Verifica que un grupo sea archivado si solo hay un lider y no existen descendientes.
        """

        grupo = Grupo.objects.get(id=800)
        self.assertTrue(grupo.grupos_red.count() == 1, 'Se debe escoger un grupo sin descendientes')
        self.assertTrue(grupo.lideres.count() >= 1, 'Se debe escoger un grupo con al menos un lider')

        lider = grupo.lideres.all()[0]
        grupo.lideres.clear()
        grupo.lideres.add(lider)

        datos = {'lider': lider.id}

        form = self.form(data=datos)

        self.assertTrue(form.is_valid())

        form.desvincular_lider()

        grupo = Grupo.objects.get(id=800)
        lider.refresh_from_db()

        self.assertEqual(grupo.estado, HistorialEstado.ARCHIVADO)
        self.assertEqual(grupo.lideres.count(), 0)
        self.prueba_estado_lider(lider)
        self.assertEqual(lider.grupo, None)

    def test_grupo_lideres_sigan_siendo_si_se_reemplaza_otro_lider(self):
        """
        verifica que al momento de reemplazar un lider, el grupo, siga manteniendo los lideres con los cuales,
        no se hará ningún movimiento.
        """

        miembro = self.miembro
        lider = self.grupo.lideres.first()
        lideres = self.grupo.lideres.exclude(id=lider.id)
        datos = {'lider': lider.id, 'nuevo_lider': miembro.id}
        form = self.form(data=datos)

        self.assertTrue(form.is_valid())

        form.desvincular_lider()

        lider.refresh_from_db()
        self.prueba_estado_lider(lider)

        self.assertIn(miembro, self.grupo.lideres.all())
        self.assertEqual(len(lideres), len(self.grupo.lideres.all()))

    def test_lider_desvinculado_si_no_lidera_grupo(self):
        """
        Verifica que el miembro tambien sea desvinculado asi no lidere grupo.
        """

        miembro = self.miembro

        form = self.form(data={'lider': miembro.id})

        self.assertTrue(form.is_valid())

        form.desvincular_lider()
        miembro.refresh_from_db()

        self.prueba_estado_lider(miembro)
