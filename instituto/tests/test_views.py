import pytest
from unittest import mock
from django.test import tag
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from common.tests.base import BaseTest, BaseRequestFactory
from common.tests.factories import UsuarioFactory
from waffle.testutils import override_switch
from .. import views

User = get_user_model()

class SeguimientoEstudianteViewTest(BaseTest):
    """Pruebas unitarias para la vista de ingresar asistencia y notas de estudiantes."""

    URL = 'instituto:seguimiento-estudiantes'
    VIEW = views.SeguimientoEstudiantesView

    def setUp(self):
        self.factory = BaseRequestFactory(self.tenant)
    
    @override_switch('instituto', active=True)
    def test_not_login_user_redirects(self):
        request = self.factory.get(self.reverse(self.URL))
        request.user = AnonymousUser()

        response = self.VIEW.as_view()(request)
        self.response_302(response)

    @override_switch('instituto', active=True)
    def test_sin_permiso_add_seguimiento_raises_permission_denied(self):
        request = self.factory.get(self.reverse(self.URL))
        request.user = mock.create_autospec(User, instance=True)
        request.user.has_perms.return_value = False

        with pytest.raises(PermissionDenied):
            response = self.VIEW.as_view()(request)
    
    @override_switch('instituto', active=True)
    def test_get(self):
        request = self.factory.get(self.reverse(self.URL))
        request.user = mock.create_autospec(User, instance=True)

        response = self.VIEW.as_view()(request)
        self.response_200(response)
        self.assertContains(response, 'id_curso')

class ReporteInstitutoTestView(BaseTest):

    def setUp(self):
        self.crear_arbol()
        self.admin = UsuarioFactory(user_permissions=('es_administrador',))
        self.URL = reverse('instituto:reporte-instituto')

    @override_switch('instituto', active=True)
    def test_retorne_html_con_formulario_invalido(self):
        """
        Prueba que con un POST y con errores en el formulario, se muestran los errores
        y la respuesta es un html.
        """
        self.login_usuario(self.admin)
        response = self.client.post(self.URL, {})

        self.assertTrue(response._headers['content-type'][1].startswith('text/html'))
        self.assertFormError(response, 'form', 'grupo', self.MSJ_OBLIGATORIO)

    @override_switch('instituto', active=True)
    def test_retorne_excel_con_formulario_valido(self):
        """
        Prueba que cuando el formulario se envia correcto, la respuesta sera un archivo
        binario de excel.
        """
        self.login_usuario(self.admin)
        response = self.client.post(self.URL, {'grupo': 100})

        self.assertTrue(response._headers['content-type'][1].startswith('application/vnd.ms-excel'))
