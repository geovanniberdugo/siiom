import datetime
from unittest import mock
from freezegun import freeze_time
from django.test import tag
from common.tests.base import BaseTest
from miembros.tests.factories import MiembroFactory
from ..models import Grupo, HistorialEstado, ReunionGAR, Predica, ReunionDiscipulado, AsistenciaDiscipulado
from .factories import (
    GrupoRaizFactory, GrupoFactory, RedFactory, ReunionGARFactory, GrupoHijoFactory,
    ReunionDiscipuladoFactory, HistorialEstadoFactory, PredicaFactory, AsistenciaDiscipuladoFactory
)


class GrupoManagerTest(BaseTest):
    """
    Pruebas unitarias para el manager de grupos.
    """

    def test_obtener_raiz_arbol(self):
        """
        Prueba que el grupo obtenido sea la raiz del arbol.
        """

        raiz = GrupoRaizFactory()
        GrupoFactory(parent=raiz)

        raiz_obtenida = Grupo.objects.raiz()
        self.assertEqual(raiz_obtenida, raiz)

    def test_no_hay_raiz_arbol_devuelva_none(self):
        """
        Prueba que si no hay grupo raiz en la iglesia en el arbol de grupos, devuelva None.
        """

        raiz_obtenida = Grupo.objects.raiz()
        self.assertIsNone(raiz_obtenida)

    def test_red_devuelve_grupos_correctos(self):
        """
        Prueba que los grupos obtenidos pertenezcan a la red ingresada.
        """

        red_jovenes = RedFactory()
        grupo_jovenes = GrupoFactory()
        otra_red = RedFactory(nombre='adultos')
        otro_grupo = GrupoFactory(red=otra_red)

        grupos = Grupo.objects.red(red_jovenes)

        self.assertIn(grupo_jovenes, grupos)
        self.assertNotIn(otro_grupo, grupos)

    def test_devuelve_grupo_sin_confirmar_ofrenda_GAR(self):
        """
        Prueba que devuelve el grupo que falta por confirmar ofrenda reunion GAR.
        """

        sin_confirmar = ReunionGARFactory()
        confirmada = ReunionGARFactory(confirmacionEntregaOfrenda=True)

        grupos = Grupo.objects.sin_confirmar_ofrenda_GAR()

        self.assertIn(sin_confirmar.grupo, grupos)
        self.assertNotIn(confirmada.grupo, grupos)

    def test_devuelve_grupo_sin_confirmar_ofrenda_GAR_una_sola_vez(self):
        """
        Prueba que devuleva el grupos que falta por confirmar ofrenda reunión GAR una sola vez aunque deba confirmar
        mas de una ofrenda.
        """

        sin_confirmar = ReunionGARFactory()
        ReunionGARFactory(grupo=sin_confirmar.grupo)

        grupos = Grupo.objects.sin_confirmar_ofrenda_GAR()

        self.assertEqual(grupos.count(), 1)

    def test_devuelve_grupo_sin_confirmar_ofrenda_discipulado(self):
        """
        Prueba que devuelve el grupo que falta por confirmar ofrenda reunion discipulado.
        """

        sin_confirmar = ReunionDiscipuladoFactory()
        confirmada = ReunionDiscipuladoFactory(confirmacionEntregaOfrenda=True)

        grupos = Grupo.objects.sin_confirmar_ofrenda_discipulado()

        self.assertIn(sin_confirmar.grupo, grupos)
        self.assertNotIn(confirmada.grupo, grupos)

    def test_devuelve_grupo_sin_confirmar_ofrenda_discipulado_una_sola_vez(self):
        """
        Prueba que devuleva el grupos que falta por confirmar ofrenda reunión discipulado una sola vez aunque deba
        confirmar mas de una ofrenda.
        """

        sin_confirmar = ReunionDiscipuladoFactory()
        ReunionDiscipuladoFactory(grupo=sin_confirmar.grupo)

        grupos = Grupo.objects.sin_confirmar_ofrenda_discipulado()

        self.assertEqual(grupos.count(), 1)

    def test_hojas_devuelve_grupos_sin_descendientes(self):
        """
        Verifica que hojas solo devuelva grupos que no tengan descendientes.
        """

        self.crear_arbol()
        queryset = Grupo.objects.hojas()

        self.assertNotIn(Grupo.objects.get(id=100), queryset)
        self.assertIn(Grupo.objects.get(id=200), queryset)
        self.assertNotIn(Grupo.objects.get(id=300), queryset)
        self.assertNotIn(Grupo.objects.get(id=400), queryset)
        self.assertNotIn(Grupo.objects.get(id=500), queryset)
        self.assertIn(Grupo.objects.get(id=600), queryset)
        self.assertIn(Grupo.objects.get(id=700), queryset)
        self.assertIn(Grupo.objects.get(id=800), queryset)

        g = Grupo.objects.get(id=700)
        g.actualizar_estado(estado=HistorialEstado.ARCHIVADO)

        self.assertIn(Grupo.objects.get(id=400), Grupo.objects.hojas())

    def test_annotate_estado_agrega_grupos_su_estado(self):
        grupo1 = GrupoFactory()
        grupo1.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)

        grupos = Grupo.objects.annotate_estado()
        self.assertTrue(hasattr(grupos[0], 'estado_anotado'))

    def test_annotate_estado_agrega_grupos_su_estado_actual(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)
        grupo.actualizar_estado(estado=HistorialEstado.ACTIVO)

        grupos = Grupo.objects.annotate_estado()
        self.assertEqual(grupos[0].estado_anotado, HistorialEstado.ACTIVO)

    def test_annotate_estado_agrega_grupo_el_estado_fecha_indicada(self):
        """Prueba que el estado que se el ultimo que tuvo el grupo hasta la fecha indicada."""

        grupo = GrupoFactory()
        with freeze_time("2017-12-15"):
            HistorialEstadoFactory(grupo=grupo, estado=HistorialEstado.INACTIVO, fecha=datetime.datetime.now())
        
        with freeze_time("2017-12-30"):
            grupos = Grupo.objects.annotate_estado(fecha=datetime.datetime.now())
        self.assertEqual(grupos[0].estado_anotado, HistorialEstado.INACTIVO)

    @mock.patch('grupos.managers.GrupoQuerySet.annotate_estado', autospec=True)
    def test_default_queryset_annotates_estado(self, mock_annotate_estado):
        Grupo.objects.all()
        self.assertTrue(mock_annotate_estado.called)

    def test_activos_devuelve_grupos_con_estado_activo_actual(self):
        grupo = GrupoFactory()

        self.assertIn(grupo, Grupo.objects.activos())
    
    def test_activos_no_devuelve_grupos_con_estado_diferente(self):
        grupo1 = GrupoFactory()
        grupo2 = GrupoFactory()
        grupo3 = GrupoFactory()
        grupo1.actualizar_estado(estado=HistorialEstado.ARCHIVADO)
        grupo2.actualizar_estado(estado=HistorialEstado.INACTIVO)
        grupo3.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)

        self.assertEqual(Grupo.objects.activos().count(), 0)
    
    def test_inactivos_devuelve_grupos_con_estado_inactivo_actual(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.INACTIVO)

        self.assertIn(grupo, Grupo.objects.inactivos())
    
    def test_inactivos_no_devuelve_grupos_con_estado_diferente(self):
        grupo1 = GrupoFactory()
        grupo2 = GrupoFactory()
        grupo3 = GrupoFactory()
        grupo2.actualizar_estado(estado=HistorialEstado.ARCHIVADO)
        grupo3.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)

        self.assertEqual(Grupo.objects.inactivos().count(), 0)
    
    def test_suspendidos_devuelve_grupos_con_estado_suspendido_actual(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)

        self.assertIn(grupo, Grupo.objects.suspendidos())
    
    def test_suspendidos_no_devuelve_grupos_con_estado_diferente(self):
        grupo1 = GrupoFactory()
        grupo2 = GrupoFactory()
        grupo3 = GrupoFactory()
        grupo2.actualizar_estado(estado=HistorialEstado.ARCHIVADO)
        grupo3.actualizar_estado(estado=HistorialEstado.INACTIVO)

        self.assertEqual(Grupo.objects.suspendidos().count(), 0)
    
    def test_archivados_devuelve_grupos_con_estado_archivado_actual(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.ARCHIVADO)

        self.assertIn(grupo, Grupo.objects.archivados())
    
    def test_archivados_no_devuelve_grupos_con_estado_diferente(self):
        grupo1 = GrupoFactory()
        grupo2 = GrupoFactory()
        grupo3 = GrupoFactory()
        grupo2.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)
        grupo3.actualizar_estado(estado=HistorialEstado.INACTIVO)

        self.assertEqual(Grupo.objects.archivados().count(), 0)
    
    def test_no_archivados(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.ARCHIVADO)

        self.assertNotIn(grupo, Grupo.objects.no_archivados())
    
    def test_no_activos(self):
        grupo = GrupoFactory()

        self.assertNotIn(grupo, Grupo.objects.no_activos())
    
    def test_no_inactivos(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.INACTIVO)

        self.assertNotIn(grupo, Grupo.objects.no_inactivos())
    
    def test_no_suspendidos(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)

        self.assertNotIn(grupo, Grupo.objects.no_suspendidos())

    def test_grupos_archivados_not_in_queryset_objects(self):
        """
        Prueba que los grupos en estado archivado no esten saliendo en queryset de objects
        """

        self.crear_arbol()
        grupo = Grupo.objects.get(id=500)

        self.assertIn(grupo, Grupo.objects.all())

        grupo.actualizar_estado(
            estado=HistorialEstado.ARCHIVADO, fecha=grupo.fechaApertura + datetime.timedelta(weeks=5)
        )

        self.assertNotIn(grupo, Grupo.objects.all())
        self.assertIn(grupo, Grupo._objects.all())

    def test_declarar_vacaciones_crea_reuniones_como_realizada(self):
        """Prueba que cuando se declaren los grupos en vacaciones se coloquen las reuniones en las fechas escogidas como
        que no realizo grupo."""

        with freeze_time("2017-12-15"):
            now = datetime.datetime.now()
            grupo1 = GrupoFactory(fechaApertura=now, historial__fecha=now)
        with freeze_time("2017-12-18"):
            dic_18 = datetime.date.today()
        with freeze_time("2017-12-31"):
            dic_31 = datetime.date.today()
        
        Grupo.objects.declarar_vacaciones(dic_18, dic_31)
        self.assertFalse(
            all([r.realizada for r in grupo1.reuniones_gar.all()]),
            msg="Las reuniones debieron ser creadas como no realizadas."
        )

    def test_declarar_vacaciones_crea_todas_reuniones_dentro_rango_fechas(self):
        """
        Prueba que cuando se declaren los grupos en vacaciones se coloquen todas las reuniones dentro del rango de
        fechas dadas.
        """

        with freeze_time("2017-12-15"):
            now = datetime.datetime.now()
            grupo1 = GrupoFactory(fechaApertura=now, historial__fecha=now)
        
        with freeze_time("2017-12-18"):
            dic_18 = datetime.date.today()
        with freeze_time("2017-12-31"):
            dic_31 = datetime.date.today()
        
        Grupo.objects.declarar_vacaciones(dic_18, dic_31)
        self.assertEqual(
            grupo1.reuniones_gar.count(), 2,
            msg="Debido al que el rango de fechas son dos semanas, solo deben haber reuniones."
        )
    
    def test_declarar_vacaciones_solo_grupos_activos(self):
        """
        Prueba que solo se creen reuniones para grupos activos.
        """

        with freeze_time("2017-12-13"):
            now = datetime.datetime.now()
            grupo1 = GrupoFactory(fechaApertura=now)
            grupo2 = GrupoFactory(fechaApertura=now)
            grupo3 = GrupoFactory(fechaApertura=now)
        
        with freeze_time("2017-12-14"):
            grupo1.actualizar_estado('IN')
            grupo2.actualizar_estado('SU')
            grupo3.actualizar_estado('AR')
        
        with freeze_time("2017-12-18"):
            dic_18 = datetime.date.today()
        with freeze_time("2017-12-31"):
            dic_31 = datetime.date.today()
        
        Grupo.objects.declarar_vacaciones(dic_18, dic_31)
        self.assertEqual(ReunionGAR.objects.count(), 0, msg="No debe haber ninguna reunion creada")
    
    def test_declarar_vacaciones_no_cree_reporte_si_grupo_ya_reporto(self):
        """
        Prueba que no se cree un reporte si el grupo ya reporto.
        """

        with freeze_time("2017-12-13"):
            grupo = GrupoFactory(fechaApertura=datetime.datetime.now())
        
        with freeze_time("2017-12-20"):
            reunion = ReunionGARFactory(grupo=grupo, fecha=datetime.datetime.now())
        
        with freeze_time("2017-12-18"):
            dic_18 = datetime.date.today()
        with freeze_time("2017-12-31"):
            dic_31 = datetime.date.today()
        
        Grupo.objects.declarar_vacaciones(dic_18, dic_31)
        self.assertEqual(ReunionGAR.objects.exclude(id=reunion.id).count(), 1, msg="Solo se debio crear una sola reunion")

    def test_devuelve_grupo_sin_reportar_reunion_GAR(self):
        """Prueba que devuelva el grupo que no ha reportado reunion GAR en el rango de fecha ingresado."""

        grupo = GrupoFactory()        
        with freeze_time("2018-01-01"):
            ene_01 = datetime.date.today()
        with freeze_time("2018-01-07"):
            ene_07 = datetime.date.today()

        grupos = Grupo.objects.sin_reportar_reunion_GAR(ene_01, ene_07)
        self.assertTrue(
            grupos.filter(id=grupo.id).exists(),
            msg="El grupo {0} no ha reportado reunion por lo tanto debe ser True.".format(grupo.id)
        )

    def test_no_devuelve_grupo_que_reporto_reunion_GAR(self):
        """Prueba que no devuelva el grupo que reporto reunion GAR en el rango de fecha ingresado."""

        GrupoFactory()
        grupo = GrupoFactory()
        with freeze_time("2018-01-03"):
            reunion = ReunionGARFactory(fecha=datetime.date.today(), grupo=grupo)
        
        with freeze_time("2018-01-01"):
            ene_01 = datetime.date.today()
        with freeze_time("2018-01-07"):
            ene_07 = datetime.date.today()

        grupos = Grupo.objects.sin_reportar_reunion_GAR(ene_01, ene_07)
        self.assertFalse(
            grupos.filter(id=grupo.id).exists(),
            msg="El grupo {0} ya reporto reunion por lo tanto debe ser False.".format(grupo.id)
        )

    def test_sin_reportar_reunion_GAR_no_devuelva_grupos_si_no_hay_grupos_activos(self):
        """Prueba que no devuelva ningún grupo si no hay grupos activos."""

        with freeze_time("2017-12-13"):
            now = datetime.datetime.now()
            grupo1 = GrupoFactory(fechaApertura=now)
            grupo2 = GrupoFactory(fechaApertura=now)
            grupo3 = GrupoFactory(fechaApertura=now)
        
        with freeze_time("2017-12-14"):
            grupo1.actualizar_estado('IN')
            grupo2.actualizar_estado('SU')
            grupo3.actualizar_estado('AR')
        
        with freeze_time("2018-01-01"):
            ene_01 = datetime.date.today()
        with freeze_time("2018-01-07"):
            ene_07 = datetime.date.today()


        grupos = Grupo.objects.sin_reportar_reunion_GAR(ene_01, ene_07)
        self.assertEqual(grupos.count(), 0)
    
    def test_pueden_reportar_discipulado_devuelve_grupos_con_hijos(self):
        """Prueba que me devuelva grupos que tengan por lo menos un hijo."""

        self.crear_arbol()
        
        grupos = Grupo.objects.pueden_reportar_discipulado()
        self.assertIn(Grupo.objects.get(id=100), grupos)
        self.assertIn(Grupo.objects.get(id=500), grupos)
    
    def test_pueden_reportar_discipulado_no_devuelve_grupos_sin_hijos(self):
        """Prueba que no devuelva grupos que no tengan hijos."""

        self.crear_arbol()

        grupos = Grupo.objects.pueden_reportar_discipulado()
        self.assertNotIn(Grupo.objects.get(id=700), grupos)
    
    def test_pueden_reportar_discipulado_no_devuelve_grupos_suspendidos(self):
        """Prueba que no devuelva grupos que tengan hijos pero que se encuentran en estado suspendido."""

        self.crear_arbol()
        suspendido = Grupo.objects.get(id=500)
        suspendido.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)

        grupos = Grupo.objects.pueden_reportar_discipulado()
        self.assertNotIn(suspendido, grupos)
    
    def test_pueden_reportar_discipulado_no_duvuelve_grupos_con_un_solo_hijo_archivado(self):
        """Prueba que no devuelva grupos que tengan un solo hijo y este se encuentre archivado."""

        self.crear_arbol()
        Grupo.objects.get(id=700).actualizar_estado(estado=HistorialEstado.ARCHIVADO)

        grupos = Grupo.objects.pueden_reportar_discipulado()
        self.assertNotIn(Grupo.objects.get(id=400), grupos)
    
    def test_disponibles_ver_retorna_todos_grupos_si_admin(self):
        """Prueba que se devuelvan todos los grupos si el miembro es un administrador."""

        admin = MiembroFactory(admin=True)
        GrupoFactory()
        GrupoFactory()

        num_grupos = Grupo.objects.disponibles_ver(admin).count()
        self.assertEqual(num_grupos, 2, msg="Debe devolver todos los grupos")
    
    def test_disponibles_ver_retorna_grupos_de_subred_miembro_si_no_admin(self):
        """Prueba que devuelva grupos de la subred del miembro si este no es admin."""

        grupo = GrupoFactory()
        grupo1 = GrupoHijoFactory(parent=grupo)
        miembro = MiembroFactory(lider=True, grupo_lidera=grupo)

        grupos = Grupo.objects.disponibles_ver(miembro)
        self.assertIn(grupo1, grupos)

    def test_disponibles_ver_no_retorna_grupos_no_son_subred_miembro_si_no_admin(self):
        """Prueba que no devuelva grupos que no pertenezcan a la subred del miembro si este no es admin."""

        grupo = GrupoFactory()
        grupo1 = GrupoFactory()
        miembro = MiembroFactory(lider=True, grupo_lidera=grupo)

        grupos = Grupo.objects.disponibles_ver(miembro)
        self.assertNotIn(grupo1, grupos)
    
    def test_disponibles_no_retorna_grupos_si_miembro_no_lidera_grupo_no_admin(self):
        """Prueba que no devuelva grupos si miembro no lidera grupo y no es admin."""

        miembro = MiembroFactory(lider=True)

        grupos = Grupo.objects.disponibles_ver(miembro)
        self.assertEqual(grupos.count(), 0)

    def test_faltantes_reportar_discipulado_retorne_grupo_que_no_ingresado_reporte_para_predica(self):
        """Prueba que si el grupo no ha ingresado el reporte aparezca en la lista."""

        grupo = GrupoFactory()
        GrupoHijoFactory(parent=grupo)
        predica = PredicaFactory()
        
        grupos = Grupo.objects.faltantes_reportar_discipulado(predica)
        self.assertIn(grupo, grupos)
    
    def test_faltantes_reportar_discipulado_no_retorne_grupo_que_ingreso_reporte_para_predica(self):
        """Prueba que si el grupo ya ingreso el reporte no aparezca en la lista."""

        grupo = GrupoFactory()
        GrupoHijoFactory(parent=grupo)
        predica = PredicaFactory()
        ReunionDiscipuladoFactory(grupo=grupo, predica=predica)
        
        grupos = Grupo.objects.faltantes_reportar_discipulado(predica)
        self.assertNotIn(grupo, grupos)
    
    @mock.patch('grupos.managers.GrupoQuerySet.pueden_reportar_discipulado')
    def test_faltantes_reportar_discipulado_solo_muestra_grupos_que_pueden_reportar(self, method_mock):
        """Prueba que solo se muestren los grupos que pueden reportar discipulado."""

        Grupo.objects.faltantes_reportar_discipulado(PredicaFactory())
        self.assertTrue(method_mock.called)

class PredicaManagerTest(BaseTest):
    """Pruebas unitarias para el manager de predicas."""

    def test_disponibles_retorna_todas_predicas_si_admin(self):
        """"Prueba que se devuelvan todas las predicas si el usuario es un administrador."""

        admin = MiembroFactory(admin=True)
        PredicaFactory(nombre='Otra predica')
        PredicaFactory()

        num_predicas = Predica.objects.disponibles(admin).count()
        self.assertEqual(num_predicas, 2, msg="Debe devolver todas las predicas")
    
    def test_disponibles_retorna_predicas_pastores_arriba_sino_admin(self):
        """
        Prueba que se devuelvan solo predicas dictadas por pastores que se encuentren por encima del miembro
        sino este no es admin.
        """

        grupo1 = GrupoFactory()
        grupo2 = GrupoHijoFactory(parent=grupo1)
        grupo3 = GrupoHijoFactory(parent=grupo1)
        grupo4 = GrupoHijoFactory(parent=grupo2)

        pastor = MiembroFactory(lider_pastor=True, grupo_lidera=grupo2)
        predica = PredicaFactory(miembro=pastor)

        miembro = grupo4.lideres.first()
        predicas = Predica.objects.disponibles(miembro)

        self.assertIn(predica, predicas)

    def test_disponibles_no_retorna_predicas_pastores_no_arriba_miembro_sino_admin(self):
        """
        Prueba que no devuelva predicas dictadas por pastores que no se encuentren por encima del miembro
        si este no es admin.
        """

        grupo1 = GrupoFactory()
        grupo2 = GrupoHijoFactory(parent=grupo1)
        grupo3 = GrupoHijoFactory(parent=grupo1)
        grupo4 = GrupoHijoFactory(parent=grupo2)

        pastor = MiembroFactory(lider_pastor=True, grupo_lidera=grupo2)
        predica = PredicaFactory(miembro=pastor)

        miembro = grupo3.lideres.first()
        predicas = Predica.objects.disponibles(miembro)

        self.assertNotIn(predica, predicas)


class ReunionDiscipuladoManagerTest(BaseTest):
    """Pruebas unitarias para el manager reunion discipulado."""

    def test_reportar_reunion_si_reunion_no_existe_crea_nueva(self):
        """Prueba que si la reunion para el grupo y predica ingresada no existe se cree nueva."""

        grupo = GrupoFactory()
        predica = PredicaFactory()
        miembro = MiembroFactory(lider=True, grupo=grupo)

        ReunionDiscipulado.objects.reportar_reunion(
            grupo=grupo, predica=predica, novedades='novedad', ofrenda=20000, asistentes=[miembro]
        )

        self.assertEqual(ReunionDiscipulado.objects.count(), 1, msg="Debe existir una reunion en la bd")
        self.assertEqual(AsistenciaDiscipulado.objects.count(), 1, msg="Debe existir una asistencia en la bd")

    def test_reportar_reunion_si_reunion_no_existe_indique_fue_creada(self):
        """Prueba que si la reunion para la predica y grupo ingresados no existe indique que la reunion fue creada."""

        grupo = GrupoFactory()
        predica = PredicaFactory()
        miembro = MiembroFactory(lider=True, grupo=grupo)

        _, created = ReunionDiscipulado.objects.reportar_reunion(
            grupo=grupo, predica=predica, novedades='novedad', ofrenda=20000, asistentes=[miembro]
        )

        self.assertTrue(created, msg="Se debio crear la reunión")
    
    def test_reportar_reunion_si_reunion_existe_no_cree_nueva_reunion(self):
        reunion = ReunionDiscipuladoFactory()
        asistencia = AsistenciaDiscipuladoFactory(reunion=reunion)

        ReunionDiscipulado.objects.reportar_reunion(
            grupo=reunion.grupo, predica=reunion.predica, novedades='novedades', ofrenda=20000,
            asistentes=[asistencia.miembro]
        )

        self.assertEqual(ReunionDiscipulado.objects.count(), 1, msg="No se debio crear nueva reunion")
        self.assertEqual(AsistenciaDiscipulado.objects.count(), 1, msg="No se debio crear nueva asistencia")

    def test_reportar_reunion_si_reunion_existe_no_indique_fue_actualizada(self):
        reunion = ReunionDiscipuladoFactory()
        asistencia = AsistenciaDiscipuladoFactory(reunion=reunion)

        r, created = ReunionDiscipulado.objects.reportar_reunion(
            grupo=reunion.grupo, predica=reunion.predica, novedades='novedades', ofrenda=20000,
            asistentes=[asistencia.miembro]
        )

        self.assertFalse(created, msg="Debio ser actualizada no creada")
        self.assertEqual(r.ofrenda, 20000)