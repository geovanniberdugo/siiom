from unittest import mock
from django.test import tag
from django.http import Http404
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from grupos.models import Red, Grupo
from grupos.tests.factories import GrupoFactory
from common.tests.base import BaseTest, BaseRequestFactory
from common.tests.factories import UsuarioFactory
from .factories import MiembroFactory
from ..models import Miembro
from .. import views

User = get_user_model()


class ListarLideresRedViewTest(BaseTest):
    """
    Pruebas unitarias para la vista listar lideres de una red.
    """

    def setUp(self):
        self.crear_arbol()
        self.admin = UsuarioFactory(user_permissions=('es_administrador',))

        red_jovenes = Red.objects.get(nombre='jovenes')
        self.URL = reverse('miembros:listar_lideres', args=(red_jovenes.id,))

    def test_get_red_no_existe_devuelve_404(self):
        """
        Prueba que si se envia una red que no existe la vista devuelve un status code de 404.
        """

        self.login_usuario(self.admin)
        response = self.client.get(reverse('miembros:listar_lideres', args=(100,)))
        self.response_404(response)

    def test_get_muestra_lideres_red(self):
        """
        Prueba que se listen los lideres de la red escogida.
        """

        self.login_usuario(self.admin)
        response = self.client.get(self.URL)

        lider = Grupo.objects.get(id=300).lideres.first()
        self.assertContains(response, lider.nombre.upper())


class TrasladarMiembroViewTest(BaseTest):
    """
    Pruebas unitarias para la vista de trasladar un miembro que no lidere grupo a otro grupo.
    """

    def setUp(self):
        grupo1 = GrupoFactory()
        self.grupo2 = GrupoFactory()
        self.miembro = MiembroFactory(grupo=grupo1)
        self.admin = UsuarioFactory(user_permissions=('es_administrador',))

        self.URL = reverse('miembros:trasladar', args=(self.miembro.id,))

    def test_get_miembro_no_existe_devuelve_404(self):
        """
        Prueba que cuando se envia el id de un miembro que no existe en la URL, la vista devuelve un 404.
        """

        self.login_usuario(self.admin)
        response = self.client.get(reverse('miembros:trasladar', args=(100,)))

        self.response_404(response)

    def test_get_miembro_lider_grupo_redirecciona_sin_permisos(self):
        """
        Prueba que si se intenta trasladar un miembro que lidera un grupo se redireccione a página sin permisos.
        """

        self.login_usuario(self.admin)
        lider = self.grupo2.lideres.first()
        response = self.client.get(reverse('miembros:trasladar', args=(lider.id,)))

        self.assertEqual(response.status_code, 302)

    def test_admin_get(self):
        """
        Prueba que un administrador pueda ver el template.
        """

        self.login_usuario(self.admin)
        response = self.client.get(self.URL)

        self.assertContains(response, 'input')
        self.assertContains(response, self.miembro.nombre.upper())

    def test_post_formulario_valido_traslada_miembro(self):
        """
        Prueba que si el formulario es valido traslada el miembro y redirecciona.
        """

        self.login_usuario(self.admin)
        response = self.client.post(self.URL, {'nuevo': self.grupo2.id})
        self.miembro.refresh_from_db()

        self.assertRedirects(response, self.URL)
        self.assertEqual(self.miembro.grupo, self.grupo2)

    def test_post_formulario_no_valido_muestra_errores(self):
        """
        Prueba que si el formulario no es valido se muestren los errores.
        """

        self.login_usuario(self.admin)
        response = self.client.post(self.URL, {})
        self.assertFormError(response, 'form', 'nuevo', 'Este campo es obligatorio.')


class CrearMiembroViewTest(BaseTest):
    """
    Pruebas unitarias para la vista crear miembro de una iglesia.
    """

    URL = 'miembros:nuevo'

    def setUp(self):
        self.admin = MiembroFactory(admin=True)

    def datos_formulario(self):
        """
        Retorna un diccionario con los datos para el formulario NuevoMiembroForm
        """

        from miembros.models import Miembro
        data = {
            'nombre': 'Maria', 'primer_apellido': 'Torres', 'genero': Miembro.FEMENINO, 'cedula': '122342312',
            'email': 'test@siiom.com', 'segundo_apellido': 'Mejia', 'telefono': '3423454', 'celular': '3003224543',
            'fecha_nacimiento': '1990-03-12', 'direccion': 'Cra 45 N 93 - 34', 'profesion': 'Ing. Civil',
            'estado_civil': Miembro.SOLTERO
        }

        return data

    def test_admin_get(self):
        """
        Prueba que el administrador pueda ver el template.
        """

        self.login_usuario(self.admin.usuario)
        self.get_check_200(self.URL)
        self.assertResponseContains('id_nombre', html=False)

    def test_post_formulario_valido_redirecciona_get(self):
        """
        Prueba que si se hace un POST y el formulario es valido redirecciona a la misma página.
        """

        from ..models import Miembro

        data = self.datos_formulario()
        self.login_usuario(self.admin.usuario)
        response = self.post(self.URL, data=data)

        self.assertEqual(Miembro.objects.filter(cedula=data['cedula']).count(), 1, msg="Se debio crear el miembro")
        self.assertRedirects(response, self.reverse(self.URL))

    def test_post_formulario_invalido_muestra_errores(self):
        """
        Prueba que si se hace un POST y el formulario es invalido se muestren los errores.
        """

        self.login_usuario(self.admin.usuario)
        response = self.post(self.URL, data={})

        self.assertFormError(response, 'form', 'email', self.MSJ_OBLIGATORIO)
        self.assertFormError(response, 'form', 'nombre', self.MSJ_OBLIGATORIO)
        self.assertFormError(response, 'form', 'genero', self.MSJ_OBLIGATORIO)
        self.assertFormError(response, 'form', 'cedula', self.MSJ_OBLIGATORIO)
        self.assertFormError(response, 'form', 'primer_apellido', self.MSJ_OBLIGATORIO)


class CambiarContrasenaViewTest(BaseTest):
    """Pruebas unitarias para la vista cambiar contraseña de un usuario logueado."""

    URL = 'miembros:cambiar_contrasena'

    def setUp(self):
        self.usuario = UsuarioFactory()

    def test_get_cambiar_contrasena(self):
        """"Prueba que se puede ver el template."""

        self.login_usuario(self.usuario)
        self.get_check_200(self.URL)

class DiscipuladosMiembroViewTest(BaseTest):
    
    URL = 'miembros:discipulados'

    def setUp(self):
        self.factory = BaseRequestFactory(self.tenant)

    def test_not_login_user_redirects(self):
        request = self.factory.get(self.reverse(self.URL, pk=1))
        request.user = AnonymousUser()
        response = views.discipulados(request, 1)

        self.response_302(response)
    
    def test_miembro_no_existe_returns_404(self):
        request = self.factory.get(self.reverse(self.URL, pk=1))
        request.user = mock.create_autospec(User, instance=True)

        with self.assertRaises(Http404):
            views.discipulados(request, 1)
    
    def test_get_returns_200(self):
        miembro = MiembroFactory(lider=True)
        request = self.factory.get(self.reverse(self.URL, pk=miembro.id))
        request.user = mock.create_autospec(User, instance=True)

        response = views.discipulados(request, miembro.id)
        self.response_200(response)
    
    @mock.patch('miembros.views.Miembro.predicas_recibidas', autospec=True)
    def test_get_calls_predicas_recibidas(self, mock_predicas_recibidas):
        miembro = MiembroFactory(lider=True)
        request = self.factory.get(self.reverse(self.URL, pk=miembro.id))
        request.user = mock.create_autospec(User, instance=True)

        response = views.discipulados(request, miembro.id)
        self.assertTrue(mock_predicas_recibidas.called)
