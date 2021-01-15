# Django Package
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.core.exceptions import ValidationError

# Locale Apps
from .models import Caso, Comentario, Invitacion, Documento
from .utils import get_sender

# Apps
from organizacional.models import Empleado
from common.constants import CONTENT_TYPES

# Python Package
import re


class ModelFormBase(forms.ModelForm):
    error_css_class = 'has-error'


class FormBase(forms.Form):
    error_css_class = 'has-error'


class FormularioCaso(ModelFormBase):
    """
    Formulario para la creacion de casos en el sistema
    """

    class Meta:
        model = Caso
        fields = (
            'fecha_acontecimiento', 'nombre', 'identificacion',
            'direccion', 'telefono', 'email', 'descripcion', 'asunto'
        )

    def __init__(self, *args, **kwargs):
        super(FormularioCaso, self).__init__(*args, **kwargs)
        self.fields['fecha_acontecimiento'].widget.attrs.update({'class': 'form-control', 'data-mask': '00/00/00'})
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['descripcion'].widget.attrs.update({'class': 'form-control'})
        self.fields['identificacion'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefono'].widget.attrs.update({'class': 'form-control'})
        self.fields['asunto'].widget.attrs.update({'class': 'form-control'})


class FormularioAgregarMensaje(ModelFormBase):
    """
    Formulario para los mensajes que hacen los integrantes de un caso
    """

    class Meta:
        model = Comentario
        fields = ('mensaje', 'empleado', 'caso', 'importante')

    def __init__(self, *args, **kwargs):
        caso = kwargs.pop('caso', None)
        super(FormularioAgregarMensaje, self).__init__(*args, **kwargs)
        self.fields['empleado'].widget = forms.HiddenInput()
        self.fields['caso'].widget = forms.HiddenInput()
        self.fields['mensaje'].widget.attrs.update({'placeholder': 'Ingresa un mensaje aquí...'})
        self.fields['importante'].widget.attrs.update({'class': 'hidden'})

        if hasattr(caso, 'cerrado') and caso.cerrado:
            self.fields['mensaje'].widget.attrs.update({'readonly': 'readonly', 'style': 'background-color: #e6e6e6;'})


class FormularioAgregarIntegrante(ModelFormBase):
    """
    docstring for FormularioAgregarIntegrante
    """

    class Meta:
        model = Invitacion
        fields = ('mensaje', 'caso', 'emisor')

    integrante = forms.CharField(max_length=255, label=_('Integrante'))

    def __init__(self, *args, **kwargs):
        super(FormularioAgregarIntegrante, self).__init__(*args, **kwargs)
        self.fields['integrante'].widget.attrs.update({'class': 'autocompletar'})
        self.fields['caso'].widget = forms.HiddenInput()
        self.fields['emisor'].widget = forms.HiddenInput()

    def clean(self, *args, **kwargs):
        cleaned_data = super(FormularioAgregarIntegrante, self).clean(*args, **kwargs)

        if 'integrante' in cleaned_data:
            match = re.compile(r'\(([^)]+)\)')
            regex = match.findall(cleaned_data['integrante'])
            try:
                self.receptor = Empleado.objects.get(cedula=regex[0])
            except:
                self.add_error('integrante', _('Este Empleado No existe, por favor recarga la página'))

    def get_receptor(self):
        """
        Retorna el receptor que consiguió a partir de el formulario
        """

        if self.is_bound and not self.errors and hasattr(self, 'receptor'):
            return self.receptor
        return None


class FormularioEliminarInvitacion(FormBase):
    """
    Formulario para eliminar una invitacion
    """

    integrante = forms.ModelChoiceField(queryset=Empleado.objects.none(), label=_('Integrante a eliminar'))

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('query', None)
        super(FormularioEliminarInvitacion, self).__init__(*args, **kwargs)
        self.fields['integrante'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})

        if queryset:
            self.fields['integrante'].queryset = queryset


class FormularioCerrarCaso(FormularioAgregarMensaje):
    """
    Formulario con el cual se cierra un caso, y se envia un e-mail a el usuario final
    """

    def __init__(self, *args, **kwargs):
        caso = kwargs.pop('caso', None)
        super(FormularioCerrarCaso, self).__init__(*args, **kwargs)
        # self.fields['importante'].widget.attrs.update({'class': 'hidden'})
        self.fields['mensaje'].widget.attrs.update({'class': 'form-control'})
        self.fields['importante'].initial = True
        self.fields['caso'].initial = caso.id
        self.fields['empleado'].initial = caso.empleado_cargo.id

    def enviar_email(self):
        if self.is_valid() and 'mensaje' in self.cleaned_data and 'caso' in self.cleaned_data:
            self._enviar_email()
        else:
            raise ValidationError(_('mensaje or caso not in self.cleaned_data'))

    def _enviar_email(self):
        if self.is_valid() and 'mensaje' in self.cleaned_data and 'caso' in self.cleaned_data:
            mensaje = \
                """
                ¡Hola!\n
                Tenemos respuesta a su solicitud número %(id_caso)d\n
                    Su solicitud fue:
                        "%(descripcion)s"\n
                    Respuesta:
                        "%(respuesta)s"\n
                Estamos para servirle.
                """
            ASUNTO = 'Respuesta a Su Inquietud'
            SENDER = get_sender()
            _data = {
                'id_caso': self.cleaned_data['caso'].id,
                'descripcion': self.cleaned_data['caso'].descripcion,
                'respuesta': self.cleaned_data['mensaje']
            }
            send_mail(
                ASUNTO,
                mensaje % _data,
                SENDER,
                ('{}'.format(self.cleaned_data['caso'].email), ),
                fail_silently=False
            )
        else:
            raise ValidationError(_('mensaje or caso not in self.cleaned_data'))


class FormularioEditarCaso(ModelFormBase):
    """
    Formulario para editar los datos de la persona que ingresa un caso
    """

    class Meta:
        model = Caso
        fields = (
            'email', 'telefono', 'direccion',
        )

    def __init__(self, *args, **kwargs):
        super(FormularioEditarCaso, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefono'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})


class FormularioAgregarArchivoCaso(ModelFormBase):
    """
    Formulario para agregar archivos a los casos
    """

    class Meta:
        model = Documento
        fields = ('archivo', )

    def __init__(self, *args, **kwargs):
        super(FormularioAgregarArchivoCaso, self).__init__(*args, **kwargs)

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo', None)

        if archivo is not None:
            if archivo.content_type not in CONTENT_TYPES.values():
                self.add_error('archivo', _('Formato de Archivo No Soportado'))
            elif len(archivo.name.split('.')) == 1:
                self.add_error('archivo', _('Formato de Archivo No Econtrado'))

            return archivo
        raise ValidationError(_("No se econtro, el archivo"))
