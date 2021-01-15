from unittest import mock
from django.test import tag
from django.contrib.auth import get_user_model
from common.tests.base import BaseTestAPI, BaseTestRESTAPI
from common.tests.factories import UsuarioFactory
from .factories import GrupoFactory, GrupoHijoFactory, PredicaFactory, ReunionDiscipuladoFactory

User = get_user_model()


class LideresGrupoTest(BaseTestAPI):
    """
    Pruebas unitarias para la vista lideres de un grupo.
    """

    def test_get_lideres_grupo(self):
        """
        Prueba que me devuelva solo los lideres del grupo ingresado.
        """

        grupo = GrupoFactory()
        self.url = self.reverse('grupos:lideres_api', grupo.pk)
        response = self.GET()

        self.assertEqual(grupo.lideres.first().pk, response[0]['pk'])


class DiscipulosGrupoViewTest(BaseTestAPI):
    """Pruebas unitarias para la vista discipulos de un grupo."""

    URL = 'grupos:discipulos_api'

    @mock.patch('grupos.models.Grupo.discipulos', new_callable=mock.PropertyMock)
    def test_get_discipulos_grupo(self, discipulos_mock):
        """Prueba que solo devuelva los discipulos del grupo ingresado."""

        grupo = GrupoFactory()
        self.url = self.reverse(self.URL, grupo.pk)
        self.GET()
        
        self.assertTrue(discipulos_mock.called)


class ReunionDiscipuladoViewTest(BaseTestRESTAPI):
    """Pruebas unitarias para la vista de reunion discipulado de un grupo y una predica."""

    URL = 'grupos:reunion_discipulado_api'

    def test_not_login_user_returns_401(self):
        self.get(self.URL, grupo=1, predica=1)
        self.response_401()

    def test_get_reunion_discipulado_no_ingresada_retorna_404(self):
        """Prueba que si la reunión discipulado para el grupo y predica no ha sido ingresada retorna 404."""

        self.login_usuario(UsuarioFactory())
        self.get(self.URL, grupo=1, predica=1)
        self.response_404()
    
    def test_get_existe_reunion_discipulado_retorna_200(self):
        """Prueba que si existe una reunion discipulado para el grupo y predica retorne 200."""

        grupo = GrupoFactory()
        predica = PredicaFactory()
        ReunionDiscipuladoFactory(grupo=grupo, predica=predica)
        self.login_usuario(UsuarioFactory())
        self.get_check_200(self.URL, grupo=grupo.id, predica=predica.id)