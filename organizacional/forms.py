import logging

# Django Package
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.functions import Lower
from django.utils.translation import ugettext as _, ugettext_lazy as _lazy

# Locale Apps
from .models import Area, Departamento, Empleado
from common.forms import CustomModelForm

logger = logging.getLogger(__name__)

User = get_user_model()


class AreaForm(forms.ModelForm):
    """
    Formulario para creación de áreas en SGD
    """
    error_css_class = 'has-error'

    class Meta:
        model = Area
        fields = ['nombre', 'departamento']

    def __init__(self, *args, **kwargs):
        super(AreaForm, self).__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['departamento'].widget.attrs.update({'class': 'selectpicker'})


class DepartamentoForm(forms.ModelForm):
    """
    Formulario para la creación de departamentos en el SGD
    """
    error_css_class = 'has-error'

    class Meta:
        model = Departamento
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        super(DepartamentoForm, self).__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})


class EmpleadoForm(forms.ModelForm):
    """
    Formulario para la creacion de empleados en el SGD
    """
    error_css_class = 'has-error'
    correo = forms.EmailField(label=_('Correo Electronico'))
    departamento = forms.ModelChoiceField(queryset=Departamento.objects.all(), label=_('Departamento'))
    contrasena = forms.CharField(
        max_length=255, widget=forms.PasswordInput(), label=_('Contraseña'), required=False
    )
    contrasena_confirmacion = forms.CharField(
        max_length=255, widget=forms.PasswordInput(), label=_('Confirmar Contraseña'), required=False
    )
    _accept = [
        'lider', 'administrador', 'maestro', 'pastor', 'agente',
        'miembro', 'coordinador', 'receptor', 'tesorero'
    ]
    tipo_usuario = forms.ModelChoiceField(
        queryset=Group.objects.annotate(nombre=Lower('name')).exclude(nombre__in=_accept),
        label=_('Tipo de Usuario'), required=False
    )

    class Meta:
        model = Empleado
        fields = [
            'areas', 'cedula', 'primer_nombre', 'segundo_nombre',
            'primer_apellido', 'segundo_apellido', 'jefe_departamento', 'cargo'
        ]

    def __init__(self, *args, **kwargs):
        super(EmpleadoForm, self).__init__(*args, **kwargs)
        self.fields['correo'].widget.attrs.update({'class': 'form-control'})
        self.fields['contrasena'].widget.attrs.update({'class': 'form-control'})
        self.fields['contrasena_confirmacion'].widget.attrs.update({'class': 'form-control'})
        self.fields['cedula'].widget.attrs.update({'class': 'form-control'})
        self.fields['primer_nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['primer_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['cargo'].widget.attrs.update({'class': 'form-control'})
        self.fields['tipo_usuario'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['areas'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['departamento'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['areas'].required = False
        self.fields['areas'].queryset = Area.objects.none()
        if self.is_bound:
            id_departamento = self.data.get('departamento', None)
            try:
                self.fields['areas'].queryset = Area.objects.filter(departamento_id=id_departamento)
            except:
                self.fields['areas'].queryset = Area.objects.none()
        if self.initial:
            if 'areas' in self.initial:
                queryset = self.initial['areas']
                if isinstance(queryset, list):
                    if any(queryset):
                        self.fields['departamento'].initial = Area.objects.get(id=queryset[0].id).departamento
                else:
                    if queryset.exists():
                        self.fields['areas'].queryset = queryset
                        self.fields['departamento'].initial = queryset.first().departamento

    def clean(self, *args, **kwargs):
        inher = kwargs.pop('inher', False)
        cleaned_data = super(EmpleadoForm, self).clean(*args, **kwargs)
        usuario_existente = None
        if 'areas' in cleaned_data and 'jefe_departamento' in cleaned_data:
            departamento = cleaned_data.get('departamento', None)
            jefe_departamento = cleaned_data.get('jefe_departamento', False)
            areas = cleaned_data.get('areas', [])
            if departamento and jefe_departamento is False and not areas:
                self.add_error('areas', _('Este campo es obligatorio'))

        if not inher:
            if 'correo' in cleaned_data:
                try:
                    usuario_existente = User.objects.get(email=cleaned_data['correo'])
                    try:
                        if usuario_existente.empleado:
                            self.add_error('correo', _('Ya existe un empleado con este correo'))
                    except Empleado.DoesNotExist:
                        pass

                except User.DoesNotExist:
                    pass
            if usuario_existente is None:
                if 'contrasena' in cleaned_data and 'contrasena_confirmacion' in cleaned_data:
                    if cleaned_data['contrasena'] != cleaned_data['contrasena_confirmacion']:
                        self.add_error('contrasena', _('Las contraseñas no coinciden'))
                        self.add_error('contrasena_confirmacion', _('Las contraseñas no coinciden'))
        else:
            if 'contrasena' in cleaned_data and 'contrasena_confirmacion' in cleaned_data:
                if cleaned_data['contrasena'] != cleaned_data['contrasena_confirmacion']:
                    self.add_error('contrasena', _('Las contraseñas no coinciden'))
                    self.add_error('contrasena_confirmacion', _('Las contraseñas no coinciden'))
        return cleaned_data


class FormularioEditarEmpleado(EmpleadoForm):
    """
    Formulario de Edicion de empleados
    """
    def __init__(self, *args, **kwargs):
        super(FormularioEditarEmpleado, self).__init__(*args, **kwargs)
        self.fields['contrasena'].required = False
        self.fields['contrasena_confirmacion'].required = False

    def clean(self, *args, **kwargs):
        cleaned_data = super(FormularioEditarEmpleado, self).clean(inher=True, *args, **kwargs)

        contrasena = cleaned_data.get('contrasena', None)
        contrasena_confirmacion = cleaned_data.get('contrasena_confirmacion', None)

        if contrasena != '' and contrasena_confirmacion == '':
            self.add_error('contrasena_confirmacion', _('Este campo es obligatorio'))

        if contrasena_confirmacion != '' and contrasena == '':
            self.add_error('contrasena', _('Este campo es obligatorio'))


class NuevoEmpleadoForm(CustomModelForm):
    """
    Formulario para la creación de un empleado de una iglesia.
    """

    error_messages = {
        'dependencia': _lazy('Debe indicar si el empleado es jefe de departamento o las áreas donde pertenece.'),
        'transaction': _lazy('Ha ocurrido un error al guardar el empleado. Por favor intentelo de nuevo.'),
        'email_asignado': _lazy('Ya existe un empleado con este email.'),
        'contrasenas_diferentes': _lazy('Las contraseñas no coinciden.')
    }

    # Perfiles que se le pueden asignar a un empleado
    _accept = ['consulta', 'digitador', 'administrador sgd']

    email = forms.EmailField(label=_lazy('Email'))
    contrasena1 = forms.CharField(label=_lazy('Contraseña'), widget=forms.PasswordInput(), required=False)
    contrasena2 = forms.CharField(label=_lazy('Confirmar contraseña'), widget=forms.PasswordInput(), required=False)

    departamento = forms.ModelChoiceField(label=_lazy('Departamento'), queryset=Departamento.objects.all())
    perfil = forms.ModelChoiceField(
        label=_lazy('Tipo de usuario'), required=False,
        queryset=Group.objects.annotate(nombre=Lower('name')).filter(nombre__in=_accept)
    )

    class Meta:
        model = Empleado
        fields = [
            'areas', 'cedula', 'primer_nombre', 'segundo_nombre', 'primer_apellido',
            'segundo_apellido', 'cargo', 'jefe_departamento'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['areas'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['cargo'].widget.attrs.update({'class': 'form-control'})
        self.fields['cedula'].widget.attrs.update({'class': 'form-control'})
        self.fields['perfil'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['contrasena1'].widget.attrs.update({'class': 'form-control'})
        self.fields['contrasena2'].widget.attrs.update({'class': 'form-control'})
        self.fields['departamento'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['primer_nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['primer_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['areas'].required = False

        areas_query = Area.objects.none()
        if self.is_bound:
            id = self.data.get('departamento', None)
            try:
                areas_query = Area.objects.filter(departamento=int(id))
            except:
                pass
        elif self.instance.pk:
            departamento = self.instance.areas.first().departamento
            areas_query = Area.objects.filter(departamento=departamento)
            self.fields['departamento'].initial = departamento

        self.fields['areas'].queryset = areas_query

    def clean(self):
        cleaned_data = super().clean()

        # Se verifica que las contraseñas coincidan.
        contrasena1 = cleaned_data.get('contrasena1', None)
        contrasena2 = cleaned_data.get('contrasena2', None)

        if contrasena1 or contrasena2:
            if contrasena1 != contrasena2:
                codigo = 'contrasenas_diferentes'
                mensaje = self.error_messages[codigo]
                self.add_error('contrasena1', forms.ValidationError(mensaje, code=codigo))
                self.add_error('contrasena2', forms.ValidationError(mensaje, code=codigo))

        # Se verifica que se halla indicado si es jefe de departamento o las áreas.
        areas = cleaned_data.get('areas', None)
        jefe_departamento = cleaned_data.get('jefe_departamento', False)

        if not areas and not jefe_departamento:
            self.add_error(None, forms.ValidationError(self.error_messages['dependencia'], code='dependencia'))

        # Se verifica que el email ingresado no pertenezca a otro empleado.
        email = cleaned_data.get('email', None)
        if email:
            try:
                usuario = User.objects.get(email=email)
                try:
                    if usuario.empleado:
                        codigo = 'email_asignado'
                        self.add_error('email', forms.ValidationError(self.error_messages[codigo], code=codigo))
                except Empleado.DoesNotExist:
                    pass
            except Exception as e:
                pass

    def save(self):
        try:
            with transaction.atomic():
                # se intenta buscar o crear el usuario.
                usuario, created = User.objects.get_or_create(
                    email=self.cleaned_data['email'],
                    defaults={'password': '123456', 'username': self.cleaned_data['cedula']}
                )

                if created:  # Si fue creado se le asigna la contraseña del formulario.
                    usuario.set_password(self.cleaned_data['contrasena1'])
                    usuario.save()

                perfil = self.cleaned_data.get('perfil', None)
                if perfil:
                    usuario.groups.add(perfil)

                self.instance.usuario = usuario
                empleado = super().save()

                # Si el empleado es jefe de departamento se le asignan todas las areas del departamento.
                if empleado.jefe_departamento:
                    areas = list(self.cleaned_data['departamento'].areas.all())
                    empleado.areas.add(*areas)

                return empleado
        except:
            logger.exception("Error al intentar crear empleado")
            self.add_error(None, forms.ValidationError(self.error_messages['transaction'], code='transaction'))
            return None
