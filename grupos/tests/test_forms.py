from unittest import mock, skip
from django.test import tag
from django.db import IntegrityError
from django.core.exceptions import NON_FIELD_ERRORS
from miembros.tests.factories import MiembroFactory, BarrioFactory
from common.tests.base import BaseTest
from miembros.models import Miembro
from ..models import Grupo, Red, HistorialEstado, ReunionDiscipulado
from ..forms import (
    GrupoRaizForm, NuevoGrupoForm, EditarGrupoForm, TrasladarLideresForm,
    ArchivarGrupoForm, ReportarReunionDiscipuladoAdminForm
)
from .factories import (
    GrupoFactory, GrupoRaizFactory, RedFactory, PredicaFactory, GrupoHijoFactory, ReunionDiscipuladoFactory
)


class GrupoRaizFormTest(BaseTest):
    """
    Pruebas unitarias para el formulario de creación y/o edición del grupo raiz.
    """

    def setUp(self):
        self.lider1 = MiembroFactory(lider=True)
        self.lider2 = MiembroFactory(lider=True)
        self.barrio = BarrioFactory()

    def datos_formulario(self):
        """
        Retorna un diccionario con datos para el formulario GrupoRaiz.
        """

        data = {
            'direccion': 'Calle 34 N 74 - 23', 'estado': 'AC', 'fechaApertura': '2012-03-03', 'diaGAR': '1',
            'horaGAR': '12:00', 'diaDiscipulado': '3', 'horaDiscipulado': '16:00', 'nombre': 'Pastor presidente',
            'barrio': self.barrio.id, 'lideres': [self.lider1.id, self.lider2.id]
        }

        return data

    def test_campo_lideres_solo_muestra_lideres(self):
        """
        Prueba que el campo lideres solo se muestren miembros que sean lideres.
        """

        no_lider = MiembroFactory()
        form = GrupoRaizForm()

        self.assertNotIn(no_lider, form.fields['lideres'].queryset)

    def test_campo_lideres_solo_muestra_lideres_sin_grupo(self):
        """
        Prueba que en el campo lideres solo se muestren miembros que sean lideres que no lideren grupo.
        """

        grupo = GrupoFactory()
        lider_sin_grupo = MiembroFactory(lider=True)
        form = GrupoRaizForm()

        self.assertNotIn(grupo.lideres.first(), form.fields['lideres'].queryset)
        self.assertIn(lider_sin_grupo, form.fields['lideres'].queryset)

    def test_campo_lideres_muestra_lideres_del_grupo_raiz(self):
        """
        Prueba que en el campo lideres muestren los lideres del grupo raiz.
        """

        raiz = GrupoRaizFactory()
        form = GrupoRaizForm(instance=raiz)

        self.assertIn(raiz.lideres.first(), form.fields['lideres'].queryset)

    def test_formulario_crea_raiz_se_asigna_grupo_a_lideres_escogidos(self):
        """
        Prueba que cuando se guarde el formulario se crea el grupo raiz sino existe y es asignado a los lideres
        escogidos.
        """

        form = GrupoRaizForm(data=self.datos_formulario())
        raiz = form.save()
        self.lider1.refresh_from_db()
        self.lider2.refresh_from_db()

        self.assertEqual(len(Grupo.get_root_nodes()), 1)
        self.assertEqual(self.lider1.grupo_lidera, raiz)
        self.assertEqual(self.lider2.grupo_lidera, raiz)

    def test_formulario_no_crea_nueva_raiz_si_ya_existe(self):
        """
        Prueba que cuando se guarde el formulario no se cree un nuevo grupo raiz si ya existe.
        """

        raiz = GrupoRaizFactory()
        form = GrupoRaizForm(instance=raiz, data=self.datos_formulario())
        form.save()

        self.assertEqual(len(Grupo.get_root_nodes()), 1)

    def test_modificar_lideres_raiz(self):
        """
        Prueba que cuando se editen los lideres del grupo raiz, se les coloque a los lideres nuevos el grupo raiz como
        su grupo que lidera y a los lideres que se cambiaron se les quite.
        """

        raiz = GrupoRaizFactory()
        lider3 = MiembroFactory(lider=True, grupo_lidera=raiz)
        lideres_viejos = list(raiz.lideres.values_list('id', flat=True))

        data = self.datos_formulario()
        data['lideres'].append(lider3.id)
        form = GrupoRaizForm(instance=raiz, data=data)
        form.save()

        lider3.refresh_from_db()
        self.lider1.refresh_from_db()
        self.lider2.refresh_from_db()
        self.assertEqual(lider3.grupo_lidera, raiz)
        self.assertEqual(self.lider1.grupo_lidera, raiz)
        self.assertEqual(self.lider2.grupo_lidera, raiz)
        self.assertEqual(len(raiz.lideres.filter(id__in=lideres_viejos)), 1)

    @mock.patch('django.db.models.query.QuerySet.update', side_effect=IntegrityError)
    def test_error_al_guardar_formulario_no_se_guarda_nada_en_db(self, update_mock):
        """
        Prueba que si ocurre un error al guardar el formulario no se guarde ni el grupo ni los lideres.
        """

        form = GrupoRaizForm(data=self.datos_formulario())
        form.save()
        self.lider1.refresh_from_db()
        self.lider2.refresh_from_db()

        self.assertTrue(update_mock.called)
        self.assertEqual(len(Grupo.get_root_nodes()), 0)
        self.assertEqual(self.lider1.grupo_lidera, None)
        self.assertEqual(self.lider2.grupo_lidera, None)

    @mock.patch('django.db.models.query.QuerySet.update', side_effect=IntegrityError)
    def test_error_al_guardar_formulario_agrega_error_form(self, update_mock):
        """
        Prueba que si ocurre un error al momento de guardar el formulario, se agregue un error al formulario.
        """

        form = GrupoRaizForm(data=self.datos_formulario())
        form.save()

        self.assertTrue(update_mock.called)
        self.assertEqual(len(form.non_field_errors()), 1)


class NuevoGrupoFormTest(BaseTest):
    """
    Pruebas unitarias para el formulario de creación de grupos de una iglesia.
    """

    def setUp(self):
        self.crear_arbol()
        grupo3 = Grupo.objects.get(id=300)
        self.padre = Grupo.objects.get(id=800)
        self.lider1 = MiembroFactory(lider=True, grupo=grupo3)
        self.lider2 = MiembroFactory(lider=True, grupo=self.padre)
        self.barrio = BarrioFactory()
        self.red_jovenes = Red.objects.get(nombre='jovenes')

    def datos_formulario(self):
        """
        Retorna un diccionario con datos para el formulario GrupoRaiz.
        """

        data = {
            'direccion': 'Calle 34 N 74 - 23', 'estado': 'A', 'fechaApertura': '2012-03-03', 'diaGAR': '1',
            'horaGAR': '12:00', 'diaDiscipulado': '3', 'horaDiscipulado': '16:00', 'nombre': 'Pastor presidente',
            'barrio': self.barrio.id, 'lideres': [self.lider1.id, self.lider2.id], 'parent': self.padre.id
        }

        return data

    def test_campo_parent_solo_muestra_grupos_red_ingresada(self):
        """
        Prueba que el campo parent solo muestra los grupos pertenecientes a la red ingresada.
        """

        raiz = Grupo.objects.get(id=100)
        grupo1 = Grupo.objects.get(id=300)
        grupo2 = Grupo.objects.get(id=400)

        form = NuevoGrupoForm(red=self.red_jovenes)

        self.assertIn(grupo1, form.fields['parent'].queryset)
        self.assertNotIn(grupo2, form.fields['parent'].queryset)
        self.assertNotIn(raiz, form.fields['parent'].queryset)

    def test_campo_parent_muestra_raiz_sino_red_no_tiene_grupos(self):
        """
        Prueba que el campo parent muestre el grupo raiz de la iglesia si la red ingresada no tiene ningún grupo.
        """

        raiz = Grupo.objects.get(id=100)
        otro = Grupo.objects.get(id=300)
        red_nueva = RedFactory(nombre='nueva red')

        form = NuevoGrupoForm(red=red_nueva)
        self.assertIn(raiz, form.fields['parent'].queryset)
        self.assertNotIn(otro, form.fields['parent'].queryset)

    @skip
    def test_campo_lideres_solo_muestra_lideres(self):
        """
        Prueba que el campo lideres solo se muestren miembros que sean lideres.
        """

        no_lider = MiembroFactory()
        form = NuevoGrupoForm(red=self.red_jovenes)

        self.assertNotIn(no_lider, form.fields['lideres'].queryset)

    @skip
    def test_campo_lideres_solo_muestra_lideres_sin_grupo(self):
        """
        Prueba que en el campo lideres solo se muestren miembros que sean lideres que no lideren grupo.
        """

        grupo = Grupo.objects.get(id=300)
        lider_sin_grupo = MiembroFactory(lider=True, grupo=grupo)
        form = NuevoGrupoForm(red=self.red_jovenes)

        self.assertNotIn(grupo.lideres.first(), form.fields['lideres'].queryset)
        self.assertIn(lider_sin_grupo, form.fields['lideres'].queryset)

    @skip
    def test_campo_lideres_solo_muestra_lideres_red_ingresada(self):
        """
        Prueba que el campo lideres solo muestra lideres que pertenecen a los grupos de la red ingresada.
        """

        grupo1 = Grupo.objects.get(id=300)
        lider_joven = MiembroFactory(lider=True, grupo=grupo1)

        grupo2 = Grupo.objects.get(id=400)
        otro_lider = MiembroFactory(lider=True, grupo=grupo2)

        form = NuevoGrupoForm(red=self.red_jovenes)

        self.assertIn(lider_joven, form.fields['lideres'].queryset)
        self.assertNotIn(otro_lider, form.fields['lideres'].queryset)

    @skip
    def test_campo_lideres_muestra_lideres_raiz_si_red_no_tiene_grupo(self):
        """
        Prueba que el campo lideres muestre los lideres disponibles que asisten al grupo raiz de una iglesia si la red
        ingresada no tiene ningún grupo.
        """

        raiz = Grupo.objects.get(id=100)
        otro = Grupo.objects.get(id=300)
        red_nueva = RedFactory(nombre='nueva red')
        miembro = MiembroFactory(lider=True, grupo=raiz)

        form = NuevoGrupoForm(red=red_nueva)

        self.assertIn(miembro, form.fields['lideres'].queryset)
        self.assertNotIn(otro.lideres.first(), form.fields['lideres'].queryset)

    def test_formulario_crea_grupo_y_se_asigna_a_lideres_escogidos(self):
        """
        Prueba que cuando se guarde el formulario se crea el grupo y es asignado a los lideres escogidos como grupo
        que lidera y el padre como grupo al que pertenecen.
        """

        form = NuevoGrupoForm(red=self.red_jovenes, data=self.datos_formulario())
        grupo = form.save()
        self.lider1.refresh_from_db()
        self.lider2.refresh_from_db()

        self.assertEqual(self.padre.get_children_count(), 1)
        self.assertEqual(grupo.red, self.red_jovenes)
        self.assertEqual(self.lider1.grupo_lidera, grupo)
        self.assertEqual(self.lider2.grupo_lidera, grupo)
        self.assertEqual(self.lider1.grupo, self.padre)
        self.assertEqual(self.lider2.grupo, self.padre)

    @mock.patch('django.db.models.query.QuerySet.update', side_effect=IntegrityError)
    def test_error_al_guardar_formulario_no_se_guarda_nada_en_db(self, update_mock):
        """
        Prueba que si ocurre un error al guardar el formulario no se guarde ni el grupo ni los lideres.
        """

        form = NuevoGrupoForm(red=self.red_jovenes, data=self.datos_formulario())
        form.save()
        self.lider1.refresh_from_db()
        self.lider2.refresh_from_db()

        self.assertTrue(update_mock.called)
        self.assertEqual(self.padre.get_children_count(), 0)
        self.assertEqual(self.lider1.grupo_lidera, None)
        self.assertEqual(self.lider2.grupo_lidera, None)

    @mock.patch('django.db.models.query.QuerySet.update', side_effect=IntegrityError)
    def test_error_al_guardar_formulario_agrega_error_form(self, update_mock):
        """
        Prueba que si ocurre un error al momento de guardar el formulario, se agregue un error al formulario.
        """

        form = NuevoGrupoForm(red=self.red_jovenes, data=self.datos_formulario())
        form.save()

        self.assertTrue(update_mock.called)
        self.assertEqual(len(form.non_field_errors()), 1)


class EditarGrupoFormTest(BaseTest):
    """
    Pruebas unitarias para el formulario de edición de grupos de una iglesia.
    """

    def setUp(self):
        self.crear_arbol()
        grupo3 = Grupo.objects.get(id=300)
        self.grupo = Grupo.objects.get(id=500)
        self.lider1 = MiembroFactory(lider=True, grupo=grupo3)
        self.lider2 = MiembroFactory(lider=True, grupo=grupo3)
        self.barrio = BarrioFactory()

    def datos_formulario(self):
        """
        Retorna un diccionario con datos para el formulario.
        """

        data = {
            'direccion': 'Calle 34 N 74 - 23', 'estado': 'IN', 'fechaApertura': '2012-03-03', 'diaGAR': '1',
            'horaGAR': '12:00', 'diaDiscipulado': '3', 'horaDiscipulado': '16:00', 'nombre': 'Pastor presidente',
            'barrio': self.barrio.id, 'lideres': [self.lider1.id, self.lider2.id]
        }

        return data

    def test_campo_lideres_muestra_lideres_del_grupo_escogido(self):
        """
        Prueba que en el campo lideres muestren los lideres del grupo que se esta editando.
        """

        form = EditarGrupoForm(instance=self.grupo)
        self.assertIn(self.grupo.lideres.first(), form.fields['lideres'].queryset)

    def test_formulario_edita_grupo(self):
        form = EditarGrupoForm(instance=self.grupo, data=self.datos_formulario())
        form.save()

        self.lider1.refresh_from_db()
        self.assertEqual(self.lider1.grupo_lidera, self.grupo)

    @mock.patch('django.db.models.query.QuerySet.update', side_effect=IntegrityError)
    def test_error_al_guardar_formulario_no_se_guarda_nada_en_db(self, update_mock):
        """
        Prueba que si ocurre un error al guardar el formulario no se guarde ni el grupo ni los lideres.
        """

        form = EditarGrupoForm(instance=self.grupo, data=self.datos_formulario())
        form.save()
        self.lider1.refresh_from_db()
        self.lider2.refresh_from_db()

        self.assertTrue(update_mock.called)
        self.assertEqual(self.lider1.grupo_lidera, None)
        self.assertEqual(self.lider2.grupo_lidera, None)

    @mock.patch('django.db.models.query.QuerySet.update', side_effect=IntegrityError)
    def test_error_al_guardar_formulario_agrega_error_form(self, update_mock):
        """
        Prueba que si ocurre un error al momento de guardar el formulario, se agregue un error al formulario.
        """

        form = EditarGrupoForm(instance=self.grupo, data=self.datos_formulario())
        form.save()

        self.assertTrue(update_mock.called)
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_grupo_no_cambia_grupo_padre(self):
        """"Prueba que el padre del grupo a editar no se modifique."""

        parent = self.grupo.parent_id
        form = EditarGrupoForm(instance=self.grupo, data=self.datos_formulario())
        grupo = form.save()

        self.assertEqual(grupo.parent_id, parent)

class TrasladarLideresFormTest(BaseTest):
    """
    Pruebas unitarias para el formulario usado para el traslado de lideres de un grupo a otro.
    """

    def setUp(self):
        self.crear_arbol()

    def datos_formulario(self):
        lideres = map(str, Grupo.objects.get(id=500).lideres.values_list('id', flat=True))
        return {'grupo': 500, 'lideres': list(lideres), 'nuevo_grupo': 800}

    def test_formulario_invalido_si_nuevo_grupo_es_descendiente_de_grupo(self):
        """
        Prueba que el formulario sea invalido si el nuevo grupo es descendiente del grupo escogido.
        """

        data = self.datos_formulario()
        data['nuevo_grupo'] = 600
        form = TrasladarLideresForm(data=data)

        self.assertFalse(form.is_valid(), msg="No se debe dejar trasladar lideres al grupo de un descendiente.")
        self.assertTrue(
            form.has_error('nuevo_grupo', code='es_descendiente'),
            msg="El error {} no es el esperado. Se espera {}".format(
                form.errors,
                form.error_messages['es_descendiente']
            )
        )


class ArchivarGrupoFormTest(BaseTest):
    """
    Pruebas para el formulario de archivar o eliminar un grupo.
    """

    def setUp(self):
        self.crear_arbol()
        self.form = ArchivarGrupoForm

    @property
    def datos_formulario(self):
        for children in Grupo.objects.get(id=300).children_set.all():
            children.actualizar_estado(estado=HistorialEstado.ARCHIVADO)

        return {
            'grupo': 300, 'grupo_destino': 200,
            'mantener_lideres': True, 'seleccionados': list(map(str, Grupo.objects.get(
                id=300).miembros.all().values_list('id', flat=1)))
        }

    def test_formulario_invalido_si_seleccionados_y_no_grupo_destino(self):
        """
        Verifica que el formulario retorne error si no se envia un grupo de destino,
        pero sí se escogen seleccionados.
        """

        datos = self.datos_formulario
        datos.update({'grupo_destino': None})
        form = self.form(data=datos)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('grupo_destino', code='sin_destino'))

    def test_miembros_seleccionados_son_miembros_de_grupo(self):
        """
        Verifica que los miembros seleccionados, siempre sean discipulos o miembros del Grupo
        escogido.
        """

        data = self.datos_formulario
        data.update(
            {'seleccionados': list(map(str, Grupo.objects.get(id=100).miembros.all().values_list('id', flat=1)))}
        )

        form = self.form(data=data)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('seleccionados'))

    def test_grupo_es_archivado_existosamente(self):
        """
        Verifica que el grupo escogido, sea archivado.
        """

        form = self.form(data=self.datos_formulario)

        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data['grupo'].estado, HistorialEstado.ACTIVO)

        form.archiva_grupo()

        self.assertTrue(form.cleaned_data['grupo'].estado, HistorialEstado.ARCHIVADO)

    def test_lideres_grupo_pasan_a_grupo_padre_si_mantenter_lideres(self):
        """
        Verifica que al escoger la opcion de mantener lideres, los lideres sigan siendo miembros
        del grupo padre.
        """

        form = self.form(data=self.datos_formulario)

        self.assertTrue(form.is_valid())

        grupo_padre = form.cleaned_data['grupo'].get_parent()
        lideres = form.cleaned_data['grupo'].lideres.all()

        form.archiva_grupo()

        for lider in lideres:
            self.assertEqual(lider.grupo, grupo_padre)

    def test_lideres_grupo_quedan_sin_grupo_si_no_mantener_lideres(self):
        """
        Verifica que los lideres de grupo queden sin grupo si no se escoge la opcion de mantener lideres.
        """

        data = self.datos_formulario
        data.pop('mantener_lideres')
        form = self.form(data=data)

        self.assertTrue(form.is_valid())

        lideres = form.cleaned_data['grupo'].lideres.all()
        form.archiva_grupo()

        for lider in lideres:
            lider.refresh_from_db()
            self.assertIsNone(lider.grupo)

    def test_miembros_grupo_grupo_destino(self):
        """
        Verifica que los miembros del grupo, vayan al grupo de destino
        """

        datos = self.datos_formulario
        form = self.form(data=datos)

        self.assertTrue(form.is_valid())

        form.archiva_grupo()

        for miembro in datos['seleccionados']:
            self.assertIn(
                int(miembro),
                form.cleaned_data['grupo_destino'].miembros.all().values_list('id', flat=1)
            )

    def test_miembros_grupo_grupo_destino_es_none(self):
        """
        Verifica que si no hay seleccionados, los miembros queden sin grupo
        """

        datos = self.datos_formulario
        datos.pop('seleccionados')
        datos.pop('grupo_destino')
        form = self.form(data=datos)

        self.assertTrue(form.is_valid())

        miembros = list(form.cleaned_data['grupo'].miembros.all())
        form.archiva_grupo()

        for miembro in miembros:
            miembro.refresh_from_db()
            self.assertIsNone(miembro.grupo)

    def test_error_si_grupo_destino_igual_a_grupo_a_eliminar(self):
        """
        Verifica que se lance un error cuando el grupo de destino es igual al grupo a eliminar.
        """

        data = self.datos_formulario
        data.update({'grupo_destino': self.datos_formulario['grupo']})
        form = self.form(data=data)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('grupo_destino', code='mismo_grupo'))

    def test_parametro_all_no_falle_en_el_formulario(self):
        """
        Verifica que cuando en el data se envia el parametro 'all' en 'seleccionados',
        el formulario lo omita, y no arroje error. (Se sobreescribe el método full_clean).
        """

        class DictWrapper(dict):
            """
            Wrapper para dict, en el cual se agrega el metodo getlist,
            para simular la peticion de Django en request.POST.
            """
            def getlist(self, selector):
                return self[selector]

        data = DictWrapper(self.datos_formulario)
        data['seleccionados'] += ['all', ]

        form = self.form(data=data)

        self.assertTrue(form.is_valid())


class ReportarReunionDiscipuladoAdminFormTest(BaseTest):
    """Pruebas unitarias para el formulario de ingreso de sobres de discipulado por parte de un admin."""

    def datos_formulario(self):
        self.predica = PredicaFactory()
        self.grupo = GrupoFactory()
        hijo = GrupoHijoFactory(parent=self.grupo)
        return {
            'ofrenda': 10000, 'novedades': 'novedades', 'predica': self.predica.pk,
            'grupo': self.grupo.pk, 'asistencia': self.grupo.discipulos.values_list('id', flat=True)
        }

    @mock.patch('grupos.managers.GrupoQuerySet.pueden_reportar_discipulado') 
    def test_campo_grupo_solo_muestra_grupos_que_pueden_reportar_discipulado(self, pueden_reportar_discipulado_mock):
        """Prueba que solo haya grupos que puedan dictar discipulado."""

        form = ReportarReunionDiscipuladoAdminForm(mock.create_autospec(Miembro, instance=True))
        self.assertTrue(pueden_reportar_discipulado_mock.called)

    @mock.patch('grupos.managers.GrupoManager.disponibles_ver', autospec=True)
    def test_campo_grupo_muestra_grupos_que_puede_ver_el_miembro(self, mock_disponibles_ver):
        """Prueba que el campo grupo muestre solo los grupos que el miembro pueda ver."""

        form = ReportarReunionDiscipuladoAdminForm(mock.create_autospec(Miembro, instance=True))
        self.assertTrue(mock_disponibles_ver.called)

    def test_campo_grupo_no_vacio_asistencia_permita_discipulos_del_grupo_escogido(self):
        """Prueba que si el campo grupo no se encuentra vacio, el campo asistencia permita los discipulos
        del grupo escogido."""

        form = ReportarReunionDiscipuladoAdminForm(mock.create_autospec(Miembro, instance=True), data=self.datos_formulario())
        self.assertTrue(form.is_valid())
    
    @mock.patch('grupos.forms.ReunionDiscipulado.objects.reportar_reunion', autospec=True)
    def test_save_calls_reportar_reunion(self, mock_reportar_reunion):

        form = ReportarReunionDiscipuladoAdminForm(mock.create_autospec(Miembro, instance=True), data=self.datos_formulario())
        form.is_valid()
        form.save()

        self.assertTrue(mock_reportar_reunion.called)
    
    @mock.patch('grupos.forms.ReunionDiscipulado.objects.reportar_reunion', autospec=True, side_effect=ReunionDiscipulado.MultipleObjectsReturned)
    def test_save_shows_error_if_multiple_objects_found(self, mock_reportar_reunion):

        form = ReportarReunionDiscipuladoAdminForm(mock.create_autospec(Miembro, instance=True), data=self.datos_formulario())
        form.is_valid()
        form.save()

        self.assertTrue(form.has_error(NON_FIELD_ERRORS))