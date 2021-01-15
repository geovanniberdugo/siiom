import datetime

from common.tests.base import BaseTest
from .. import utils, managers
from .factories import ReunionGARFactory



class UtilsModuleTest(BaseTest):
    """
    Pruebas unitarias para el modulo Utils.
    """

    def test_convertir_lista_queryset(self):
        """
        Prueba cuando se ingresa una lista de grupos, la función devuelva un queryset.
        """

        queryset = utils.convertir_lista_grupos_a_queryset([])
        self.assertIsInstance(queryset, managers.GrupoQuerySet)

    def test_obtener_fechas_semana(self):
        """
        Verifica que la funcion solo retorne las fechas desde el lunes hasta el domingo.
        """

        days_list = [8, 9, 10, 11, 12, 13, 14]

        for day in days_list:
            fecha = datetime.date(month=8, day=day, year=2016)
            fechas = utils.obtener_fechas_semana(fecha)
            self.assertEqual(days_list, list(map(lambda x: x.day, fechas)))


class UtilsReunionReportadaTest(BaseTest):
    """
    Pruebas unitarias para la funcion de reunion_reportada
    """

    def setUp(self):
        self.function = utils.reunion_reportada
        self.fecha = datetime.date(month=8, day=11, year=2016)

    def test_reunion_reportada_mismo_dia(self):
        """
        Verifica que la funcion retorne verdadero si se consulta el mismo dia.
        """

        reunion = ReunionGARFactory()

        self.assertTrue(self.function(reunion.fecha, reunion.grupo))

    def test_reunion_reportada_retorna_falso_si_se_escoge_otra_fecha(self):
        """
        Verifica que la funcion retorne falso si se consulta otra fecha donde no hay reporte.
        """

        reunion = ReunionGARFactory(fecha=self.fecha)

        self.assertFalse(self.function(datetime.date.today(), reunion.grupo))

    def test_reunion_reportada_retorna_true_en_cualquier_dia_de_la_semana_de_reunion(self):
        """
        Verifica que a partir de una fecha de reunion, la funcion retorne verdadero sobre cada
        dia de esa semana.
        """

        reunion = ReunionGARFactory(fecha=self.fecha)

        fecha_inicio = datetime.date(month=8, day=8, year=2016)

        for x in range(7):
            self.assertTrue(self.function(fecha_inicio + datetime.timedelta(days=x), reunion.grupo))
        self.assertFalse(self.function(fecha_inicio + datetime.timedelta(days=7), reunion.grupo))
