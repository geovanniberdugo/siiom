from django import forms
from django.utils.translation import ugettext_lazy as _

from common.forms import CustomModelForm, CustomForm, ArrayFieldSelectMultiple
from miembros.models import Miembro
from grupos.models import Grupo

from . import resources, models

class MateriaForm(CustomModelForm):
    """
    Formulario para crear las Materias.
    """

    class Meta:
        model = models.Materia
        fields = ('nombre', 'grupos_minimo', 'dependencia', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['grupos_minimo'].widget.attrs.update({'class': 'form-control'})
        self.fields['dependencia'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})


class PrioridadMixin:
    OBJETO = _('')

    error_messages = {
        'prioridad_exists': _('Ya existe un %s con esta prioridad.' % OBJETO)
    }


class ModuloForm(PrioridadMixin, CustomModelForm):
    """
    Formulario para crear los módulos de cada materia.
    """

    OBJETO = _('módulo')

    class Meta:
        model = models.Modulo
        fields = ('nombre', 'prioridad', )

    def __init__(self, materia=None, *args, **kwargs):
        self.materia = materia
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['prioridad'].widget.attrs.update({'class': 'form-control'})

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        if self.materia is not None:
            if 'prioridad' in cleaned_data and self.materia.modulos.filter(prioridad=cleaned_data.get('prioridad')).exists():
                self.add_error(
                    'prioridad',
                    forms.ValidationError(self.error_messages['prioridad_exists'], code='prioridad_exists')
                )
        else:
            if self.instance.materia.modulos.filter(
               prioridad=cleaned_data.get('prioridad')).exclude(id=self.instance.id).exists():
                self.add_error(
                    'prioridad',
                    forms.ValidationError(self.error_messages['prioridad_exists'], code='prioridad_exists')
                )
        return cleaned_data

    def save(self, commit=True, *args, **kwargs):
        if commit and self.materia is not None:
            self.instance.materia = self.materia
        return super().save(commit=commit, *args, **kwargs)


class SesionForm(PrioridadMixin, CustomModelForm):
    """
    Formulario para crear una sesión.
    """

    OBJETO = _('sesión')

    class Meta:
        model = models.Sesion
        fields = ('nombre', 'prioridad', )

    def __init__(self, modulo=None, *args, **kwargs):
        self.modulo = modulo
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['prioridad'].widget.attrs.update({'class': 'form-control'})

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)

        if self.modulo is not None:
            if 'prioridad' in cleaned_data and self.modulo.sesiones.filter(prioridad=cleaned_data.get('prioridad')).exists():
                self.add_error(
                    'prioridad',
                    forms.ValidationError(self.error_messages['prioridad_exists'], code='prioridad_exists')
                )
        else:
            if self.instance.modulo.sesiones.filter(
               prioridad=cleaned_data.get('prioridad')).exclude(id=self.instance.id).exists():
                self.add_error(
                    'prioridad',
                    forms.ValidationError(self.error_messages['prioridad_exists'], code='prioridad_exists')
                )
        return cleaned_data

    def save(self, commit=True, *args, **kwargs):
        if commit and self.modulo is not None:
            self.instance.modulo = self.modulo
        return super().save(commit=commit, *args, **kwargs)


class SalonForm(CustomModelForm):
    """Formulario de creación de salones."""

    class Meta:
        model = models.Salon
        fields = ['nombre', 'capacidad', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['capacidad'].widget.attrs.update({'class': 'form-control'})


class CursoForm(CustomModelForm):
    """Formulario para cursos."""

    error_messages = {
        'current_curso': _('Ya existe un curso en este horario.')
    }

    # cambio el queryset a lideres, en teoria debe salir una lista larga de lideres
    profesor = forms.ModelMultipleChoiceField(
        queryset=Miembro.objects.maestros(), label=_('Profesores'))
    # fecha_inicio = forms.DateField(widget=forms.HiddenInput())

    class Meta:
        model = models.Curso
        fields = [
            'precio', 'hora_inicio', 'hora_fin', 'fecha_inicio',
            'fecha_fin', 'salon', 'materia', 'dia', 'profesor', 'color',
        ]
        widgets = {
            'dia': ArrayFieldSelectMultiple(
                choices=models.Curso.DIAS_SEMANA, attrs={'class': 'selectpicker'}),
            'color': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['precio'].widget.attrs.update({'class': 'form-control'})
        self.fields['hora_inicio'].widget.attrs.update({'class': 'form-control', 'data-mask': '00:00'})
        self.fields['hora_fin'].widget.attrs.update({'class': 'form-control', 'data-mask': '00:00'})
        self.fields['fecha_inicio'].widget.attrs.update({'class': 'form-control', 'data-mask': '0000-00-00'})
        self.fields['fecha_fin'].widget.attrs.update({'class': 'form-control', 'data-mask': '0000-00-00'})
        self.fields['salon'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['materia'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['profesor'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['profesor'].queryset = Miembro.objects.maestros()

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean(*args, **kwargs)
        hora_inicio = cleaned_data.get('hora_inicio', '') or None
        hora_fin = cleaned_data.get('hora_fin', '') or None
        fecha_inicio = cleaned_data.get('fecha_inicio') or None
        fecha_fin = cleaned_data.get('fecha_fin', '') or None
        salon = cleaned_data.get('salon', '') or None
        dias = cleaned_data.get('dia', '')

        if fecha_inicio is not None and fecha_fin is not None and salon is not None:
            if hora_inicio is not None and hora_fin is not None:
                dia = dias
                current = models.Curso.objects.filter(
                    salon=salon, fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio, dia__overlap=dia).activos().filter(
                        hora_inicio__lte=hora_fin, hora_fin__gte=hora_inicio
                    )
                if current.exists():
                    raise forms.ValidationError(self.error_messages['current_curso'], code='current_curso')

        return cleaned_data


class ReporteInstitutoForm(CustomForm):
    
    grupo = forms.ModelChoiceField(queryset=Grupo.objects.prefetch_related('lideres').all(), label=_('Grupo'))
    materias = forms.ModelMultipleChoiceField(queryset=models.Materia.objects.all(), label=_('Materias'), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].widget.attrs.update({'class': self.select_css_class, 'data-live-search': 'true'})
        self.fields['materias'].widget.attrs.update({'class': 'chosen', 'placeholder': 'Escoge algunas materias'})

    def get_lideres(self):
        if self.is_bound and not bool(self._errors):
            grupo = self.cleaned_data.get('grupo')
            grupos = grupo._grupos_red.prefetch_related('lideres')
            lideres = Miembro.objects.filter(id__in=grupos.values_list('lideres__id', flat=True))
            return lideres
        return Miembro.objects.none()

    def get_materias(self):
        if self.is_bound and not bool(self._errors):
            materias = self.cleaned_data.get('materias')
            if not materias.exists():
                materias = models.Materia.objects.all()
            return materias
        return models.Materia.objects.none()

    def get_excel(self):
        lideres = self.get_lideres()
        materias = self.get_materias()
        return resources.ReporteInstituto(data=lideres, materias=materias)

from django.forms.renderers import TemplatesSetting
class SeguimientoEstudianteForm(CustomForm):
    default_renderer = TemplatesSetting()
    curso = forms.ModelChoiceField(label=_('Curso'), queryset=models.Curso.objects.all())
    modulo = forms.ModelChoiceField(label=_('Modulo'), queryset=models.Modulo.objects.all())