# Django imports
from django.urls import reverse
from django.test import tag
from rest_framework import status

from .base import BaseTestAPI
from miembros.tests.factories import MiembroFactory, BarrioFactory
from grupos.tests.factories import RedFactory
from grupos.models import Grupo, Red
from .. import constants

class TestAPIBusquedaMiembro(BaseTestAPI):
    """
    Pruebas unitarias para la vista de API que permite hacer las busquedas a los miembros lideres
    que no lideran un grupo.
    """

    def setUp(self):
        self.crear_arbol()
        grupo3 = Grupo.objects.get(id=300)
        self.padre = Grupo.objects.get(id=800)
        self.lider1 = MiembroFactory(lider=True, grupo=grupo3)
        self.lider2 = MiembroFactory(lider=True, grupo=self.padre)
        self.barrio = BarrioFactory()
        self.red_jovenes = Red.objects.get(nombre='jovenes')
        self.url = reverse('common:busqueda_miembro_api', args=(self.red_jovenes.id, ))

    def test_get_not_response(self):
        """Prueba que en GET no se obtienga la respuesta."""

        response = self.GET(login=False)

        self.assertNotIn('miembros', response)
        self.assertIn(constants.RESPONSE_CODE, response)
        self.assertEqual(response[constants.RESPONSE_CODE], status.HTTP_401_UNAUTHORIZED)

    def test_miembros_in_response(self):
        """
        Prueba que los miembros esten en la respuesta de JSON.
        """

        response = self.POST(data={'value': self.lider1.nombre[0:5]})

        self.assertIn('miembros', response)
        self.assertIn(constants.RESPONSE_CODE, response)
        self.assertEqual(response[constants.RESPONSE_CODE], constants.RESPONSE_SUCCESS)

    def test_busqueda_solo_muestra_lideres(self):
        """
        Prueba que en la busqueda solo se muestren miembros que sean lideres.
        """

        no_lider = MiembroFactory()

        response = self.POST(data={'value': no_lider.nombre[0:5]})

        self.assertEqual(response['miembros'].__len__(), 0)

        lider = MiembroFactory(lider=True, grupo=Grupo.objects.red(self.red_jovenes)[0])

        response = self.POST(data={'value': lider.nombre[0:5]})

        self.assertIn('id', response['miembros'][0])
        # self.assertEqual(str(response['miembros'][0]['id']), str(lider.id))
        self.assertIn(str(lider.id), [x['id'] for x in response['miembros']])

    def test_campo_lideres_solo_muestra_lideres_red_ingresada(self):
        """
        Prueba que el campo lideres solo muestra lideres que pertenecen a los grupos de la red ingresada.
        """

        grupo1 = Grupo.objects.get(id=200)
        lider_joven = MiembroFactory(lider=True, grupo=grupo1, nombre='asdfder')

        response = self.POST(data={'value': lider_joven.nombre[0:5]})
        self.assertEqual(response['miembros'].__len__(), 0)

    def test_campo_lideres_muestra_lideres_raiz_si_red_no_tiene_grupo(self):
        """
        Prueba que el campo lideres muestre los lideres disponibles que asisten al grupo raiz de la iglesia si la red
        ingresada no tiene ningún grupo.
        """

        raiz = Grupo.objects.get(id=100)
        otro = Grupo.objects.get(id=300)

        red_nueva = RedFactory(nombre='nueva red')

        miembro = MiembroFactory(lider=True, grupo=raiz)

        url = reverse('common:busqueda_miembro_api', args=(red_nueva.id, ))

        response = self.POST(url=url, data={'value': miembro.nombre[0:5]})

        self.assertEqual(str(response['miembros'][0]['id']), miembro.id.__str__())

        for m in response['miembros']:
            self.assertNotEqual(str(otro.lideres.first().id), str(m['id']))

    def test_grupo_by_solo_muestra_lideres_disponibles_debajo_de_grupo(self):
        """
        Prueba que a partir de el campo de grupo_by, solo sean mostrados los lideres disponibles que se encuentran
        por debajo de ese grupo.
        """
        grupo = Grupo.objects.get(id=300)
        grupo_lider_disponible = Grupo.objects.get(id=700)

        lider_disponible_1 = MiembroFactory(lider=True, grupo=grupo_lider_disponible)
        lider_disponible_2 = MiembroFactory(lider=True, grupo=grupo)

        response = self.POST(data={'value': lider_disponible_1.nombre[0:5], 'grupo_by': grupo.id})

        self.assertNotIn(str(lider_disponible_1), [x['id'] for x in response['miembros']])

        response = self.POST(data={'value': lider_disponible_2.nombre[0:5], 'grupo_by': grupo.id})

        self.assertIn(str(lider_disponible_2.id), [x['id'] for x in response['miembros']])

    def test_busqueda_muestre_discipulos_grupo_raiz(self):
        """Prueba que en la busqueda se muestren los discipulos de grupo raiz que se encuentren disponibles."""

        raiz = Grupo.objects.get(id=100)
        lider = MiembroFactory(lider=True, grupo=raiz, nombre='ASDFGHJER')

        response = self.POST(data={'value': lider.nombre[0:5]})
        self.assertIn(str(lider.id), [x['id'] for x in response['miembros']])
