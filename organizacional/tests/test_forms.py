import factory

from unittest import mock
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from common.tests.base import BaseTest
from ..forms import NuevoEmpleadoForm
from .factories import DepartamentoFactory, EmpleadoFactory, AreaFactory

User = get_user_model()


class NuevoEmpleadoFormTest(BaseTest):
    """
    Pruebas unitarias para el formulario de creación de empleados de una iglesia.
    """

    def datos_formulario(self, **kwargs):
        """
        Retorna un diccionario con los datos para el formulario NuevoEmpleadoForm.
        """

        self.departamento = DepartamentoFactory()
        data = factory.build(dict, FACTORY_CLASS=EmpleadoFactory)
        data.update({
            'email': 'a@a.com', 'contrasena1': 'mariana', 'contrasena2': 'mariana',
            'password2': 'mariana', 'departamento': self.departamento.id, 'jefe_departamento': True
        })
        data.update(**kwargs)
        return data

    def test_contrasenas_diferentes_formulario_invalido(self):
        """
        Prueba que si los campos contraseña y confirmar contraseña son diferentes el formulario no sea valido.
        """

        data = self.datos_formulario()
        data['contrasena2'] = 'diferente'
        form = NuevoEmpleadoForm(data=data)

        self.assertFalse(
            form.is_valid(),
            msg="{0} y {1} son diferentes. Por lo tanto, el formulario no debe ser valido".format(
                data['contrasena1'], data['contrasena2']
            )
        )
        self.assertTrue(form.has_error('contrasena1', code='contrasenas_diferentes'))
        self.assertTrue(form.has_error('contrasena2', code='contrasenas_diferentes'))

    def test_formulario_invalido_si_areas_y_jefe_departamento_vacios(self):
        """
        Prueba que el formulario sea invalido si los campos jefe de departamento y areas no estan llenos.
        """

        data = self.datos_formulario()
        del data['jefe_departamento']
        form = NuevoEmpleadoForm(data=data)

        self.assertFalse(form.is_valid(), msg="Los campos jefe de departamento y areas se encuentran vacíos.")

    def test_formulario_invalido_si_email_pertenece_otro_empleado(self):
        """
        Prueba que el formulario sea invalido si el email ingresado pertenece a otro empleado.
        """

        data = self.datos_formulario()
        EmpleadoFactory(usuario__email=data['email'])
        form = NuevoEmpleadoForm(data=data)

        self.assertFalse(
            form.is_valid(),
            msg="Ya existe un empleado con el email. Por lo tanto el formulario debe ser invalido."
        )

    def test_formulario_guarda_empleado(self):
        """
        Prueba que cuando se guarde el formulario se crea el empleado.
        """

        from ..models import Empleado

        form = NuevoEmpleadoForm(data=self.datos_formulario())
        form.is_valid()
        form.save()

        self.assertEqual(Empleado.objects.count(), 1)

    def test_formulario_crea_usuario_si_no_existe(self):
        """
        Prueba que cuando se guarde el formulario se crea el usuario si el email ingresado no pertenece a ningún
        usuario.
        """

        form = NuevoEmpleadoForm(data=self.datos_formulario())
        form.is_valid()
        empleado = form.save()

        usuario = User.objects.first()
        self.assertIsNotNone(usuario, msg="El usuario no fue creado")
        self.assertEqual(empleado.usuario, usuario, msg="El usuario no fue asignado al empleado")

    def test_formulario_no_crea_usuario_si_existe(self):
        """
        Prueba que cuando se guarde el formulario no se crea un nuevo usuario si el email ingresado pertenece a algún
        usuario ya existente.
        """

        from common.tests.factories import UsuarioFactory

        data = self.datos_formulario()
        usuario = UsuarioFactory(email=data['email'])

        form = NuevoEmpleadoForm(data=data)
        form.is_valid()
        empleado = form.save()

        self.assertEqual(User.objects.count(), 1, msg="El usuario fue creado")
        self.assertEqual(empleado.usuario, usuario, msg="El usuario no fue asignado al empleado")

    def test_jefe_departamento_asigna_todas_areas_departamento(self):
        """
        Prueba que cuando el empleado sea jefe de departamento se le asignen todas las areas que pertencen al
        departamento escogido.
        """

        data = self.datos_formulario(jefe_departamento='True')
        AreaFactory(nombre='Tesoreria', departamento=self.departamento)
        AreaFactory(departamento=self.departamento)

        form = NuevoEmpleadoForm(data=data)
        form.is_valid()
        empleado = form.save()

        self.assertEqual(empleado.areas.count(), 2, msg="No se asignaron todas las areas del departamento al empleado")

    @mock.patch('common.forms.CustomModelForm.save', side_effect=IntegrityError)
    def test_error_al_guardar_formulario_no_se_guarda_nada_en_db(self, save_mock):
        """
        Prueba que si ocurre un error al guardar el formulario no se guarde el empleado, ni el usuario.
        """

        from ..models import Empleado

        form = NuevoEmpleadoForm(data=self.datos_formulario())
        form.is_valid()
        form.save()

        self.assertTrue(save_mock.called)
        self.assertEqual(Empleado.objects.count(), 0, msg="Se guardo el empleado.")

    @mock.patch('common.forms.CustomModelForm.save', side_effect=IntegrityError)
    def test_error_al_guardar_formulario_agrega_error_form(self, save_mock):
        """
        Prueba que si ocurre un error al momento de guardar el formulario, se agregue un error al formulario.
        """

        form = NuevoEmpleadoForm(data=self.datos_formulario())
        form.is_valid()
        form.save()

        self.assertTrue(save_mock.called)
        self.assertEqual(len(form.non_field_errors()), 1)
