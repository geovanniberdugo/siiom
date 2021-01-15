from unittest import mock
from django.test import tag
from common.tests.base import BaseTest
from grupos.models import Grupo
from grupos.tests.factories import GrupoFactory, GrupoHijoFactory, PredicaFactory, AsistenciaDiscipuladoFactory
from .factories import MiembroFactory


class MiembroModelTest(BaseTest):
    """
    Pruebas unitarias para el modelo Miembro.
    """

    def get_lider_grupo(self, grupo):
        """Obtiene el lider del grupo"""

        return Grupo.objects.get(id=grupo).lideres.first()

    def test_es_director_red(self):
        """Prueba que si el miembro es director de red devuelva True."""

        self.crear_arbol()
        director = Grupo.objects.get(id=200).lideres.first()
        no_director = Grupo.objects.get(id=500).lideres.first()

        self.assertTrue(director.es_director_red)
        self.assertFalse(no_director.es_director_red)

    def test_trasladar_miembro_mismo_grupo(self):
        """Prueba que cuando se quiere trasladar un miembro al mismo grupo no se cambie el grupo actual."""

        grupo = GrupoFactory()
        miembro = MiembroFactory(grupo=grupo)

        miembro.trasladar(grupo)
        miembro.refresh_from_db()
        self.assertEqual(miembro.grupo, grupo)

    def test_trasladar_miembro_mueve(self):
        """Prueba que se traslada un miembro a un nuevo grupo."""

        grupo1 = GrupoFactory()
        grupo2 = GrupoFactory()
        miembro = MiembroFactory(grupo=grupo1)

        miembro.trasladar(grupo2)
        miembro.refresh_from_db()
        self.assertTrue(miembro.grupo, grupo2)

    def test_resetear_contrasena_cedula(self):
        """Prueba que se cambie la contraseña del miembro a su cedula."""

        miembro = MiembroFactory(lider=True)
        miembro.usuario.set_password('password')

        miembro.resetear_contrasena()
        self.assertTrue(
            miembro.usuario.check_password(miembro.cedula),
            msg="La nueva contraseña deberia ser la identificación del miembro."
        )

    def test_resetear_contresena_envia_email(self):
        """Prueba que cuando se modifique la contraseña se notifique al miembro de esto por mail."""

        from django.core import mail

        miembro = MiembroFactory(lider=True)

        miembro.resetear_contrasena()
        self.assertEqual(len(mail.outbox), 1, msg="El outbox deberia contener un mensaje.")
        self.assertListEqual(mail.outbox[0].to, [miembro.email])

    def test_tiene_subred_retorna_true(self):
        """"Prueba que si el grupo que lidera el miembro tiene hijos retorne true."""

        grupo = GrupoFactory()
        lider = grupo.lideres.first()
        GrupoHijoFactory(parent=grupo)

        self.assertTrue(lider.tiene_subred, msg="Debe devolver True ya que el grupo del miembro es padre de otro grupo")
    
    def test_tiene_subred_retorna_false(self):
        """Prueba que si el grupo que lidera el miembro no tiene hijos retorne false."""

        grupo = GrupoFactory()
        lider = grupo.lideres.first()

        self.assertFalse(lider.tiene_subred, msg="Debe retornar False ya que el grupo no tiene hijos")
    
    def test_tiene_subred_retorna_false_sino_miembro_no_lidera_grupo(self):

        lider = MiembroFactory(lider=True)

        self.assertFalse(lider.tiene_subred, msg="El miembro no lidera grupo por lo tanto debe retornar false")
    
    def test_pastores_cuando_pastor_ancestro(self):
        """Prueba el pastor haga parte de los pastores porque pertenece a los ancentros del miembro"""

        self.crear_arbol()
        pastor = MiembroFactory(lider_pastor=True, grupo_lidera=Grupo.objects.get(id=300))

        lider = self.get_lider_grupo(600)
        pastores = lider.pastores()

        self.assertIn(pastor, pastores)

    def test_pastores_cuando_pastor_no_ancestro(self):
        """Prueba el pastor no haga parte de los pastores porque no pertenece a los ancentros del miembro"""

        self.crear_arbol()
        pastor = MiembroFactory(lider_pastor=True, grupo_lidera=Grupo.objects.get(id=300))

        lider = self.get_lider_grupo(700)
        pastores = lider.pastores()

        self.assertNotIn(pastor, pastores)

    def test_pastores_retorne_solo_miembros_permiso_pastor(self):
        """Prueba que solo devuelva miembros con permiso de pastor"""

        self.crear_arbol()
        pastor = MiembroFactory(lider=True, grupo_lidera=Grupo.objects.get(id=300))

        lider = self.get_lider_grupo(600)
        pastores = lider.pastores()

        self.assertNotIn(pastor, pastores)
    
    def test_pastores_incluya_colideres_y_mismo_si_pastores(self):
        """Prueba que si el miembro o alguno de sus colideres es pastor los incluya."""

        self.crear_arbol()
        pastor = MiembroFactory(lider_pastor=True, grupo_lidera=Grupo.objects.get(id=600))

        lider = self.get_lider_grupo(600)
        pastores = lider.pastores()

        self.assertIn(pastor, pastores)

    def test_predicas_recibidas_retorna_predica_dada(self):
        predica = PredicaFactory()
        miembro = MiembroFactory(lider=True)
        AsistenciaDiscipuladoFactory(miembro=miembro, reunion__predica=predica)

        self.assertIn(predica, miembro.predicas_recibidas())

    def test_predicas_recibidas_no_retorna_predica_no_dada(self):
        predica = PredicaFactory()
        miembro = MiembroFactory(lider=True)

        self.assertNotIn(predica, miembro.predicas_recibidas())

    @mock.patch('grupos.models.Grupo.cabeza_red', new_callable=mock.PropertyMock)
    def test_cabeza_red(self, mock_cabeza_red):
        miembro = MiembroFactory(grupo=GrupoFactory())
        miembro.cabeza_red

        self.assertTrue(mock_cabeza_red.called)
    
    @mock.patch('grupos.models.Grupo.padre_subred')
    def test_padre_subred(self, mock_padre_subred):
        grupo=GrupoFactory()
        miembro = MiembroFactory(grupo=grupo)
        miembro.padre_subred(grupo)

        self.assertTrue(mock_padre_subred.called)

