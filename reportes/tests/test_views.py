from unittest import mock
from django.test import tag
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from common.tests.base import BaseTest, BaseRequestFactory
from common.tests.factories import UsuarioFactory
from miembros.tests.factories import MiembroFactory
from grupos.tests.factories import GrupoFactory, GrupoHijoFactory, PredicaFactory
from miembros.models import Miembro
from .. import views

User = get_user_model()

class ReporteEstadisticoReunionesGARViewTest(BaseTest):
    """Pruebas unitarias para la vista del reporte de estadisticos de reuniones GAR."""

    URL = 'reportes:estadistico_reuniones_gar'

    def setUp(self):
        self.factory = BaseRequestFactory(self.tenant)
    
    def test_not_login_user_redirects(self):
        request = self.factory.get(self.reverse(self.URL))
        request.user = AnonymousUser()

        response = views.reporte_estadistico_reuniones_gar(request)
        self.response_302(response)
    
    def test_not_admin_not_lider_user_raises_permission_denied(self):
        request = self.factory.get(self.reverse(self.URL))
        request.user = mock.create_autospec(User, instance=True)
        request.user.has_perm.return_value = False

        with self.assertRaises(PermissionDenied):
            views.reporte_estadistico_reuniones_gar(request)
    
    def test_get(self):
        """Prueba que se pueda ver el formulario."""

        request = self.factory.get(self.reverse(self.URL))
        request.user = mock.create_autospec(User, instance=True)
        request.miembro = mock.create_autospec(Miembro, instance=True)
        request.miembro.id = 1

        response = views.reporte_estadistico_reuniones_gar(request)
        self.response_200(response) 
        self.assertContains(response, 'id_grupo')
    
    @mock.patch('reportes.views.EstadisticoReunionesGARForm', autospec=True)
    def test_formulario_invalido_not_calls_datos_reporte(self, MockForm):
        request = self.factory.post(self.reverse(self.URL), data={})
        request.user = mock.create_autospec(User, instance=True)
        request.miembro = mock.create_autospec(Miembro, instance=True)
        request.miembro.id = 1
        MockForm.return_value.is_valid.return_value = False

        response = views.reporte_estadistico_reuniones_gar(request)
        self.assertNotIn(mock.call().datos_reporte(), MockForm.mock_calls)
    
    @mock.patch('reportes.views.EstadisticoReunionesGARForm', autospec=True)
    def test_formulario_valido_calls_datos_reporte(self, MockForm):
        post_data = {'grupo': 1, 'fecha_inicial': '01/02/2018', 'fecha_final': '02/03/2018'}
        request = self.factory.post(self.reverse(self.URL), data=post_data)
        request.user = mock.create_autospec(User, instance=True)
        request.miembro = mock.create_autospec(Miembro, instance=True)
        request.miembro.id = 1
        MockForm.return_value.is_valid.return_value = True
        MockForm.return_value.datos_reporte.return_value = {}

        response = views.reporte_estadistico_reuniones_gar(request)
        self.assertIn(mock.call().datos_reporte(), MockForm.mock_calls)

class ReporteDiscipuladoViewTest(BaseTest):
    """Pruebas unitarias para la vista del reporte de discipulado."""

    URL = 'reportes:estadistico_reunion_discipulado'

    def setUp(self):
        self.admin = MiembroFactory(admin=True)
    
    def test_not_login_user_redirects_login_page(self):

        self.assertLoginRequired(self.URL)
    
    def test_not_admin_user_raises_403(self):

        self.login_usuario(UsuarioFactory())
        self.get(self.URL)
        self.response_403()
    
    def test_lider_con_grupos_debajo_gets_200(self):
        """Prueba que un lider con grupos debajo del grupo que lidera pueda ver el formulario."""

        grupo = GrupoFactory()
        lider = grupo.lideres.first()
        GrupoHijoFactory(parent=grupo)
        
        self.login_usuario(lider.usuario)
        self.get_check_200(self.URL)

    def test_admin_get(self):
        """Prueba que un administrador pueda ver el formulario."""

        self.login_usuario(self.admin.usuario)
        self.get_check_200(self.URL)
    
    @mock.patch('reportes.views.EstadisticoDiscipuladoForm', autospec=True)
    def test_post_formulario_valido_calcule_faltantes(self, MockForm):
        """Prueba que si se hace POST y el formulario es valido calcule faltantes."""

        MockForm.return_value.is_valid.return_value = True
        MockForm.return_value.get_data_estadistico_discipulos_recibido_predica.return_value = ([], 0, 0, 0)
        self.login_usuario(self.admin.usuario)
        response = self.post(self.URL, data={'predica': 1, 'grupo': 1})

        self.assertTrue(MockForm.return_value.get_faltantes_reunion_discipulado.called)
   
    @mock.patch('reportes.views.EstadisticoDiscipuladoForm', autospec=True)
    def test_post_formulario_valido_calcule_porcentajes(self, MockForm):
        """Prueba que si se hace POST y el formulario es valido calcule porcentajes."""

        MockForm.return_value.is_valid.return_value = True
        MockForm.return_value.get_data_estadistico_discipulos_recibido_predica.return_value = ([], 0, 0, 0)
        self.login_usuario(self.admin.usuario)
        response = self.post(self.URL, data={'predica': 1, 'grupo': 1})

        self.assertTrue(MockForm.return_value.get_data_estadistico_discipulos_recibido_predica.called)
    
    def test_post_formulario_invalido_muestra_errores(self):
        """
        prueba que si se hace POST y el formulario es invalido se muestren los errores correctamente.
        """

        self.login_usuario(self.admin.usuario)
        response = self.post(self.URL, data={})

        self.assertFormError(response, 'form', 'grupo', self.MSJ_OBLIGATORIO)
        self.assertFormError(response, 'form', 'predica', self.MSJ_OBLIGATORIO)


class ReporteAsistenciaDiscipuladoExcelViewTest(BaseTest):

    URL = 'reportes:reporte_asistencia_discipulado_excel'

    def setUp(self):
        self.factory = BaseRequestFactory(self.tenant)
    
    def test_not_login_user_redirects(self):
        request = self.factory.get(self.reverse(self.URL))
        request.user = AnonymousUser()

        response = views.reporte_asistencia_discipulado_excel(request)
        self.response_302(response)
    
    def test_not_admin_user_raises_permission_denied(self):
        request = self.factory.get(self.reverse(self.URL))
        request.user = mock.create_autospec(User, instance=True)

        with self.assertRaises(PermissionDenied):
            views.reporte_asistencia_discipulado_excel(request)
    
    def test_get(self):
        """Prueba que se pueda ver el formulario."""

        request = self.factory.get(self.reverse(self.URL))
        request.user = mock.create_autospec(User, instance=True)
        request.miembro = mock.create_autospec(Miembro, instance=True)
        request.miembro.id = 1

        response = views.reporte_asistencia_discipulado_excel(request)
        self.response_200(response) 
        self.assertContains(response, 'id_predica')
    
    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm.get_nombre_archivo', autospec=True, return_value='file')
    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm.data_reporte', autospec=True)
    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm.is_valid', autospec=True, return_value=True)
    def test_form_valido_calls_data_reporte(self, mock_is_valid, mock_data_reporte, mock_get_nombre_archivo):
        request = self.factory.post(self.reverse(self.URL), data={'grupo': 1, 'predica': 1})
        request.user = mock.create_autospec(User, instance=True)
        request.miembro = mock.create_autospec(Miembro, instance=True)
        request.miembro.id = 1

        response = views.reporte_asistencia_discipulado_excel(request)
        self.assertTrue(mock_data_reporte.called)
    
    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm.get_nombre_archivo', autospec=True, return_value='file')
    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm.data_reporte', autospec=True)
    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm.is_valid', autospec=True, return_value=True)
    def test_form_valido_returns_excel(self, mock_is_valid, mock_data_reporte, mock_get_nombre_archivo):
        
        request = self.factory.post(self.reverse(self.URL), data={'grupo': 1, 'predica': 1})
        request.user = mock.create_autospec(User, instance=True)
        request.miembro = mock.create_autospec(Miembro, instance=True)
        request.miembro.id = 1

        response = views.reporte_asistencia_discipulado_excel(request)
        self.assertEqual(response['Content-Type'], 'application/ms-excel')

    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm.is_valid', autospec=True, return_value=False)
    def test_form_invalido(self, mock_is_valid):
        request = self.factory.post(self.reverse(self.URL), data={})
        request.user = mock.create_autospec(User, instance=True)
        request.miembro = mock.create_autospec(Miembro, instance=True)
        request.miembro.id = 1

        response = views.reporte_asistencia_discipulado_excel(request)
        self.response_200(response) 