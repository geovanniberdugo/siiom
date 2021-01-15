import logging
from contextlib import suppress
# Django
from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.utils.translation import ugettext as _, ugettext_lazy as _lazy

# Apps
from .models import Grupo, ReunionGAR, ReunionDiscipulado, Red, Predica, HistorialEstado, AsistenciaDiscipulado
from .utils import convertir_lista_grupos_a_queryset
from common.forms import CustomModelForm, CustomForm
from miembros.models import Miembro
from reportes.forms import FormularioRangoFechas

logger = logging.getLogger('siiom.{}'.format(__name__))


class FormularioReunionGARBase(forms.ModelForm):
    """
    Formulario base de validaciones para las reuniones GAR
    """

    error_css_class = 'has-error'
    required_css_class = 'requerido'

    no_realizo_grupo = forms.BooleanField(label=_lazy('No se realizo Realizó Grupo'), required=False)

    class Meta:
        model = ReunionGAR
        fields = (
            'fecha', 'predica', 'ofrenda', 'numeroTotalAsistentes',
            'numeroVisitas', 'numeroLideresAsistentes'
        )

    def __init__(self, *args, **kwargs):
        super(FormularioReunionGARBase, self).__init__(*args, **kwargs)
        self.fields['fecha'].widget.attrs.update({'class': 'form-control'})
        self.fields['predica'].widget.attrs.update({'class': 'form-control'})
        self.fields['numeroTotalAsistentes'].widget.attrs.update({'class': 'form-control'})
        self.fields['numeroLideresAsistentes'].widget.attrs.update({'class': 'form-control'})
        self.fields['numeroVisitas'].widget.attrs.update({'class': 'form-control'})
        self.fields['ofrenda'].widget.attrs.update({'class': 'form-control'})
        self.fields['predica'].required = False

    def clean(self, *args, **kwargs):
        cleaned_data = super(FormularioReunionGARBase, self).clean(*args, **kwargs)

        numero_lideres = cleaned_data.get('numeroLideresAsistentes', None)
        numero_asistentes = cleaned_data.get('numeroTotalAsistentes', None)
        numero_visitas = cleaned_data.get('numeroVisitas', None)
        no_realizo_grupo = cleaned_data.get('no_realizo_grupo', False)
        predica = cleaned_data.get('predica', None)

        if not no_realizo_grupo:
            if predica is None or predica == '':
                self.add_error('predica', _('Este campo es obligatorio.'))

            if numero_asistentes == 0:
                self.add_error(
                    'numeroTotalAsistentes',
                    _('Numero Total de asistentes no puede ser igual a 0, o escoja la opción de "NO Realicé Grupo"')
                )

        if numero_asistentes is not None and numero_lideres is not None and numero_visitas is not None:
            if numero_lideres > 0:
                if numero_lideres > numero_asistentes:
                    self.add_error(
                        'numeroLideresAsistentes',
                        _('Número de Líderes NO puede ser mayor a Número Total de Asistentes')
                    )
            if numero_visitas > 0:
                if numero_visitas >= numero_asistentes:
                    self.add_error(
                        'numeroVisitas', _('Número Visitas NO puede ser mayor o igual a Número Total de Asistentes')
                    )
            if numero_visitas + numero_lideres > numero_asistentes:
                self.add_error(
                    'numeroVisitas',
                    _('Asegurate que la suma de los líderes y las visitas no sea mayor a el total de asistentes')
                )
                self.add_error(
                    'numeroLideresAsistentes',
                    _('Asegurate que la suma de los líderes y las visitas no sea mayor a el total de asistentes')
                )
        else:
            raise ValidationError(_('Asegurate de Haber llenado todos los campos'))

        return cleaned_data


class FormularioEditarGrupo(forms.ModelForm):
    """
    Formulario para editar la direccion, el dia y la hora de el grupo.
    """

    error_css_class = 'has-error'
    required_css_class = 'requerido'

    class Meta:
        model = Grupo
        fields = ('direccion', 'diaGAR', 'horaGAR')

    def __init__(self, *args, **kwargs):
        super(FormularioEditarGrupo, self).__init__(*args, **kwargs)
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        self.fields['diaGAR'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['horaGAR'].widget.attrs.update({'class': 'form-control', 'data-mask': '00:00'})


class FormularioReportarReunionGrupo(FormularioReunionGARBase):
    """
    Formulario para reportar las reuniones de grupo.
    """

    error_css_class = 'has-error'
    required_css_class = 'requerido'

    class Meta(FormularioReunionGARBase.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(FormularioReportarReunionGrupo, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        return super(FormularioReportarReunionGrupo, self).clean(*args, **kwargs)


class FormularioReportarReunionGrupoAdmin(FormularioReunionGARBase):
    """
    Formulario para reportar las reuniones de grupo de amistad, desde un administrador.
    """

    error_css_class = 'has-error'
    required_css_class = 'requerido'

    class Meta(FormularioReunionGARBase.Meta):
        fields = ('grupo', ) + FormularioReunionGARBase.Meta.fields

    def __init__(self, *args, **kwargs):
        super(FormularioReportarReunionGrupoAdmin, self).__init__(*args, **kwargs)
        self.fields['grupo'].queryset = Grupo.objects.prefetch_related('lideres').activos()
        self.fields['grupo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})


class FormularioReportarReunionDiscipulado(forms.ModelForm):
    """Formulario para reportar las reuniones de discipulado."""

    error_css_class = 'has-error'
    required_css_class = 'requerido'

    class Meta:
        model = ReunionDiscipulado
        exclude = ('grupo', 'confirmacionEntregaOfrenda', 'asistentecia')

    def __init__(self, miembro, *args, **kwargs):
        super(FormularioReportarReunionDiscipulado, self).__init__(*args, **kwargs)
        self.fields['predica'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['novedades'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Novedades...'})
        self.fields['ofrenda'].widget.attrs.update({'class': 'form-control'})
        self.fields['predica'].queryset = Predica.objects.filter(miembro__in=miembro.pastores())


class FormularioCrearPredica(forms.ModelForm):
    """
    Formulario para crear predicas.
    """

    error_css_class = 'has-error'
    required_css_class = 'requerido'

    class Meta:
        model = Predica
        fields = ('miembro', 'descripcion', 'nombre')

    def __init__(self, *args, **kwargs):
        miembro = kwargs.pop('miembro', None)
        super(FormularioCrearPredica, self).__init__(*args, **kwargs)
        if miembro is not None:
            if miembro.usuario.has_perm('miembros.es_administrador'):
                grupo_pastor = Group.objects.get(name__iexact='pastor')
                self.fields['miembro'].queryset = Miembro.objects.filter(usuario__groups=grupo_pastor)
            else:
                self.fields['miembro'].queryset = Miembro.objects.filter(id=miembro.id)
                self.fields['miembro'].initial = miembro.id
        else:
            self.fields['miembro'].queryset = Miembro.objects.none()
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['miembro'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['descripcion'].widget.attrs.update({'class': 'form-control',
                                                        'placeholder': 'Descripción...',
                                                        'rows': '3'})


class FormularioEditarDiscipulado(forms.ModelForm):
    """Formulario para editar el discipulado."""

    error_css_class = 'has-error'

    class Meta:
        model = Grupo
        fields = ('diaDiscipulado', 'horaDiscipulado')

    def __init__(self, *args, **kwargs):
        super(FormularioEditarDiscipulado, self).__init__(*args, **kwargs)
        self.fields['horaDiscipulado'].widget.attrs.update({'class': 'form-control', 'data-mask': '00:00'})
        self.fields['diaDiscipulado'].widget.attrs.update({'class': 'selectpicker'})


class FormularioReportesEnviados(FormularioRangoFechas):
    """Formulario para ver los reportes enviados por un grupo."""

    grupo = forms.ModelChoiceField(queryset=Grupo.objects.none())  # .filter(estado='A'))

    def __init__(self, *args, **kwargs):
        super(FormularioReportesEnviados, self).__init__(*args, **kwargs)
        self.fields['grupo'].widget.attrs.update(
            {'class': 'selectpicker', 'data-live-search': 'true'}
        )

        if self.is_bound:
            try:
                queryset = Grupo.objects.filter(id=self.data['grupo'])
            except Grupo.DoesNotExist:
                queryset = Grupo.objects.none()

            self.fields['grupo'].queryset = queryset


class FormularioEditarReunionGAR(FormularioReunionGARBase):
    """Formulario para editar las reuniones de grupos de amistad."""

    class Meta(FormularioReunionGARBase.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(FormularioEditarReunionGAR, self).__init__(*args, **kwargs)


class FormularioSetGeoPosicionGrupo(CustomModelForm):
    """Formulario para setear la geoposicion de los grupos."""

    class Meta:
        model = Grupo
        fields = ('latitud', 'longitud', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['latitud'].required = True
        self.fields['longitud'].required = True

# ------------------

class BaseGrupoForm(CustomModelForm):
    """
    Formulario base el manejo de grupo de una iglesia.
    """

    mensaje_error = _lazy('Ha ocurrido un error al guardar el grupo. Por favor intentelo de nuevo.')
    lideres = forms.ModelMultipleChoiceField(queryset=Grupo.objects.none(), label=_lazy('Lideres'))

    class Meta:
        model = Grupo
        fields = [
            'lideres', 'direccion', 'fechaApertura', 'diaGAR', 'horaGAR', 'diaDiscipulado',
            'horaDiscipulado', 'nombre', 'barrio'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lideres'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['barrio'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['horaDiscipulado'].widget.attrs.update({'class': 'form-control time-picker'})
        self.fields['horaGAR'].widget.attrs.update({'class': 'form-control time-picker'})
        self.fields['diaDiscipulado'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['fechaApertura'].widget.attrs.update({'class': 'form-control'})
        self.fields['direccion'].widget.attrs.update({'class': 'form-control'})
        # self.fields['estado'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['diaGAR'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})

        self.fields['lideres'].queryset = Miembro.objects.lideres_disponibles()

    def save(self, commit=True):
        return super().save(commit)


class GrupoRaizForm(BaseGrupoForm):
    """
    Formulario para la creación o edición del grupo raiz.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields['lideres'].queryset = (self.fields['lideres'].queryset | self.instance.lideres.all()).distinct()
            self.fields['lideres'].initial = self.instance.lideres.all()

            choices = tuple(filter(lambda x: x[0] not in [HistorialEstado.ARCHIVADO], HistorialEstado.OPCIONES_ESTADO))
            self.fields['estado'] = forms.ChoiceField(
                choices=choices, initial=self.instance.estado, required=False, label=_lazy('Estado')
            )
            self.fields['estado'].widget.attrs.update({'class': 'selectpicker'})

    def save(self):
        try:
            with transaction.atomic():
                raiz = super().save(commit=False)
                if raiz.pk:
                    raiz.save()
                    raiz.lideres.clear()
                else:
                    raiz = Grupo.add_root(instance=raiz)

                lideres = self.cleaned_data['lideres']
                lideres.update(grupo_lidera=raiz)

                if self.instance.pk:
                    if 'estado' in self.cleaned_data and self.cleaned_data['estado'] != self.instance.estado:
                        self.instance.actualizar_estado(estado=self.cleaned_data.get('estado'))
                return raiz
        except IntegrityError:
            logger.exception("Error al intentar guardar el grupo raiz")
            self.add_error(None, forms.ValidationError(self.mensaje_error))
            return None


class NuevoGrupoForm(BaseGrupoForm):
    """
    Formulario para la creación de un grupo en una iglesia.
    """

    class Meta(BaseGrupoForm.Meta):
        fields = ['parent'] + BaseGrupoForm.Meta.fields

    def __init__(self, red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.red = red

        self.fields['parent'].required = True
        self.fields['parent'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})

        grupos_query = Grupo.objects.prefetch_related('lideres').red(red)

        if grupos_query.count() == 0:
            # grupos_query = grupos_query | Grupo.objects.prefetch_related('lideres').filter(id=Grupo.objects.raiz().id)
            grupos_query = grupos_query | convertir_lista_grupos_a_queryset([Grupo.objects.raiz()])

        self.fields['parent'].queryset = grupos_query

        # se agrega el queryset de lideres como vacio, para busqueda por ajax a la API
        self.fields['lideres'].queryset = Miembro.objects.none()

        if self.is_bound:
            # si está lleno
            if hasattr(self.data, 'getlist'):
                # busca por getlist
                lideres = self.data.getlist('lideres', [])
            else:
                # este caso solo se da, si se envian datos desde un diccionario (PRUEBAS)
                lideres = self.data.get('lideres', [])

            # se filtra por los datos que vengan con el formulario
            self.fields['lideres'].queryset = Miembro.objects.filter(id__in=lideres)

    def save(self):
        try:
            with transaction.atomic():
                grupo = super().save(commit=False)
                grupo.red = self.red

                padre = self.cleaned_data['parent']
                grupo = padre.add_child(instance=grupo)

                lideres = self.cleaned_data['lideres']
                lideres.update(grupo_lidera=grupo, grupo=padre)
                return grupo
        except IntegrityError:
            logger.exception("Error al intentar crear el grupo")
            self.add_error(None, forms.ValidationError(self.mensaje_error))
            return None


class EditarGrupoForm(NuevoGrupoForm):
    """
    Formulario para la edición de un grupo en una iglesia.
    """

    def __init__(self, *args, **kwargs):
        self.parent = kwargs['instance'].parent
        super().__init__(kwargs['instance'].red, *args, **kwargs)
        self.fields['parent'].required = False

        choices = tuple(filter(lambda x: x[0] not in [HistorialEstado.ARCHIVADO], HistorialEstado.OPCIONES_ESTADO))
        self.fields['estado'] = forms.ChoiceField(
            choices=choices, initial=self.instance.estado, label=_lazy('Estado')
        )
        self.fields['estado'].widget.attrs.update({'class': 'selectpicker'})

        if not self.is_bound:
            # si no esta bound, se agrega el queryset de acuerdo a los lideres actuales, y se marcan como initial
            self.fields['lideres'].queryset = self.fields['lideres'].initial = self.instance.lideres.all()

    def save(self):
        try:
            with transaction.atomic():
                grupo = BaseGrupoForm.save(self)
                grupo.parent = self.parent
                grupo.save()

                if 'lideres' in self.changed_data:
                    grupo.lideres.clear()
                    # padre = self.cleaned_data['parent']
                    lideres = self.cleaned_data['lideres']
                    lideres.update(grupo_lidera=grupo, grupo=self.parent)

                if 'estado' in self.changed_data:
                    self.instance.actualizar_estado(estado=self.cleaned_data.get('estado'))

                return grupo
        except IntegrityError:
            logger.exception("Error al intentar editar el grupo")
            self.add_error(None, forms.ValidationError(self.mensaje_error))
            return None


class TrasladarGrupoForm(CustomForm):
    """
    Formulario para el traslado de un grupo. En nuevo se excluyen los descendientes y el mismo.
    """

    nuevo = forms.ModelChoiceField(queryset=None)

    def __init__(self, grupo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nuevo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})

        descendientes = [grupo.id for grupo in Grupo.get_tree(grupo)]
        self.fields['nuevo'].queryset = Grupo.objects.exclude(id__in=descendientes).prefetch_related('lideres')

        self.grupo = grupo

    def trasladar(self):
        self.grupo.trasladar(self.cleaned_data['nuevo'])


class RedForm(CustomModelForm):
    """
    Formulario para la creación y edición de una red de una iglesia.
    """

    class Meta:
        model = Red
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})


class TrasladarLideresForm(CustomForm):
    """
    Formulario que permite trasladar lideres de un grupo a otro.
    """

    error_messages = {
        'es_descendiente': _lazy('El grupo destino escogido no puede ser descendiente del grupo origen.')
    }

    grupo = forms.ModelChoiceField(
        queryset=Grupo.objects.none(), label=_lazy('Grupo origen'),
        help_text=_lazy('Grupo liderado por los lideres que desea trasladar')
    )
    lideres = forms.ModelMultipleChoiceField(queryset=Miembro.objects.none(), label=_lazy('Lideres a trasladar'))
    nuevo_grupo = forms.ModelChoiceField(
        queryset=Grupo.objects.none(), label=_lazy('Grupo destino (Nuevo grupo a liderar)')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['lideres'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['nuevo_grupo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})

        self.fields['grupo'].queryset = Grupo.objects.prefetch_related('lideres')
        self.fields['nuevo_grupo'].queryset = Grupo.objects.prefetch_related('lideres')

        if self.is_bound:
            with suppress(Grupo.DoesNotExist, ValueError):
                grupo = Grupo.objects.get(pk=self.data.get('grupo', None))
                self.fields['lideres'].queryset = grupo.lideres.all()

    def clean(self):
        cleaned_data = super().clean()

        grupo = cleaned_data.get('grupo', None)
        nuevo_grupo = cleaned_data.get('nuevo_grupo', None)
        if nuevo_grupo and grupo:
            if nuevo_grupo.is_descendant_of(grupo):
                msj = self.error_messages['es_descendiente']
                self.add_error('nuevo_grupo', forms.ValidationError(msj, code='es_descendiente'))

    def trasladar(self):
        Miembro.objects.trasladar_lideres(self.cleaned_data['lideres'], self.cleaned_data['nuevo_grupo'])


class ArchivarGrupoForm(CustomForm):
    """Formulario para archivar grupos."""

    error_messages = {
        'sin_destino': _lazy('Debe escoger un grupo de destino para los discipulos y/o miembros escogidos.'),
        'mismo_grupo': _lazy('El grupo de destino, no puede ser igual al grupo que se va a eliminar.'),
    }

    grupo = forms.ModelChoiceField(
        queryset=Grupo.objects.none(), label=_lazy('Grupo a eliminar'),
        help_text=_lazy('El grupo escogido, será aquel grupo el cual se eliminará.')
    )
    grupo_destino = forms.ModelChoiceField(
        queryset=Grupo.objects.none(), label=_lazy('Grupo destino'),
        help_text=_lazy('El grupo escogido, será aquel grupo el cual se enviaran los miembros seleccionados.'),
        required=False
    )
    mantener_lideres = forms.BooleanField(
        required=False, label=_lazy('Mantener líderes en grupo origen'), initial=True,
        help_text=_lazy(
            'Al marcar esta casilla, se asegurará de que los líderes del grupo a eliminar, sigan siendo miembros \
            del grupo origen'
        )
    )
    seleccionados = forms.ModelMultipleChoiceField(queryset=Miembro.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['grupo_destino'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['grupo'].queryset = Grupo.objects.hojas().prefetch_related('lideres')

        if self.is_bound:
            grupo_destino = self.data.get('grupo_destino', None) or None
            grupo = self.data.get('grupo', None) or None

            if grupo_destino is not None:
                self.fields['grupo_destino'].queryset = Grupo.objects.filter(
                    id=grupo_destino).prefetch_related('lideres')

            if grupo is not None:
                self.fields['seleccionados'].queryset = Miembro.objects.filter(grupo_id=grupo)

    def full_clean(self, *args, **kwargs):
        if hasattr(self.data, 'getlist'):
            seleccionados = self.data.getlist('seleccionados') or []
            if seleccionados:
                with suppress(ValueError, IndexError):
                    del seleccionados[seleccionados.index('all')]
        return super().full_clean(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        grupo = cleaned_data.get('grupo', None)
        grupo_destino = cleaned_data.get('grupo_destino', None)
        seleccionados = cleaned_data.get('seleccionados', Miembro.objects.none())

        if seleccionados.exists() and not grupo_destino:
            self.add_error(
                'grupo_destino', forms.ValidationError(self.error_messages['sin_destino'], code='sin_destino')
            )

        if grupo is not None and grupo_destino is not None and grupo == grupo_destino:
            self.add_error(
                'grupo_destino', forms.ValidationError(self.error_messages['mismo_grupo'], code='mismo_grupo')
            )

        return cleaned_data

    def archiva_grupo(self):
        """
        Metodo para archivar los grupos, de acuerdo al grupo de destino y los seleccionados.
        """

        grupo = self.cleaned_data['grupo']
        seleccionados = self.cleaned_data.get('seleccionados', Miembro.objects.none())
        mantenter_lideres_en_grupo_padre = self.cleaned_data.get('mantener_lideres', False)

        with transaction.atomic():
            if seleccionados:
                grupo_destino = self.cleaned_data['grupo_destino']
                seleccionados.update(grupo=grupo_destino)

            query_miembros = grupo.miembros.all()

            grupo.actualizar_estado(estado=HistorialEstado.ARCHIVADO)

            if mantenter_lideres_en_grupo_padre:
                grupo.lideres.all().update(grupo_lidera=None)
            else:
                query_miembros |= grupo.lideres.all()
            query_miembros.update(grupo=None, grupo_lidera=None)


class ReportarReunionDiscipuladoAdminForm(CustomModelForm):
    """Formulario para que un administrador pueda reportar una reunión de discipulado."""

    ERROR_MESSAGES = {
        'multiples_reuniones': _lazy(
            'Oops! Se han encontrado multiples reuniones para esta predica. Un administrador ha sido avisado, puedes intentar con otro grupo y predica mientras se corrige tu problema.'
        )
    }

    asistencia = forms.ModelMultipleChoiceField(queryset=Miembro.objects.none())

    class Meta:
        model = ReunionDiscipulado
        fields = ['grupo', 'predica', 'novedades', 'ofrenda', 'asistencia']
    
    def __init__(self, miembro, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['predica'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['grupo'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})
        self.fields['novedades'].widget.attrs.update({'class': 'form-control'})
        self.fields['ofrenda'].widget.attrs.update({'class': 'form-control'})

        grupos_query = Grupo.objects.disponibles_ver(miembro).pueden_reportar_discipulado().prefetch_related('lideres', 'historiales')
        self.fields['grupo'].queryset = grupos_query

        query = Miembro.objects.none()
        if self.is_bound:
            grupo = self.data.get('grupo', None)
            if grupo:
                query = Grupo.objects.get(id=grupo).discipulos
        
        self.fields['asistencia'].queryset = query

    def save(self):
        asistentes = self.cleaned_data.pop('asistencia')
        try:
            return ReunionDiscipulado.objects.reportar_reunion(asistentes=asistentes, **self.cleaned_data)
        except ReunionDiscipulado.MultipleObjectsReturned:
            logger.exception("Multiples reuniones de discipulado encontradas.")
            error_code = 'multiples_reuniones'
            self.add_error(None, forms.ValidationError(self.ERROR_MESSAGES[error_code], code=error_code))
            return None, False

