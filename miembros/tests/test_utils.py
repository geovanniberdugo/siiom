from .factories import MiembroFactory
from .. import utils
from common.tests import base
from grupos.models import Grupo


class UtilsModuleTest(base.BaseTest):
    """
    Pruebas para las funciones utiles de miembros.
    """

    def test_divorciar_miembro(self):
        """
        Prueba que los miembros puedan divorciarse adecuadamente.
        """

        function = utils.divorciar_miembro

        miembro = MiembroFactory()
        conyugue = MiembroFactory(conyugue=miembro)
        miembro.update(conyugue=conyugue)

        self.assertEqual(conyugue.conyugue, miembro)
        self.assertEqual(miembro.conyugue, conyugue)

        function(miembro)

        self.assertIsNone(miembro.conyugue)
        self.assertIsNone(conyugue.conyugue)
        self.assertEqual(miembro.estado_civil, miembro.DIVORCIADO)
        self.assertEqual(conyugue.estado_civil, miembro.DIVORCIADO)

    def test_calcular_grupos_miembro(self):
        """
        Prueba que la funcion retorne el numero de grupos que tiene un miembro
        mas el incluido.
        """

        function = utils.calcular_grupos_miembro

        self.crear_arbol()

        miembro = MiembroFactory()

        self.assertEqual(function(miembro), 0)

        miembro = Grupo.objects.get(id=300).lideres.first()

        self.assertEqual(function(miembro), 4)
