import datetime
from unittest import mock
from django.test import tag
from freezegun import freeze_time
from miembros.tests.factories import MiembroFactory
from common.tests.base import BaseTest
from ..models import Grupo, HistorialEstado, ReunionGAR
from .factories import ReunionGARFactory, ReunionDiscipuladoFactory, GrupoHijoFactory, GrupoFactory, PredicaFactory


class GrupoModelTest(BaseTest):
    """
    Pruebas unitarias para el modelo Grupo.
    """

    def setUp(self):
        self.crear_arbol()

    def test_obtener_arbol_no_hay_raiz_devuelve_lista_vacio(self):
        """
        Prueba que si no existe raiz en el arbol de grupos, devuelva una lista vacía.
        """

        Grupo.objects.all().delete()
        lista_obtenida = Grupo.obtener_arbol()
        self.assertListEqual(lista_obtenida, [])

    def test_obtener_arbol_completo(self):
        """
        Prueba que la lista obtenida sea igual a la lista del arbol completo.
        """

        lista_obtenida = Grupo.obtener_arbol()
        self.assertListEqual(lista_obtenida, self.lista_arbol_completo)

    def test_obtener_arbol_padre_especifico(self):
        """
        Prueba que la lista obtenida sea igual a la lista del arbol de un padre especifico.
        """

        cb2 = Grupo.objects.get(id=300)
        lista_obtenida = Grupo.obtener_arbol(cb2)
        self.assertListEqual(lista_obtenida, self.lista_arbol_cb2)

    def test_obtener_ruta(self):
        """
        Prueba que la lista obtenida sea igual a la lista de ruta.
        """

        ruta = Grupo.objects.filter(id__in=[300, 500, 600]).order_by('id')
        ruta_obtenida = Grupo.obtener_ruta(ruta[0], ruta[2])

        self.assertListEqual(ruta_obtenida, list(ruta))

    def test_trasladar_grupo_mismo_padre(self):
        """
        Prueba que cuando se quiere trasladar un grupo al mismo padre no se cambie el grupo padre.
        """

        grupo = Grupo.objects.get(id=500)
        padre = grupo.get_parent()

        grupo.trasladar(padre)
        self.assertEqual(grupo.get_parent(), padre)

    def test_trasladar_grupo_mueve_lideres_grupo_pertenecen(self):
        """
        Prueba que cuando se traslada un grupo a un nuevo padre, tambien se modifica el grupo al que pertenecen los
        lideres del grupo que se esta transladando.
        """

        grupo = Grupo.objects.get(id=500)
        nuevo_padre = Grupo.objects.get(id=800)

        grupo.trasladar(nuevo_padre)
        self.assertTrue(all(lider.grupo == nuevo_padre for lider in grupo.lideres.all()))

    def test_trasladar_grupo_red(self):
        """
        Prueba que cuando se traslada un grupo a un nuevo padre que se encuentre en otra red, el grupo y todos
        sus descendientes se mueven a la nueva red.
        """

        grupo = Grupo.objects.get(id=500)
        nuevo_padre = Grupo.objects.get(id=200)

        grupo.trasladar(nuevo_padre)
        grupo.refresh_from_db()
        self.assertEqual(grupo.red, nuevo_padre.red)
        self.assertTrue(all(descendiente.red == nuevo_padre.red for descendiente in grupo.get_descendants()))

    def test_discipulos_devuelve_solo_miembros_grupo_son_lideres(self):
        """
        Prueba que los discipulos obtenidos son los miembros del grupo que son lideres.
        """

        grupo = Grupo.objects.get(id=300)
        miembro = MiembroFactory(grupo=grupo)
        lider = Grupo.objects.get(id=500).lideres.first()
        otro_lider = Grupo.objects.get(id=200).lideres.first()

        discipulos = list(grupo.discipulos)

        self.assertIn(lider, discipulos)
        self.assertNotIn(miembro, discipulos)
        self.assertNotIn(otro_lider, discipulos)

    def test_reunion_GAR_sin_ofrenda_confirmada(self):
        """
        Prueba que devuelva las reuniones GAR a las cuales no se les haya confirmado la ofrenda.
        """

        grupo = Grupo.objects.get(id=200)
        confirmada = ReunionGARFactory(grupo=grupo, confirmacionEntregaOfrenda=True)
        no_confirmada = ReunionGARFactory(grupo=grupo, confirmacionEntregaOfrenda=False)

        reuniones = grupo.reuniones_GAR_sin_ofrenda_confirmada
        self.assertIn(no_confirmada, reuniones)
        self.assertNotIn(confirmada, reuniones)

    def test_confirmar_ofrenda_GAR(self):
        """
        Prueba que se confirmen la ofrenda de las reuniones GAR ingresadas.
        """

        grupo = Grupo.objects.get(id=200)
        no_confirmada1 = ReunionGARFactory(grupo=grupo)
        no_confirmada2 = ReunionGARFactory(grupo=grupo)

        grupo.confirmar_ofrenda_reuniones_GAR([no_confirmada1.id])
        no_confirmada1.refresh_from_db()
        no_confirmada2.refresh_from_db()

        self.assertTrue(no_confirmada1.confirmacionEntregaOfrenda)
        self.assertFalse(no_confirmada2.confirmacionEntregaOfrenda)

    def test_reunion_discipulado_sin_ofrenda_confirmada(self):
        """
        Prueba que devuelva las reuniones de discipulado a las cuales no se les haya confirmado la ofrenda.
        """

        grupo = Grupo.objects.get(id=200)
        confirmada = ReunionDiscipuladoFactory(grupo=grupo, confirmacionEntregaOfrenda=True)
        no_confirmada = ReunionDiscipuladoFactory(grupo=grupo, confirmacionEntregaOfrenda=False)

        reuniones = grupo.reuniones_discipulado_sin_ofrenda_confirmada
        self.assertIn(no_confirmada, reuniones)
        self.assertNotIn(confirmada, reuniones)

    def test_confirmar_ofrenda_discipulado(self):
        """
        Prueba que se confirmen la ofrenda de las reuniones de discipulado ingresadas.
        """

        grupo = Grupo.objects.get(id=200)
        no_confirmada1 = ReunionDiscipuladoFactory(grupo=grupo)
        no_confirmada2 = ReunionDiscipuladoFactory(grupo=grupo)

        grupo.confirmar_ofrenda_reuniones_discipulado([no_confirmada1.id])
        no_confirmada1.refresh_from_db()
        no_confirmada2.refresh_from_db()

        self.assertTrue(no_confirmada1.confirmacionEntregaOfrenda)
        self.assertFalse(no_confirmada2.confirmacionEntregaOfrenda)

    def test_grupos_red(self):
        """
        Prueba que devuelva los grupos de la red del grupo escogido.
        """

        grupo = Grupo.objects.get(id=500)
        red = grupo.grupos_red

        self.assertEqual(grupo, red[0])
        self.assertEqual(600, red[1].id)

    def test_fusionar_traslada_visitas(self):
        """
        Prueba que se trasladen todas las visitas del grupo que se esta fusionando con el nuevo grupo.
        """

        from consolidacion.tests.factories import VisitaFactory

        grupo = Grupo.objects.get(id=500)
        nuevo_grupo = Grupo.objects.get(id=800)

        visita1 = VisitaFactory(grupo=grupo)
        visita2 = VisitaFactory(grupo=grupo)

        grupo.fusionar(nuevo_grupo)

        visitas = nuevo_grupo.visitas.all()
        self.assertIn(visita1, visitas)
        self.assertIn(visita2, visitas)

    def test_fusionar_traslada_encontristas(self):
        """
        Prueba que se trasladen todos los encontristas asociados al grupo que se esta fusionando con el nuevo grupo.
        """

        from encuentros.tests.factories import EncontristaFactory

        grupo = Grupo.objects.get(id=500)
        nuevo_grupo = Grupo.objects.get(id=800)

        encontrista1 = EncontristaFactory(grupo=grupo)
        encontrista2 = EncontristaFactory(grupo=grupo)

        grupo.fusionar(nuevo_grupo)

        encontristas = nuevo_grupo.encontristas.all()
        self.assertIn(encontrista1, encontristas)
        self.assertIn(encontrista2, encontristas)

    def test_fusionar_traslada_reuniones_gar(self):
        """
        Prueba que se trasladen todas las reuniones GAR asociadas al grupo que se esta fusionando con el nuevo grupo.
        """

        grupo = Grupo.objects.get(id=500)
        nuevo_grupo = Grupo.objects.get(id=800)

        reunion1 = ReunionGARFactory(grupo=grupo)
        reunion2 = ReunionGARFactory(grupo=grupo)

        grupo.fusionar(nuevo_grupo)

        reuniones = nuevo_grupo.reuniones_gar.all()
        self.assertIn(reunion1, reuniones)
        self.assertIn(reunion2, reuniones)

    def test_fusionar_traslada_reuniones_discipulado(self):
        """
        Prueba que se trasladen todas las reuniones de discipulado asociadas al grupo que se esta fusionando con el
        nuevo grupo.
        """

        grupo = Grupo.objects.get(id=500)
        nuevo_grupo = Grupo.objects.get(id=800)

        reunion1 = ReunionDiscipuladoFactory(grupo=grupo)
        reunion2 = ReunionDiscipuladoFactory(grupo=grupo)

        grupo.fusionar(nuevo_grupo)

        reuniones = nuevo_grupo.reuniones_discipulado.all()
        self.assertIn(reunion1, reuniones)
        self.assertIn(reunion2, reuniones)

    def test_fusionar_traslada_miembros(self):
        """
        Prueba que se trasladen todas los miembros asociados al grupo que se esta fusionando con el nuevo grupo.
        """

        grupo = Grupo.objects.get(id=500)
        nuevo_grupo = Grupo.objects.get(id=800)

        miembro1 = MiembroFactory(grupo=grupo)
        miembro2 = MiembroFactory(grupo=grupo, admin=True)

        grupo.fusionar(nuevo_grupo)

        miembros = nuevo_grupo.miembros.all()
        self.assertIn(miembro1, miembros)
        self.assertIn(miembro2, miembros)

    def test_fusionar_traslada_grupos_descendientes(self):
        """
        Prueba que se trasladen los descendientes del grupo que se esta fusionando con el nuevo grupo.
        """

        grupo = Grupo.objects.get(id=500)
        nuevo_grupo = Grupo.objects.get(id=800)

        grupo.fusionar(nuevo_grupo)

        hijo = Grupo.objects.get(id=600)
        self.assertIn(hijo, nuevo_grupo.get_children())

    def test_fusionar_elimina_grupo_actual(self):
        """
        Prueba que se elimine de la bd el grupo que se esta fusionando con el nuevo grupo.
        """

        grupo = Grupo.objects.get(id=500)
        nuevo_grupo = Grupo.objects.get(id=800)

        grupo.fusionar(nuevo_grupo)
        self.assertEqual(Grupo.objects.filter(id=500).count(), 0, msg="El grupo con id 500 se debio eliminar de la bd.")

    def test_obtener_cabeza_de_red(self):
        """
        Prueba que devuelva la cabeza de red del grupo indicado.
        """

        grupo = Grupo.objects.get(id=600)
        cabeza = grupo.cabeza_red
        self.assertEqual(cabeza.pk, 500, msg="El grupo cabeza de red no esta correcto.")

    def test_obtener_cabeza_de_red_retorna_none(self):
        """
        Prueba que devuelva NONE como cabeza de red si el grupo se encuentra por encima de los 72 del inicio del arbol.
        """

        grupo = Grupo.objects.get(id=200)
        self.assertIsNone(grupo.cabeza_red)

    def test_grupo_tiene_estado_activo(self):
        """
        Prueba que los grupos esten viniendo con estado activo.
        """

        padre = Grupo.objects.get(id=100)

        for grupo in padre.grupos_red:
            self.assertTrue(grupo.historiales.filter(estado=HistorialEstado.ACTIVO).exists())

    def test_grupos_red_retorne_todos_los_grupos_sin_excepcion_de_archivados(self):
        """
        Prueba que con el metodo de _grupos_red se retornen todos los grupos, aun los que estan en
        estado archivado
        """

        # TODO break up these test onto separete tests
        padre = Grupo.objects.get(id=100)

        ids_grupos = Grupo.objects.activos().values_list('id', flat=1)

        for grupo in padre.grupos_red:
            self.assertIn(grupo.id, ids_grupos)

        grupo_a = Grupo.objects.get(id=600)
        grupo_a.actualizar_estado(estado=HistorialEstado.ARCHIVADO)

        del padre.grupos_red
        self.assertIn(grupo_a, padre._grupos_red)
        self.assertNotIn(grupo_a, padre.grupos_red)

    def test_estado_viene_queryset_use_estado_anotado(self):
        grupo = Grupo.objects.get(id=300)
        grupo.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)
        grupo = Grupo.objects.get(id=300)

        self.assertEqual(grupo.estado, HistorialEstado.SUSPENDIDO)
    
    def test_estado_no_viene_queryset_use_estado_historial(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)

        self.assertEqual(grupo.estado, HistorialEstado.SUSPENDIDO)

    def test_get_estado_display(self):
        grupo = GrupoFactory()
        grupo.actualizar_estado(estado=HistorialEstado.SUSPENDIDO)

        self.assertEqual(grupo.get_estado_display(), 'SUSPENDIDO')

    def test_numero_celulas(self):
        """
        Prueba que devuelva el numero de grupos a cargo del grupo indicado.
        """

        grupo = Grupo.objects.get(id=300)
        self.assertEqual(grupo.numero_celulas, 4)

    def test_numero_celulas_con_archivados(self):
        """
        Prueba que si el grupo tiene descendientes archivados, estos no se cuenten dentro del numero de celulas.
        """

        grupo = Grupo.objects.get(id=300)
        hijo = GrupoHijoFactory(parent=grupo)
        hijo.actualizar_estado(estado=HistorialEstado.ARCHIVADO)

        self.assertEqual(grupo.numero_celulas, 4)

    def test_devuelve_true_si_reunion_discipulado_reportada(self):
        """Prueba que devuelva True si el grupo ya reporto la reunion discipulado con la predica ingresada."""

        predica = PredicaFactory()
        grupo = Grupo.objects.get(id=300)
        ReunionDiscipuladoFactory(grupo=grupo, predica=predica)

        self.assertTrue(grupo.reunion_discipulado_reportada(predica))

    def test_devuelve_false_si_reunion_discipulado_no_sido_reportada(self):
        """Prueba que devuelva False si el grupo no reporto la reunion discipulado con la predica ingresada."""

        predica = PredicaFactory()
        grupo = Grupo.objects.get(id=300)

        self.assertFalse(grupo.reunion_discipulado_reportada(predica))

    def test_nombre_corto_es_primer_apellido_lideres(self):
        """Prueba que el nombre corto del grupo devuelva un string con los primeros apellidos de los lideres"""

        grupo = GrupoFactory(lider__primer_apellido='Narvaez')
        MiembroFactory(primer_apellido='Hernandez', lider=True, grupo_lidera=grupo)

        self.assertEqual('HERNANDEZ - NARVAEZ', grupo.nombre_corto)
    
    def test_padre_subred(self):

        padre = Grupo.objects.get(id=300)
        grupo = GrupoHijoFactory(parent=Grupo.objects.get(id=600))

        self.assertEqual(grupo.padre_subred(padre), Grupo.objects.get(id=500))


class ReunionGARModelTest(BaseTest):
    """Pruebas unitarias para el modelo ReunionGAR."""

    def test_reunion_no_realizada_ofrenda_cero(self):
        """Prueba que me devuelva una instancia de una reunion GAR con ofrenda=0."""

        grupo = GrupoFactory()

        reunion = ReunionGAR.no_realizada(grupo, datetime.date.today())
        self.assertEqual(reunion.ofrenda, 0)

    def test_reunion_no_realizada_numero_tota_asistentes_cero(self):
        """Prueba que me devuelva una instancia de una reunion GAR con numeroTotalAsistentes=0."""

        grupo = GrupoFactory()

        reunion = ReunionGAR.no_realizada(grupo, datetime.date.today())
        self.assertEqual(reunion.numeroTotalAsistentes, 0)

    def test_reunion_no_realizada_numero_lideres_asistentes_cero(self):
        """Prueba que me devuelva una instancia de una reunion GAR con numeroLideresAsistentes=0."""

        grupo = GrupoFactory()

        reunion = ReunionGAR.no_realizada(grupo, datetime.date.today())
        self.assertEqual(reunion.numeroLideresAsistentes, 0)