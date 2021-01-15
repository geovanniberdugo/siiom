import inspect
from unittest import mock, skip, skipIf
from django.test import RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.http import HttpResponse

from common.tests.base import BaseTest
from ..decorators import miembro_property_test_decorator
from .factories import MiembroFactory


MENSAJE_SKIP = 'No hay miembros en el request sin el middleware de miembros'


class MiembroPropertyDecoratorTest(BaseTest):
    """
    Pruebas al decorador de vistas de miembro_property_test_decorator
    """

    def setUp(self):
        self.request = RequestFactory()
        self.decorator = miembro_property_test_decorator
        self.view = mock.Mock()

    def get_user_miembro(self, lider=False, admin=False):
        """Retorna un usuario miembro"""
        miembro = self.miembro = MiembroFactory(lider=lider, admin=admin)
        self.usuario = User.objects.create_user(
            username='test', email='test_fun@admin.com', password='contrasena_secreta'
        )
        miembro.usuario = self.usuario
        miembro.save()
        return self.usuario

    @skipIf('miembros.middleware.MiembroMiddleWare' not in settings.MIDDLEWARE, MENSAJE_SKIP)
    def test_vista_no_es_llamada_si_no_hay_usuario(self):
        """Verifica que la funcion decorada no sea llamada cuando no hay usuario en la peticion."""

        request = self.request

        decorador = self.decorator(self.view, 'test')

        response = HttpResponse()
        response.status_code = 403
        with self.assertRaises(PermissionDenied):
            response = decorador(request)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.view.called)

    @skipIf('miembros.middleware.MiembroMiddleWare' not in settings.MIDDLEWARE, MENSAJE_SKIP)
    def test_vista_no_es_llamada_si_usuario_es_anonimo(self):
        """Verifica que la funcion decorada no sea llamada si el usuario es anonimo."""

        request = self.request
        request.user = AnonymousUser()

        decorador = self.decorator(self.view, 'test')

        response = HttpResponse()
        response.status_code = 403
        with self.assertRaises(PermissionDenied):
            response = decorador(request)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.view.called)

    @skipIf('miembros.middleware.MiembroMiddleWare' not in settings.MIDDLEWARE, MENSAJE_SKIP)
    def test_vista_no_es_llamada_si_usuario_no_tiene_miembro(self):
        """Verifica que la funcion decorada no sea llamada si el usuario es usuario logeado sin miembro."""

        request = self.request
        request.user = User.objects.create_user(
            username='test', email='test_fun@admin.com', password='contrasena_secreta'
        )

        decorador = self.decorator(self.view, 'test')

        response = HttpResponse()
        response.status_code = 403
        with self.assertRaises(PermissionDenied):
            response = decorador(request)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.view.called)

    @skipIf('miembros.middleware.MiembroMiddleWare' not in settings.MIDDLEWARE, MENSAJE_SKIP)
    def test_vista_llamada_si_usuario_es_miembro(self):
        """Verifica que la funcion decorada sea llamada si el usuario es usuario logeado con miembro."""

        request = self.request
        request.user = self.get_user_miembro()
        request.miembro = self.miembro

        decorador = self.decorator(self.view, 'grupo_lidera', function=lambda x: not x)

        decorador(request)

        self.assertTrue(self.view.called)

    @skipIf('miembros.middleware.MiembroMiddleWare' not in settings.MIDDLEWARE, MENSAJE_SKIP)
    def test_vista_llamada_si_usuario_cumple_condicion(self):
        """
        Verifica que la funcion decorada o vista, sea llamada si el usuario miembro cumple con la condicion
        """

        request = self.request
        request.user = self.get_user_miembro()
        request.miembro = self.miembro

        decorador = self.decorator(self.view, 'cedula')

        decorador(request)

        self.assertTrue(self.view.called)

    @skipIf('miembros.middleware.MiembroMiddleWare' not in settings.MIDDLEWARE, MENSAJE_SKIP)
    def test_vista_llamada_si_usuario_cumple_permiso(self):
        """
        Verifica que la funcion decorada o vista, sea llamada si el usuario miembro cumple con el permiso
        """

        request = self.request
        request.user = self.get_user_miembro(lider=True, admin=True)
        request.miembro = self.miembro

        decorador = self.decorator(self.view, 'cedula', 'miembros.es_lider', 'miembros.es_administrador')

        decorador(request)

        self.assertTrue(self.view.called)
