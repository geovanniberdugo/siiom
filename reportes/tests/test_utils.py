from django.test import TestCase

from .. import utils

import datetime


class UtilsModuleTest(TestCase):
    """
    Pruebas Unitarias para las funciones de utils en el modulo de reportes.
    """

    def test_fechas_reporte_generador(self):
        """
        verifica que la tupla de fechas siempre sea de lunes a domingo,
        y que sean fechas válidas.
        """
        import calendar

        _fecha_inicial = datetime.datetime.today()
        fecha_inicial = _fecha_inicial
        fecha_final = fecha_inicial + datetime.timedelta(days=15)

        for tupla in utils.fechas_reporte_generador(_fecha_inicial, fecha_final):
            self.assertIsInstance(tupla, tuple)

            self.assertEqual(tupla[0], fecha_inicial - datetime.timedelta(days=fecha_inicial.isoweekday() - 1))
            self.assertEqual(calendar.weekday(year=tupla[0].year, month=tupla[0].month, day=tupla[0].day), 0)

            self.assertEqual(tupla[1], tupla[0] + datetime.timedelta(days=6))
            self.assertEqual(calendar.weekday(year=tupla[1].year, month=tupla[1].month, day=tupla[1].day), 6)

            fecha_inicial += datetime.timedelta(days=7)
