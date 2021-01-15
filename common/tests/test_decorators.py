from unittest import mock
from django.core.cache import cache
from django.test import SimpleTestCase
from ..decorators import cache_value


class CacheValueDecoratorTest(SimpleTestCase):
    """Pruebas para el decorador cache_value."""

    def setUp(self):
        self.function = mock.Mock(return_value='hola')
        self.key = 'test_decorator'

    def test_valor_se_guarda_cache(self):
        """Prueba que el valor se guarde en la cache si no se encuentra ya guardado."""

        valor = cache_value(key=self.key)(self.function)()

        self.assertTrue(self.function.called, msg="La función debio ser llamada.")
        self.assertIsNotNone(cache.get(self.key))
        self.assertEqual(cache.get(self.key), valor)

    def test_valor_se_obtiene_cache(self):
        """Prueba que el valor se obtiene la cache si ya se encuentra guardado en ella."""

        cache.set(self.key, 'hola')
        cache_value(key=self.key)(self.function)()

        self.assertFalse(self.function.called, msg="La función no debio ser llamada.")

    def test_sufijo_not_None_key_modifique(self):
        """Prueba que si se envia un sufijo, la llave usada en la cache se modifique para usar el sufijo."""

        nueva_llave = '{}_{}'.format(self.key, 2)
        objeto = mock.Mock()
        objeto.pk = 2

        cache_value(key=self.key, suffix='pk')(self.function)(objeto)
        self.assertIsNotNone(cache.get(nueva_llave))
        self.assertIsNone(cache.get(self.key))
