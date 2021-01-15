from django.test import tag
from common.tests.base import BaseTest
from common.tests.factories import UsuarioFactory
from ..models import Visita


class CrearVisitaViewTest(BaseTest):
    """Pruebas unitarias para la vista crear visita."""

    URL = 'consolidacion:crear_visita'

    def setUp(self):
        self.usuario = UsuarioFactory(user_permissions=('es_administrador',))
    
    def datos_formulario(self):
        """
        Retorna un diccionario con los datos para el formulario VisitaForm
        """

        data = {
            'primer_nombre': 'Maria', 'primer_apellido': 'Torres', 'genero': Visita.FEMENINO, 'segundo_nombre': 'Melina',
            'email': 'test@siiom.com', 'segundo_apellido': 'Mejia', 'telefono': 3423454, 'direccion': 'Cra 45 N 93 - 34',
            'edad': '23 años', 'estado_civil': Visita.SOLTERO
        }

        return data
    
    def test_get(self):
        """Prueba que se pueda ver el template."""

        self.login_usuario(self.usuario)
        self.get_check_200(self.URL)
        self.assertResponseContains('Visita', html=False)
    
    def test_post_formulario_valido_redirecciona_get(self):
        """
        Prueba que si se hace un POST y el formulario es valido redirecciona a la misma página.
        """

        data = self.datos_formulario()
        self.login_usuario(self.usuario)
        response = self.post(self.URL, data=data)

        self.assertEqual(Visita.objects.count(), 1, msg="Se debio crear la visita")
        self.assertRedirects(response, self.reverse(self.URL))

    def test_post_formulario_invalido_muestra_errores(self):
        """
        Prueba que si se hace un POST y el formulario es invalido se muestren los errores.
        """

        self.login_usuario(self.usuario)
        response = self.post(self.URL, data={})

        self.assertFormError(response, 'form', 'primer_apellido', self.MSJ_OBLIGATORIO)
        self.assertFormError(response, 'form', 'primer_nombre', self.MSJ_OBLIGATORIO)
        self.assertFormError(response, 'form', 'telefono', self.MSJ_OBLIGATORIO)
        self.assertFormError(response, 'form', 'genero', self.MSJ_OBLIGATORIO)