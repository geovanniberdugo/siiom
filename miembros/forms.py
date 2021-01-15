# -*- coding: utf-8 -*-
from PIL import Image
from io import BytesIO
from django import forms
from django.db.models import Q
from django.contrib import auth
from django.urls import reverse_lazy
from django.utils.http import is_safe_url
from django.contrib.auth import forms as auth_forms, get_user_model
from django.utils.translation import ugettext_lazy as _lazy, ugettext as _

from common.forms import CustomForm, CustomModelForm
from grupos.models import Grupo
from grupos.forms import ArchivarGrupoForm
from .models import Miembro, Zona, Barrio, CambioTipo, TipoMiembro

__all__ = (
    'FormularioLiderAgregarMiembro', 'FormularioAdminAgregarMiembro',
    'FormularioAsignarGrupo', 'FormularioCrearZona', 'FormularioCrearBarrio', 'NuevoMiembroForm',
    'TrasladarMiembroForm', 'DesvincularLiderGrupoForm', 'FormularioCrearTipoMiembro', 'FormularioCambioTipoMiembro',
    'FormularioAsignarUsuario', 'FormularioTipoMiembros',
    'FormularioFotoPerfil', 'FormularioInformacionIglesiaMiembro', 'LoginForm'
)


class LoginForm(CustomForm):
    """
    Formulario para el logeo de usuarios en el sistema.
    """

    error_messages = {
        'invalid_login': _lazy('Email y contraseña no coinciden.')
    }

    next = forms.CharField(max_length=255, required=False, widget=forms.HiddenInput)
    email = forms.EmailField(label=_lazy('Email'))
    password = forms.CharField(
        max_length=255, label=_lazy('Contraseña'), widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': self.input_css_class, 'placeholder': _lazy('Email (usuario)')})
        self.fields['password'].widget.attrs.update(
            {'class': self.input_css_class, 'placeholder': _lazy('Contraseña')})

    def clean(self):
        cleaned_data = super().clean()

        email = self.cleaned_data.get('email', '')
        password = self.cleaned_data.get('password', '')

        if password and email:
            self.usuario = auth.authenticate(email=email, password=password)

            if self.usuario is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'], code='invalid_login'
                )

        return cleaned_data

    def get_user(self):
        return getattr(self, 'usuario', None)

    def is_safe_url(self, *args, **kwargs):
        """
        Verifica que la url a la cual se va a redirigir sea segura.

        :rtype bool:

        :param \\*args:
            Argumentos de la funcion ``is_safe_url``.

        :param \\*\\*kwargs:
            Diccionario de argumentos de la funcion ``is_safe_url``.
        """
        return is_safe_url(allowed_hosts=self.request.get_host(), *args, **kwargs)

    def get_next(self):
        """
        :returns:
            El string de la url a la cual hará la redireccion una vez el formulario
            este válido.

        :rtype str:
        """
        if self.get_user() is not None and self.usuario.has_perm('miembros.es_administrador'):
            next = reverse_lazy('administracion')
        else:
            next = reverse_lazy('miembros:miembro_inicio')

        url = self.cleaned_data.get('next', next)

        if self.is_safe_url(url=url):
            return url
        return next


class FormularioLiderAgregarMiembro(forms.ModelForm):
    """
    Formulario para crear miembros.
    """

    required_css_class = 'requerido'
    error_css_class = 'has-error'

    def __init__(self, g='', c=None, *args, **kwargs):
        super(FormularioLiderAgregarMiembro, self).__init__(*args, **kwargs)
        if g != '':
            if g == 'M':
                g = 'F'
            else:
                g = 'M'

        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['primer_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefono'].widget.attrs.update({'class': 'form-control'})
        self.fields['celular'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_nacimiento'].widget.attrs.update({'class': 'form-control', 'data-mask': '00/00/0000'})
        self.fields['cedula'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['profesion'].widget.attrs.update({'class': 'form-control'})
        self.fields['barrio'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['genero'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['estado_civil'].widget.attrs.update({'class': 'selectpicker'})

    class Meta:
        model = Miembro
        fields = (
            'nombre', 'primer_apellido', 'segundo_apellido', 'telefono',
            'celular', 'direccion', 'fecha_nacimiento', 'cedula', 'email',
            'profesion', 'barrio', 'genero', 'estado_civil'
        )


class FormularioAdminAgregarMiembro(forms.ModelForm):
    """
    Formulario para agregar miembros un administrador
    """
    required_css_class = 'requerido'
    error_css_class = 'has-error'

    def __init__(self, g='', *args, **kwargs):
        super(FormularioAdminAgregarMiembro, self).__init__(*args, **kwargs)
        if g != '':
            if g == 'M':
                g = 'F'
            else:
                g = 'M'
            queryset = Miembro.objects.filter(Q(estado_civil='S') | Q(estado_civil='V') | Q(estado_civil='D'), genero=g)
            self.fields['conyugue'].queryset = queryset

            if self.instance.conyugue:
                conyugue = Miembro.objects.filter(id=self.instance.conyugue.id)
                self.fields['conyugue'].queryset = queryset | conyugue

        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['primer_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefono'].widget.attrs.update({'class': 'form-control'})
        self.fields['celular'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_nacimiento'].widget.attrs.update({'class': 'form-control', 'data-mask': '00/00/0000'})
        self.fields['cedula'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['profesion'].widget.attrs.update({'class': 'form-control'})
        self.fields['barrio'].widget.attrs.update({'class': 'form-control'})
        self.fields['genero'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['estado_civil'].widget.attrs.update({'class': 'selectpicker'})
        # self.fields['estado'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['conyugue'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})

    class Meta:
        model = Miembro
        fields = (
            'nombre', 'primer_apellido', 'segundo_apellido', 'telefono',
            'celular', 'direccion', 'fecha_nacimiento', 'cedula', 'email',
            'profesion', 'barrio', 'genero', 'estado_civil', 'conyugue'
        )


class FormularioAsignarGrupo(forms.ModelForm):
    """
    Formulario para asignar grupos de amistad a miembros que no asistan a grupos.
    """
    required_css_class = 'requerido'
    error_css_class = 'has-error'

    def __init__(self, *args, **kwargs):
        super(FormularioAsignarGrupo, self).__init__(*args, **kwargs)
        self.fields['grupo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})

    class Meta:
        model = Miembro
        fields = ('grupo', )


class FormularioCrearZona(forms.ModelForm):
    """
    Formulario para crear y editar zonas.
    """

    required_css_class = 'requerido'
    error_css_class = 'has-error'

    def __init__(self, *args, **kwargs):
        super(FormularioCrearZona, self).__init__(*args, **kwargs)

        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['nombre'].required = True

    def clean(self):
        nam = self.cleaned_data.get('nombre')

        if not nam:
            self.add_error('nombre', "Este campo es requerido")
        return super(FormularioCrearZona, self).clean()

    class Meta:
        model = Zona
        fields = ('nombre', )


class FormularioCrearBarrio(forms.ModelForm):
    """
    Formulario para crear y editar barrios.
    """
    required_css_class = 'requerido'
    error_css_class = 'has-error'

    def __init__(self, *args, **kwargs):
        super(FormularioCrearBarrio, self).__init__(*args, **kwargs)

        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Barrio
        fields = ('nombre', )


class FormularioCrearTipoMiembro(forms.ModelForm):
    """
    Formulario para crear y editar los tipos de miembros.
    """
    required_css_class = 'requerido'
    error_css_class = 'has-error'

    def __init__(self, *args, **kwargs):
        super(FormularioCrearTipoMiembro, self).__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = TipoMiembro
        fields = ('nombre', )


class FormularioCambioTipoMiembro(forms.ModelForm):
    """
    Formulario para crear los cambios de tipos de miembro.
    """
    required_css_class = 'requerido'
    error_css_class = 'has-error'

    def __init__(self, idm='', *args, **kwargs):
        super(FormularioCambioTipoMiembro, self).__init__(*args, **kwargs)  # populates the post
        self.fields['nuevoTipo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.idm = idm
        if idm != '':
            m = Miembro.objects.get(id=idm)
            tipos = CambioTipo.objects.filter(miembro=m).values('nuevoTipo')
            self.fields['nuevoTipo'].queryset = TipoMiembro.objects.all().exclude(id__in=tipos)

    class Meta:
        model = CambioTipo
        fields = ('nuevoTipo', )


class FormularioAsignarUsuario(forms.Form):
    """
    Formulario para crear y asignar usuarios a los miembros.
    """
    required_css_class = 'requerido'
    error_css_class = 'has-error'

    email = forms.EmailField(label='Verificar correo:')
    contrasena = forms.CharField(widget=forms.PasswordInput(render_value=False), max_length=20, label='Contraseña:')
    contrasenaVerificacion = forms.CharField(widget=forms.PasswordInput(render_value=False),
                                             max_length=20, label='Verifique contraseña:')

    def __init__(self, *args, **kwargs):
        super(FormularioAsignarUsuario, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['contrasena'].widget.attrs.update({'class': 'form-control'})
        self.fields['contrasenaVerificacion'].widget.attrs.update({'class': 'form-control'})


class FormularioFotoPerfil(forms.ModelForm):
    """
    Formulario para manejar las validaciones de la imagen de perfil de el miembro,
    y manejar el tamaño de la misma.
    """
    error_css_class = 'has-error'

    def __init__(self, *args, **kwargs):
        return super(FormularioFotoPerfil, self).__init__(*args, **kwargs)

    def clean_foto_perfil(self):
        foto = self.cleaned_data['foto_perfil']

        if foto is None:
            foto = 'static/Imagenes/log.jpg'

        try:
            from django.core.files.images import get_image_dimensions

            w, h = get_image_dimensions(foto)

            max_width = max_height = 2000

            if w > max_width or h > max_height:
                self.add_error('foto_perfil', 'Tamaño maximo aceptado de %sx%s y has puesto una de \
                    %sx%s' % (max_width, max_height, w, h))

        except AttributeError:
            pass

        return foto

    def clean(self):
        return super(FormularioFotoPerfil, self).clean()

    def save(self, commit=True):
        image_field = self.cleaned_data.get('foto_perfil')
        image_file = BytesIO(image_field.read())
        image = Image.open(image_file)
        w, h = image.size

        image_file = BytesIO()
        image.save(image_file, 'png', quality=90)

        image_field.file = image_file

        return super(FormularioFotoPerfil, self).save(commit=commit)

    class Meta:
        model = Miembro
        fields = ('foto_perfil', )


class FormularioInformacionIglesiaMiembro(forms.ModelForm):
    """
    Formulario para cambiar el estado de un miembro.
    """
    error_css_class = 'has-error'

    def __init__(self, *args, **kwargs):
        super(FormularioInformacionIglesiaMiembro, self).__init__(*args, **kwargs)
        self.fields['estado'].widget.attrs.update({'class': 'selectpicker'})

    class Meta:
        model = Miembro
        fields = ('estado', )


class FormularioTipoMiembros(forms.ModelForm):
    """
    Formulario para cambiar el tipo de miembro de un usuario.
    """
    error_css_class = 'has-error'

    tipos = forms.ModelMultipleChoiceField(queryset=TipoMiembro.objects.all(), widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(FormularioTipoMiembros, self).__init__(*args, **kwargs)
        if self.instance:
            tipos = CambioTipo.objects.filter(miembro=self.instance)
            self.fields['tipos'].initial = [tipo.nuevoTipo.id for tipo in tipos]
            # self.fields['tipos'].required = False

    class Meta:
        model = CambioTipo
        exclude = ('miembro', 'autorizacion', 'nuevoTipo', 'anteriorTipo', 'fecha')


class NuevoMiembroForm(CustomModelForm):
    """
    Formulario para la creación de un miembro de una iglesia.
    """

    class Meta:
        model = Miembro
        fields = [
            'nombre', 'primer_apellido', 'segundo_apellido', 'genero', 'telefono', 'celular', 'fecha_nacimiento',
            'cedula', 'direccion', 'barrio', 'email', 'profesion', 'estado_civil'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['genero'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['cedula'].widget.attrs.update({'class': 'form-control'})
        self.fields['celular'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefono'].widget.attrs.update({'class': 'form-control'})
        self.fields['profesion'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        self.fields['estado_civil'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['primer_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_nacimiento'].widget.attrs.update({'class': 'form-control'})
        self.fields['barrio'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})


class TrasladarMiembroForm(CustomForm):
    """
    Formulario para el traslado de un miembro de un grupo a otro.
    """

    nuevo = forms.ModelChoiceField(
        queryset=Grupo.objects.prefetch_related('lideres').all(), label=_lazy('Trasladar a')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nuevo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})

    def trasladar(self, miembro):
        miembro.trasladar(self.cleaned_data['nuevo'])


class DesvincularLiderGrupoForm(ArchivarGrupoForm):
    """
    Formulario para desvincular a los lideres de grupos de amistad.
    """

    lider = forms.ModelChoiceField(
        queryset=Miembro.objects.all(), label=_lazy('Lider')
    )
    nuevo_lider = forms.ModelChoiceField(
        queryset=Miembro.objects.none(), label=_lazy('Nuevo Lider'),
        required=False, empty_label=_lazy('NO REEMPLAZAR LIDER'),
        help_text=_lazy('Si escoge esta opcion, el líder escogido, reemplazará al líder el cual quiere desvincular.')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lider'].widget.attrs.update({'class': 'form-control'})
        self.fields['nuevo_lider'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['grupo'].required = False

        if self.is_bound:
            lider = self.data.get('lider', None)

            if lider is not None:
                lider = Miembro.objects.get(pk=lider)
                self.fields['nuevo_lider'].queryset = Miembro.objects.lideres_disponibles().filter(
                    grupo__red_id=lider.grupo.red_id)

    def clean(self):
        """Clean override. Se verifica que el usuario exista antes de enviar email."""
        cleaned_data = super().clean()

        lider = cleaned_data.get('lider', None)
        nuevo_lider = cleaned_data.get('nuevo_lider', None)
        miembros = cleaned_data.get('seleccionados', Miembro.objects.none())
        grupo_destino = cleaned_data.get('grupo_destino', None)

        if lider is not None and lider.grupo_lidera is not None:
            if not lider.grupo_lidera.is_leaf():
                if lider.grupo_lidera.lideres.count() == 1 and nuevo_lider is None:
                    self.add_error(
                        'nuevo_lider',
                        forms.ValidationError(
                            _lazy("""
                                Debes escoger un nuevo lider que reemplaze al anterior, \
                                ya que el grupo actual tiene grupos descendientes"""),
                            code='required'
                        )
                    )
            elif lider.grupo_lidera.lideres.count() == 1:  # se va a archivar
                cleaned_data['grupo'] = lider.grupo_lidera
                if miembros.exists() and not grupo_destino:
                    self.add_error('grupo_destino', forms.ValidationError(
                        self.error_messages['sin_destino'], code='sin_destino'))
        return cleaned_data

    def desvincular_lider(self):
        """Metodo para desvincular a un lider de un grupo de amistad."""

        lider = self.cleaned_data['lider']
        nuevo_lider = self.cleaned_data.get('nuevo_lider', None)
        grupo = lider.grupo_lidera

        if grupo is not None and grupo.lideres.count() <= 1:
            if grupo.is_leaf():
                self.cleaned_data['mantener_lideres'] = False
                self.archiva_grupo()

        if nuevo_lider is not None and grupo:
            grupo.lideres.add(nuevo_lider)

        lider.update(grupo=None, grupo_lidera=None, estado=Miembro.INACTIVO)


class CambiarContrasenaForm(CustomForm, auth_forms.PasswordChangeForm):
    """Formulario que permite a un usuario cambiar su contraseña.

    Extiende del formulario PasswordChangeForm de auth.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})


class PasswordResetForm(CustomForm, auth_forms.PasswordResetForm):
    """Formulario que permite a un usuario ingresar su email para poder resetear su contraseña.

    Extendiende del formulario PasswordResetForm de auth.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        label = self.fields['email'].label
        self.fields['email'].widget.attrs.update({'class': self.input_css_class, 'placeholder': label})

    def clean_email(self):
        """Verifica que el email pertenezca a un usuario."""

        email = self.cleaned_data['email']
        if not get_user_model()._default_manager.filter(email=email).exists():
            raise forms.ValidationError(
                _('No se encontro ningún usuario asociado al email ingresado.'),
                code='invalid'
            )

        return email

    def save(self, **kwargs):
        request = kwargs['request']
        super().save(domain_override=request.get_host(), **kwargs)


class SetPasswordForm(CustomForm, auth_forms.SetPasswordForm):
    """Formulario que permite a un usuario resetear su contraseña.

    Extendiende del formulario PasswordResetForm de auth.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        label1 = self.fields['new_password1'].label
        label2 = self.fields['new_password2'].label
        self.fields['new_password1'].widget.attrs.update({'class': self.input_css_class, 'placeholder': label1})
        self.fields['new_password2'].widget.attrs.update({'class': self.input_css_class, 'placeholder': label2})


class ResetearContrasenaAdminForm(CustomForm):
    """Formulario que permite resetear la contraseña de un miembro."""

    miembro = forms.ModelChoiceField(queryset=Miembro.objects.all())

    def resetear(self):
        """Resetea la contraseña."""

        miembro = self.cleaned_data['miembro']
        miembro.resetear_contrasena()
