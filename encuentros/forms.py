# Django
from django import forms

# Apps
from .models import Encuentro, Encontrista

from common.forms import CustomModelForm, CustomForm
from grupos.models import Grupo, Red
from miembros.models import Miembro


class CrearEncuentroForm(CustomModelForm):
    """
    Formulario para crear encuentros
    """

    red = forms.ModelChoiceField(queryset=Red.objects.all())

    class Meta:
        model = Encuentro
        fields = (
            'fecha_inicial', 'fecha_final', 'hotel',
            'grupos', 'coordinador', 'tesorero',
            'direccion', 'observaciones',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.id is not None:
            self.fields['grupos'].queryset = self.instance.grupos
        else:
            self.fields['grupos'].queryset = Grupo.objects.none()  # prefetch_related('lideres').all()
        self.fields['coordinador'].queryset = Miembro.objects.none()
        self.fields['tesorero'].queryset = Miembro.objects.none()
        self.fields['fecha_inicial'].widget.attrs.update({'class': 'form-control', 'data-mask': '00/00/00 00:00'})
        self.fields['fecha_final'].widget.attrs.update({'class': 'form-control', 'data-mask': '00/00/00'})
        self.fields['coordinador'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['red'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['tesorero'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['observaciones'].widget.attrs.update({'class': 'form-control', 'rows': '5'})
        self.fields['grupos'].widget.attrs.update(
            {
                'class': 'selectpicker',
                'data-live-search': 'true',
                'data-actions-box': 'true',
                'liveSearchPlaceholder': 'Busca por nombre de líder',
                'noneSelectedText': 'SIN ESCOGER'
            }
        )
        self.fields['hotel'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})

        if self.is_bound:
            red = self.data.get('red', None) or None
            if hasattr(self.data, 'getlist'):
                grupos = self.data.getlist('grupos', None) or None
            else:
                grupos = self.data.get('grupos', None) or None

            if red is not None:
                try:
                    red = Red.objects.get(id=red)
                    if grupos:
                        self.fields['grupos'].queryset = Grupo.objects.filter(id__in=grupos).prefetch_related('lideres')
                    else:
                        self.fields['grupos'].queryset = Grupo.objects.none()
                except Red.DoesNotExist:
                    self.fields['grupos'].queryset = Grupo.objects.none()
            else:
                self.fields['grupos'].queryset = Grupo.objects.none()

            queryset_miembros = Miembro.objects.none()
            if grupos is not None:
                grupos = Grupo.objects.filter(id__in=grupos)
                if grupos.exists():
                    ids_lideres = []
                    for grupo in grupos:
                        for _id in grupo.grupos_red.prefetch_related('lideres').values_list('lideres__id', flat=True):
                            if _id not in ids_lideres:
                                ids_lideres.append(_id)

                    queryset_miembros = Miembro.objects.filter(
                        id__in=ids_lideres
                    ).select_related('grupo_lidera', 'grupo').distinct()

            self.fields['tesorero'].queryset = queryset_miembros
            self.fields['coordinador'].queryset = queryset_miembros


class NuevoEncontristaForm(forms.ModelForm):
    """
    Formulario Para la Creacion de Encontristas
    """
    error_css_class = 'has-error'

    class Meta:
        model = Encontrista
        fields = (
            'primer_nombre', 'segundo_nombre', 'primer_apellido',
            'segundo_apellido', 'talla', 'genero', 'identificacion',
            'email', 'grupo',
        )

    def __init__(self, encuentro=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['primer_nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['primer_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['segundo_apellido'].widget.attrs.update({'class': 'form-control'})
        self.fields['talla'].widget.attrs.update({'class': 'form-control'})
        self.fields['identificacion'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

        if encuentro:
            grupos = encuentro.grupos.all()
            _ids = []
            for grupo in grupos:
                for _id in grupo.grupos_red.values_list('id', flat=True):
                    if _id not in _ids:
                        _ids.append(_id)
            self.fields['grupo'].queryset = Grupo.objects.filter(id__in=_ids)
        else:
            self.fields['grupo'].queryset = Grupo.objects.filter(id=self.instance.grupo.id)
        self.fields['grupo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['genero'].widget.attrs.update({'class': 'selectpicker'})


class EditarEncuentroForm(CrearEncuentroForm):
    """
    Formulario para la edicion de encuentros.
    """

    def __init__(self, *args, **kwargs):
        super(EditarEncuentroForm, self).__init__(*args, **kwargs)
        self.fields['coordinador'].widget.attrs.update({'readonly': ''})
        self.fields['tesorero'].widget.attrs.update({'readonly': ''})

        if not self.is_bound:
            if self.instance:
                if any(self.instance.grupos.all()):
                    self.fields['red'].initial = self.instance.grupos.first().red

                self.fields['coordinador'].queryset = Miembro.objects.filter(id=self.instance.coordinador.id)
                self.fields['coordinador'].initial = self.instance.coordinador

                self.fields['tesorero'].queryset = Miembro.objects.filter(id=self.instance.tesorero.id)
                self.fields['tesorero'].initial = self.instance.tesorero


class FormularioObtenerGrupoAPI(CustomForm):
    """Formulario para el uso desde la api, para obtener grupos."""
    red = forms.ModelChoiceField(queryset=Red.objects.all())
    value = forms.CharField(max_length=255)


class FormularioObtenerTesoreroCoordinadorAPI(CustomForm):
    """Formulario para el uso desde la api, para obtener miembros tesoreros y coordinadores."""
    grupos = forms.ModelMultipleChoiceField(queryset=Grupo.objects.all())
    value = forms.CharField(max_length=255)
