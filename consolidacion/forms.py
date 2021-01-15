from django import forms
from grupos.models import Grupo
from common.forms import CustomModelForm, CustomForm
from .models import Visita


class VisitaForm(CustomModelForm):
    """
    Formulario para crear visitas en el modulo de consolidacion.
    """

    class Meta:
        model = Visita
        fields = (
            'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido',
            'direccion', 'telefono', 'email', 'genero', 'estado_civil', 'edad'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['primer_nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['primer_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['estado_civil'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefono'].widget.attrs.update({'class': 'form-control'})
        self.fields['genero'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['edad'].widget.attrs.update({'class': 'form-control'})


class FormularioAsignarGrupoVisita(forms.Form):
    """
    Formulario de Asignacion de visita a grupo.
    """

    visita = forms.ModelChoiceField(queryset=Visita.objects.filter(retirado=False))
    grupo = forms.ModelChoiceField(queryset=Grupo.objects.activos())

    def __init__(self, *args, **kwargs):
        super(FormularioAsignarGrupoVisita, self).__init__(*args, **kwargs)
