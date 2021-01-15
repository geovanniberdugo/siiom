from django.urls import reverse
from miembros.tests.factories import MiembroFactory
from common.tests.factories import UsuarioFactory
from grupos.tests.factories import GrupoFactory
from common.tests.base import BaseTest
from grupos.models import Grupo


class BuscarViewTest(BaseTest):
    """
    Pruebas unitarias para la vista de busqueda de miembros y grupos.
    """

    URL_MIEMBROS = reverse('buscar', args=['miembro'])
    URL_GRUPOS = reverse('buscar', args=['grupo'])

    def setUp(self):
        self.usuario = UsuarioFactory(user_permissions=['buscar_todos'])
        self.lider = MiembroFactory(lider=True, nombre='mariana')

    def termino_busqueda(self, termino='adriana fernandez'):
        return {'buscar': termino}

    def test_get_buscar_todos_miembros(self):
        """
        Prueba el buscador de miembros cuando el usuario tiene permiso de buscar todos.
        """

        MiembroFactory(nombre='adriana', primer_apellido='mendoza')
        MiembroFactory(nombre='maria', primer_apellido='fernandez')

        self.login_usuario(self.usuario)
        response = self.client.get(self.URL_MIEMBROS, self.termino_busqueda())

        self.assertContains(response, 'adriana'.upper())
        self.assertContains(response, 'fernandez'.upper())

    def test_get_buscar_todos_grupos(self):
        """
        Prueba el buscador de grupos cuando el usuario tiene permiso de buscar todos.
        """

        grupo1 = GrupoFactory(lider__nombre='adriana', lider__primer_apellido='mendoza', nombre='mendoza')
        grupo2 = GrupoFactory(lider__nombre='maria', lider__primer_apellido='fernandez', nombre='fernandez')

        self.login_usuario(self.usuario)
        response = self.client.get(self.URL_GRUPOS, self.termino_busqueda())

        self.assertContains(response, grupo1.nombre.upper())
        self.assertContains(response, grupo2.nombre.upper())

    def datos_pruebas(self):
        self.crear_arbol()
        grupo = Grupo.objects.get(id=400)
        self.lider.grupo_lidera = grupo
        self.lider.save()

        grupo2 = Grupo.objects.get(id=700)
        self.miembro_red = MiembroFactory(grupo=grupo2)
        self.lider_red = grupo2.lideres.first()

        self.miembro_no_red = MiembroFactory(nombre='maria')
        self.lider_no_red = Grupo.objects.get(id=300).lideres.first()

    def test_get_lider_sin_grupo_buscar_miembros(self):
        """
        Prueba que cuando el lider no tenga el permiso buscar_todos y no lidere grupo la busqueda no devuelva
        resultados.
        """

        self.login_usuario(self.lider.usuario)
        response = self.client.get(self.URL_MIEMBROS, self.termino_busqueda())

        self.assertContains(response, 'No se encontraron resultados')

    def test_get_lider_sin_grupo_buscar_grupos(self):
        """
        Prueba que cuando el lider no tenga el permiso buscar_todos y no lidere grupo la busqueda no devuelva
        resultados.
        """

        self.login_usuario(self.lider.usuario)
        response = self.client.get(self.URL_GRUPOS, self.termino_busqueda())

        self.assertContains(response, 'No se encontraron resultados')

    def test_get_lider_buscar_miembros(self):
        """
        Prueba que cuando el lider no tenga el permiso buscar_todos solo puede buscar miembros entre sus descendientes.
        """

        self.datos_pruebas()
        termino = 'maria {0} {1} {2}'.format(
            self.lider_red.primer_apellido, self.miembro_red.nombre, self.lider_no_red.nombre
        )

        self.login_usuario(self.lider.usuario)
        response = self.client.get(self.URL_MIEMBROS, self.termino_busqueda(termino=termino))

        self.assertContains(response, self.miembro_red.cedula)
        self.assertContains(response, self.lider_red.cedula)
        self.assertContains(response, self.lider.cedula)

        self.assertNotContains(response, self.miembro_no_red.cedula)
        self.assertNotContains(response, self.lider_no_red.cedula)

    def test_get_lider_buscar_grupos(self):
        """
        Prueba que cuando lider no tenga el permiso buscar_todos solo pueda buscar grupos entre sus descendientes.
        """

        self.datos_pruebas()
        termino = 'maria {0} {1} {2}'.format(
            self.lider_red.primer_apellido, self.miembro_red.nombre, self.lider_no_red.nombre
        )

        self.login_usuario(self.lider.usuario)
        response = self.client.get(self.URL_GRUPOS, self.termino_busqueda(termino=termino))

        self.assertContains(response, self.lider_red.cedula)
        self.assertContains(response, self.lider.cedula)

        self.assertNotContains(response, self.lider_no_red.cedula)
