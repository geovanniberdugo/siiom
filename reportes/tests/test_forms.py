from unittest import mock
from django.test import tag
from common.tests.base import BaseTest
from miembros.tests.factories import MiembroFactory
from miembros.models import Miembro
from grupos.models import Grupo, Predica
from grupos.tests.factories import GrupoFactory, GrupoHijoFactory, PredicaFactory, AsistenciaDiscipuladoFactory
from ..forms import (
    PredicaFormMixin, GrupoFormMixin, EstadisticoDiscipuladoForm, RangoFechasFormMixin,
    ReporteAsistenciaDiscipuladoExcelForm, EstadisticoReunionesGARForm
)

class PredicaFormMixinTest(BaseTest):
    """Pruebas unitarias para el mixin de predicas."""

    @mock.patch('reportes.forms.PredicaFormMixin._miembro', autospec=True)
    @mock.patch('grupos.managers.PredicaManager.disponibles', autospec=True)
    def test_campo_predica_filtra_predicas_segun_miembro(self, mock_disponibles, mock_miembro):
        """Prueba que las predicas se filtren según el miembro logueado."""

        PredicaFormMixin()
        self.assertTrue(mock_disponibles.called)

class GrupoFormMixinTest(BaseTest):
    """Pruebas unitarias paa el mixin de grupos."""

    @mock.patch('reportes.forms.GrupoFormMixin._miembro', autospec=True)
    @mock.patch('grupos.managers.GrupoManager.disponibles_ver', autospec=True)
    def test_campo_grupo_filtra_grupos_segun_miembro(self, mock_disponibles_ver, mock_miembro):
        """Prueba que los grupos se filtren según el miembro loguedo."""

        GrupoFormMixin()
        self.assertTrue(mock_disponibles_ver.called)

class EstadisticoDiscipuladoFormTest(BaseTest):
    """Pruebas unitarias para el formulario de reporte estadístico de reuniones discipulado."""

    @mock.patch('grupos.managers.GrupoManager.disponibles_ver', autospec=True)
    def test_campo_grupo_filtra_grupos_segun_miembro(self, mock_disponible_ver):
        """Prueba que los grupos se filtren según el miembro logueado."""

        EstadisticoDiscipuladoForm(mock.create_autospec(Miembro, instance=True))
        self.assertTrue(mock_disponible_ver.called)
    
    @mock.patch('reportes.forms.Miembro', autospec=True)
    @mock.patch('reportes.forms.EstadisticoDiscipuladoForm._calcula_porcentaje', autospec=True)
    @mock.patch('reportes.forms.EstadisticoDiscipuladoForm._get_form_data', autospec=True)
    def test_get_estadistico_discipulos_recibido_predica_muestre_hijos_que_pueden_reportar_reunion(
        self, mock_get_form_data, mock_calcula_porcentaje, MockMiembro
    ):
        """Prueba que solo se muestren los hijos que tengan grupos debajo de ellos."""

        mock_calcula_porcentaje.return_value = 2
        MockPredica = mock.create_autospec(Predica)
        MockPredica.return_value = 1

        mock_grupo = mock.create_autospec(Grupo, instance=True)
        mock_grupo.configure_mock(**{
            'get_children.return_value.pueden_reportar_discipulado.return_value': [GrupoFactory.build()],
        })
        mock_get_form_data.return_value = (mock_grupo, MockPredica())
        
        form = EstadisticoDiscipuladoForm(mock.create_autospec(Miembro, instance=True), data={'predica': 1, 'grupo': 1})
        data = form.get_data_estadistico_discipulos_recibido_predica()

        self.assertEqual(len(data[0]), 1)
    
    @mock.patch('reportes.forms.EstadisticoDiscipuladoForm._get_form_data', autospec=True)
    def test_get_estadistico_discipulos_no_tiene_hijos_retorne_lista_vacia_valores_0(self, mock_get_form_data):
        """Prueba que si el grupo ingresado no tiene hijos que pueden reportar reunion, el metodo retorne una lista
        vacia y lo demas valores en 0."""

        MockPredica = mock.create_autospec(Predica)
        MockPredica.return_value = 1
        mock_grupo = mock.create_autospec(Grupo, instance=True)
        mock_grupo.configure_mock(**{'get_children.return_value.pueden_reportar_discipulado.return_value': []})
        mock_get_form_data.return_value = (mock_grupo, MockPredica())

        form = EstadisticoDiscipuladoForm(mock.create_autospec(Miembro, instance=True), data={'predica': 1, 'grupo': 1})
        data = form.get_data_estadistico_discipulos_recibido_predica()

        self.assertEqual(data, ([], 0, 0, 0))

    def test_get_estadistico_discipulos_agregue_total_lideres_a_grupo(self):
        """Prueba que se agregue el total de lideres subred al grupo"""

        grupo1 = GrupoFactory()
        grupo2 = GrupoHijoFactory(parent=grupo1)
        grupo3 = GrupoHijoFactory(parent=grupo1)
        grupo4 = GrupoHijoFactory(parent=grupo2)

        miembro = MiembroFactory(admin_lider=True, grupo_lidera=grupo1)
        predica = PredicaFactory(miembro=miembro)

        form = EstadisticoDiscipuladoForm(miembro, data={'predica': predica.id, 'grupo': grupo1.id})
        form.is_valid()
        data = form.get_data_estadistico_discipulos_recibido_predica()

        self.assertEqual(data[0][0].total_lideres_subred, 2)
    
    def test_get_estadistico_discipulos_agregue_numero_grupos_reportaron(self):
        """Prueba que se agregue el numero de grupos que reportaron reunion"""

        grupo1 = GrupoFactory()
        grupo2 = GrupoHijoFactory(parent=grupo1)
        grupo3 = GrupoHijoFactory(parent=grupo1)
        grupo4 = GrupoHijoFactory(parent=grupo2)
        grupo5 = GrupoHijoFactory(parent=grupo4)

        miembro = MiembroFactory(admin_lider=True, grupo_lidera=grupo1)
        predica = PredicaFactory(miembro=miembro)

        AsistenciaDiscipuladoFactory(miembro=grupo2.lideres.first(), reunion__predica=predica, reunion__grupo=grupo2)
        AsistenciaDiscipuladoFactory(miembro=grupo4.lideres.first(), reunion__predica=predica, reunion__grupo=grupo4)

        form = EstadisticoDiscipuladoForm(miembro, data={'predica': predica.id, 'grupo': grupo1.id})
        form.is_valid()
        data = form.get_data_estadistico_discipulos_recibido_predica()

        self.assertEqual(data[0][0].numero_grupos_reportaron, 2)
    
    def test_get_estadistico_discipulos_agregue_numero_grupos_no_reportaron(self):
        """Prueba que se agregue el numero de grupos que no reportaron reunion"""

        grupo1 = GrupoFactory()
        grupo2 = GrupoHijoFactory(parent=grupo1)
        grupo3 = GrupoHijoFactory(parent=grupo1)
        grupo4 = GrupoHijoFactory(parent=grupo2)
        grupo5 = GrupoHijoFactory(parent=grupo4)

        miembro = MiembroFactory(admin_lider=True, grupo_lidera=grupo1)
        predica = PredicaFactory(miembro=miembro)

        form = EstadisticoDiscipuladoForm(miembro, data={'predica': predica.id, 'grupo': grupo1.id})
        form.is_valid()
        data = form.get_data_estadistico_discipulos_recibido_predica()

        self.assertEqual(data[0][0].numero_grupos_no_reportaron, 2)

    def test_get_estadistico_discipulos_agregue_numero_lideres_asistentes_predica_a_grupo(self):
        """Prueba que se agregue el numero de lideres subred asistentes a la predica al grupo"""

        grupo1 = GrupoFactory()
        grupo2 = GrupoHijoFactory(parent=grupo1)
        grupo3 = GrupoHijoFactory(parent=grupo1)
        grupo4 = GrupoHijoFactory(parent=grupo2)

        miembro = MiembroFactory(admin_lider=True, grupo_lidera=grupo1)
        predica = PredicaFactory(miembro=miembro)
        predica2 = PredicaFactory(miembro=miembro, nombre='asdad')
        
        # Prueba con mas de una asistencia para el mismo lider con la misma predica
        AsistenciaDiscipuladoFactory(miembro=grupo2.lideres.first(), reunion__predica=predica, reunion__grupo=grupo2)
        AsistenciaDiscipuladoFactory(miembro=grupo2.lideres.first(), reunion__predica=predica, reunion__grupo=grupo2)
        AsistenciaDiscipuladoFactory(miembro=grupo2.lideres.first(), reunion__predica=predica2, reunion__grupo=grupo2)

        form = EstadisticoDiscipuladoForm(miembro, data={'predica': predica.id, 'grupo': grupo1.id})
        form.is_valid()
        data = form.get_data_estadistico_discipulos_recibido_predica()

        self.assertEqual(data[0][0].numero_lideres_asistentes_predica, 1)

    def test_get_estadistico_discipulos_agregue_procentaje_a_grupo(self):
        """Prueba que se agregue el porcentaje de lideres subred asistentes a la predica al grupo"""

        grupo1 = GrupoFactory()
        grupo2 = GrupoHijoFactory(parent=grupo1)
        grupo3 = GrupoHijoFactory(parent=grupo1)
        grupo4 = GrupoHijoFactory(parent=grupo2)

        miembro = MiembroFactory(admin_lider=True, grupo_lidera=grupo1)
        predica = PredicaFactory(miembro=miembro)
        predica2 = PredicaFactory(miembro=miembro, nombre='asdad')
        
        # Prueba con mas de una asistencia para el mismo lider con la misma predica
        AsistenciaDiscipuladoFactory(miembro=grupo2.lideres.first(), reunion__predica=predica, reunion__grupo=grupo2)
        AsistenciaDiscipuladoFactory(miembro=grupo2.lideres.first(), reunion__predica=predica, reunion__grupo=grupo2)
        AsistenciaDiscipuladoFactory(miembro=grupo2.lideres.first(), reunion__predica=predica2, reunion__grupo=grupo2)

        form = EstadisticoDiscipuladoForm(miembro, data={'predica': predica.id, 'grupo': grupo1.id})
        form.is_valid()
        data = form.get_data_estadistico_discipulos_recibido_predica()

        self.assertEqual(data[0][0].porcentaje, 50)

    @mock.patch('grupos.managers.GrupoQuerySet.faltantes_reportar_discipulado', autospec=True)
    def test_get_faltantes_reunion_discipulado_llama_faltantes(self, mock_faltantes):
        
        grupo1 = GrupoFactory()
        grupo2 = GrupoHijoFactory(parent=grupo1)
        miembro = MiembroFactory(admin_lider=True, grupo_lidera=grupo1)
        predica = PredicaFactory(miembro=miembro)

        form = EstadisticoDiscipuladoForm(miembro, data={'predica': predica.id, 'grupo': grupo1.id})
        form.is_valid()
        form.get_faltantes_reunion_discipulado()

        self.assertTrue(mock_faltantes.called)

class ReporteAsistenciaDiscipuladoExcelFormTest(BaseTest):
    """Pruebas unitarias para el formulario de reporte D12 excel."""

    def setUp(self):
        self.mock_miembro = mock.create_autospec(Miembro, instance=True)

    def test_form_has_predica_field(self):
        form = ReporteAsistenciaDiscipuladoExcelForm(self.mock_miembro)
        self.assertIsInstance(form, PredicaFormMixin)

    def test_form_has_grupo_field(self):
        form = ReporteAsistenciaDiscipuladoExcelForm(self.mock_miembro)
        self.assertIsInstance(form, GrupoFormMixin)
    
    @mock.patch('reportes.forms.Miembro.objects.lideres_subred', autospec=True)
    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm._get_form_data', autospec=True)
    def test_data_reporte_calls_lideres_subred(self, mock_form_data, mock_lideres_subred):
        form = ReporteAsistenciaDiscipuladoExcelForm(self.mock_miembro)
        mock_form_data.return_value = (GrupoFactory.build(), PredicaFactory.build())
        form.data_reporte()

        self.assertTrue(mock_lideres_subred.called)
    
    @mock.patch('reportes.forms.ReporteAsistenciaDiscipuladoExcelForm._get_form_data', autospec=True)
    @mock.patch('miembros.managers.MiembroQuerySet.add_recibio_discipulado', autospec=True)
    def test_data_reporte_calls_add_recibio_discipulado(
        self, mock_add_recibio_discipulado, mock_form_data
    ):

        form = ReporteAsistenciaDiscipuladoExcelForm(self.mock_miembro)
        mock_form_data.return_value = (GrupoFactory.build(), PredicaFactory.build())
        form.data_reporte()

        self.assertTrue(mock_add_recibio_discipulado.called)

class EstadisticoReunionesGARFormTest(BaseTest):
    def setUp(self):
        self.mock_miembro = mock.create_autospec(Miembro, instance=True)
    
    def test_form_has_grupo_field(self):
        form = EstadisticoReunionesGARForm(self.mock_miembro)
        self.assertIsInstance(form, GrupoFormMixin)
    
    def test_form_has_rango_fechas_field(self):
        form = EstadisticoReunionesGARForm(self.mock_miembro)
        self.assertIsInstance(form, RangoFechasFormMixin)
    
    def test_data_reporte(self):
        print('..................probar este metodo....EstadisticoReunionesGARFormTest...reportes.........')

