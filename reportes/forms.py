# -*- coding: utf-8 -*-
import copy
import datetime
# Django Package
from django import forms
from django.db.models import Sum, Count
from django.utils.translation import ugettext_lazy as _

# Locale Apps
from miembros.models import Miembro
from grupos.utils import reunion_reportada
from grupos.models import Predica, Grupo, ReunionDiscipulado, AsistenciaDiscipulado, ReunionGAR
from common.forms import (FormularioRangoFechas as RangoFechasFormMixin, CustomForm)
from .utils import fechas_reporte_generador

__author__ = 'Tania'


class FormularioRangoFechas(forms.Form):  # deprecado
    """
    Formulario rango de fechas anterior, se recomienda usar ``common.forms.FormularioRangoFechas``.
    """

    required_css_class = 'requerido'

    fechai = forms.DateField(label='Fecha inicial', widget=forms.DateInput(attrs={'size': 10}))
    fechaf = forms.DateField(label='Fecha final', widget=forms.DateInput(attrs={'size': 10}))

    def __init__(self, *args, **kwargs):
        super(FormularioRangoFechas, self).__init__(*args, **kwargs)
        self.fields['fechai'].widget.attrs.update({'class': 'form-control', 'data-mask': '00/00/00'})
        self.fields['fechaf'].widget.attrs.update({'class': 'form-control', 'data-mask': '00/00/00'})


class FormularioPredicas(forms.Form):
    """Formulario para ahcer reportes a partir de las predicas."""

    required_css_class = 'requerido'

    predica = forms.ModelChoiceField(queryset=Predica.objects.none(), empty_label=None)

    def __init__(self, miembro, *args, **kwargs):
        super(FormularioPredicas, self).__init__(*args, **kwargs)
        self.fields['predica'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})

        if miembro.usuario.has_perm("miembros.es_administrador"):
            self.fields['predica'].queryset = Predica.objects.all()
        else:
            self.fields['predica'].queryset = Predica.objects.filter(miembro__id__in=miembro.pastores())


class FormularioReportesSinConfirmar(RangoFechasFormMixin):
    """
    Formulario para ver los reportes que no se han confirmado de un grupo, de acuerdo a un rango de fechas.
    """
    grupo = forms.ModelChoiceField(
        queryset=Grupo.objects.prefetch_related('lideres').all().distinct(),
        label=_('grupo')
    )
    descendientes = forms.BooleanField(label=_('Descendientes'), required=False)

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset', None)
        super().__init__(*args, **kwargs)
        self.fields['grupo'].widget.attrs.update({
            'class': 'selectpicker',
            'data-live-search': 'true'
        })
        if queryset is not None:
            self.fields['grupo'].queryset = queryset

# ---------

class PredicaFormMixin(CustomForm):
    """"Mixin que agrega campo predica a un formulario."""

    predica = forms.ModelChoiceField(queryset=Predica.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['predica'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})        
        self.fields['predica'].queryset = Predica.objects.disponibles(self._miembro)
    
    @property
    def _miembro(self):
        raise NotImplementedError

class GrupoFormMixin(CustomForm):
    """Mixin que agrega campo grupo a un formulario. El campo solo muestra grupos según los permisos miembro logueado."""

    grupo = forms.ModelChoiceField(queryset=Grupo.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grupo'].queryset = Grupo.objects.disponibles_ver(self._miembro).prefetch_related('lideres')
    
    @property
    def _miembro(self):
        raise NotImplementedError

class EstadisticoDiscipuladoForm(PredicaFormMixin, GrupoFormMixin, CustomForm):
    """Formulario para el reporte de estadístico de reuniones discipulado."""

    def __init__(self, miembro, *args, **kwargs):
        self.miembro = miembro
        super().__init__(*args, **kwargs)
        self.fields['predica'].empty_label = None
        self.fields['grupo'].empty_label = None
    
    @property
    def _miembro(self):
        return self.miembro
    
    def _get_form_data(self):
        return self.cleaned_data['grupo'], self.cleaned_data['predica']
    
    def _calcula_porcentaje(self, lideres_asistentes, total_lideres):
        if total_lideres == 0:
            return 0

        return round(lideres_asistentes/total_lideres*100)

    def get_faltantes_reunion_discipulado(self):
        """Devuelve los faltantes por reportar la reunion de discipulado."""

        grupo, predica = self._get_form_data()
        
        return grupo.grupos_red.faltantes_reportar_discipulado(predica).prefetch_related(
            'lideres', 'parent', 'parent__lideres'
        )
    
    def get_data_estadistico_discipulos_recibido_predica(self):
        """
        Devuelve un queryset de grupos con los datos para el estadistico de discipulos que recibieron la predica ingresada. 
        """

        total_lideres = total_lideres_predica = 0
        grupo, predica = self._get_form_data()

        hijos = grupo.get_children().pueden_reportar_discipulado()
        for hijo in hijos:
            lideres_red = Miembro.objects.lideres_subred(hijo)
            subred = hijo.grupos_red

            hijo.total_lideres_subred = lideres_red.count()
            hijo.numero_lideres_asistentes_predica = lideres_red.filter(
                discipulados__asistencia=True, discipulados__reunion__predica=predica
            ).distinct().count()

            hijo.porcentaje = self._calcula_porcentaje(hijo.numero_lideres_asistentes_predica, hijo.total_lideres_subred)
        
            hijo.numero_grupos_no_reportaron = subred.faltantes_reportar_discipulado(predica).count()
            hijo.numero_grupos_reportaron = subred.pueden_reportar_discipulado().count() - hijo.numero_grupos_no_reportaron

            total_lideres = total_lideres + hijo.total_lideres_subred
            total_lideres_predica = total_lideres_predica + hijo.numero_lideres_asistentes_predica
        
        total_porcentaje = self._calcula_porcentaje(total_lideres_predica, total_lideres)
        return hijos, total_lideres, total_lideres_predica, total_porcentaje


class ReporteAsistenciaDiscipuladoExcelForm(PredicaFormMixin, GrupoFormMixin, CustomForm):

    descendientes = forms.BooleanField(label=_('Descendientes'), required=False)
    
    def __init__(self, miembro, *args, **kwargs):
        self.miembro = miembro
        super().__init__(*args, **kwargs)
        self.fields['predica'].empty_label = None
        self.fields['grupo'].empty_label = None
    
    @property
    def _miembro(self):
        return self.miembro
    
    def _get_form_data(self):
        return self.cleaned_data['grupo'], self.cleaned_data['predica']

    def _formatAsistio(self, asistio):
        return 'SI' if asistio else 'NO'
    
    def _formatUpper(self, cad):
        return cad.upper() if cad else ''

    def data_reporte(self):
        grupo, predica = self._get_form_data()
        
        lideres = Miembro.objects.lideres_subred(grupo).add_recibio_discipulado(predica).select_related('grupo_lidera__parent')
        
        data = [[
            self._formatUpper(lider.nombre), self._formatUpper(lider.primer_apellido), 
            self._formatUpper(lider.segundo_apellido), lider.cedula, lider.email,
            str(lider.grupo_lidera.get_parent()), str(lider.padre_subred(grupo)),
            self._formatAsistio(lider.recibio_discipulado)
        ] for lider in lideres]

        data.insert(0, [
            'Nombre', 'Primer Apellido', 'Segundo Apellido', 'Cedula', 'Email', 'Discipulo de', 'Subred', 'Asistio'
        ])
        
        return data
    
    def get_nombre_archivo(self):
        grupo, predica = self._get_form_data()
        return '{} - {}'.format(grupo, predica)


class EstadisticoReunionesGARForm(GrupoFormMixin, RangoFechasFormMixin, CustomForm):

    ofrenda = forms.BooleanField(label=_('Ofrenda'), required=False)
    descendientes = forms.BooleanField(label=_('Descendientes'), required=False)

    def __init__(self, miembro, *args, **kwargs):
        self.miembro = miembro
        super().__init__(*args, **kwargs)
        self.fields['grupo'].empty_label = None
    
    @property
    def _miembro(self):
        return self.miembro
    
    # TODO probar metodo
    def datos_reporte(self):
        data = {}
        # se sacan los datos iniciales
        grupo = self.cleaned_data['grupo']
        _fecha_final = self.cleaned_data['fecha_final']
        ofrenda = self.cleaned_data.get('ofrenda', False)
        _fecha_inicial = self.cleaned_data['fecha_inicial']
        descendientes = self.cleaned_data.get('descendientes', False)
        
        fecha_inicial = copy.deepcopy(_fecha_inicial)
        fecha_final = copy.deepcopy(_fecha_final)

        # constants
        format_date = "%d/%m/%y"
        date_split = ' - '
    
        # helpers
        _helper = []
        labels_fecha = []
        values_porcentaje_utilidad = [labels_fecha, []]
        values_asistencias = [['Fechas']]
        morosos = []
        _morosos = {}
        data_table = []
        ofrendas = []

        # se empacan los datos a la vista
        data['values_porcentaje_utilidad'] = values_porcentaje_utilidad
        data['values_asistencias'] = values_asistencias

        # si hay descendientes en el formulario
        if descendientes:
            grupos = grupo._grupos_red.prefetch_related('lideres').only('fechaApertura', 'id')
        else:
            grupos = Grupo._objects.filter(id=grupo.id)

        total_grupos_inactivos = grupos.inactivos().count()

        for fecha_inicial, fecha_final in fechas_reporte_generador(_fecha_inicial, _fecha_final):
            # esto, trae los que estuvieron activos antes de la fecha filtrada
            _grupos_semana = grupos.annotate_estado(fecha=fecha_final).activos().distinct()
            grupos_semana = _grupos_semana.count()

            # se sacan las reuniones que han ocurrido en la semana actual de el ciclo
            _reuniones = ReunionGAR.objects.filter(
                fecha__range=(fecha_inicial, fecha_final),
                grupo__in=_grupos_semana  # solo busca los reportes de los grupos de la semana
            ).defer(
                'confirmacionEntregaOfrenda', 'novedades', 'predica'
            ).distinct()

            # se hacen las agregaciones, con los datos de los estadisticos por semana
            reuniones = _reuniones.aggregate(
                lideres_asistentes=Sum('numeroLideresAsistentes'),
                visitas_=Sum('numeroVisitas'),
                total_asistentes=Sum('numeroTotalAsistentes'),
                grupos_reportaron=Count('grupo', distinct=True)
            )

            # Si las agregaciones estan vacias, se pasan a 0 para evitar errores en las operaciones
            for key in reuniones:
                if reuniones[key] is None:
                    reuniones[key] = 0

            # se agrega una nueva llave a las reuniones, con los asistentes regulares esa semana
            reuniones['asistentes_regulares'] = (
                reuniones['total_asistentes'] - reuniones['visitas_'] -
                reuniones['lideres_asistentes']
            )

            # se añaden las fechas
            fechas_str = fecha_inicial.strftime(format_date) + date_split + fecha_final.strftime(format_date)
            labels_fecha.insert(len(labels_fecha), fechas_str)  # se agrega como pila

            # si hay ofrendas
            if ofrenda:
                # se crea por aparte el agregate de ofrendas
                ofrenda_aggregate = _reuniones.aggregate(
                    ofrendas=Sum('ofrenda')
                )
                # se agrega de la forma [['fecha', ofrenda]]
                if ofrenda_aggregate['ofrendas'] is None:
                    ofrenda_aggregate['ofrendas'] = 0
                ofrendas.append([fechas_str, float(ofrenda_aggregate['ofrendas']) or 0])

            # se sacan los grupos sin reportar, vendria de la resta de los grupos de la semana, menos los sobres
            _sin_reportar = _grupos_semana.exclude(
                id__in=_reuniones.values_list('grupo__id', flat=True)
            )
            # se saca el conteo de los grupos sin reportar
            sin_reportar = _sin_reportar.count()

            # se añaden los datos a el diccionario, para la tabla
            data_table.append(
                {
                    'reuniones': reuniones,
                    'grupos_semana': grupos_semana,
                    'sin_reportar': sin_reportar,
                    'fecha': fechas_str
                }
            )

            # se agregan a la lista de morosos
            if sin_reportar > 0:
                _morosos_list_id = _sin_reportar.values_list('id', flat=True)
                for x in _morosos_list_id:
                    if x.__str__() not in _morosos:
                        _morosos[x.__str__()] = [fechas_str]
                    else:
                        _morosos[x.__str__()].append(fechas_str)

            # porcentaje grupos que estan reportando
            grupos_reportaron = reuniones.pop('grupos_reportaron', 0)

            try:
                # se intenta sacar el porcentaje, si grupos semana es 0, entonces no hay porcentaje
                porcentaje_grupos_reportando = round(float(grupos_reportaron) / grupos_semana * 100, 2)
            except ZeroDivisionError:
                porcentaje_grupos_reportando = 0

            # empaquetado de datos para porcetaje de utilidad
            values_porcentaje_utilidad[1].insert(len(values_porcentaje_utilidad[1]), porcentaje_grupos_reportando)
            # porcentaje quedaria de la forma
            # [['fecha1', 'fecha2'], [80, 30]]
            # se empaca el porcentaje a data_table, no puede llegar la lista vacia
            data_table[len(data_table) - 1]['porcentaje'] = porcentaje_grupos_reportando

            # empaquetado de datos para asistencias
            _auxiliar = []
            # se intenta organizar los datos de la mejor forma
            for key, item in reuniones.items():
                # se reemplazan los '_' por espacios
                key_to_word = key.replace('_', ' ').title()
                if key_to_word not in values_asistencias[0]:
                    values_asistencias[0].insert(len(values_asistencias[0]), key_to_word)
                # se agregan los valores a la variable auxiliar
                # _auxiliar.append()
                _auxiliar.insert(len(_auxiliar), [item, item.__str__()])  # [[1,1],[2,2],[3,3],[4,4]]
            _helper.insert(len(_helper), _auxiliar)  # [[[1,1],[2,2],[3,3],[4,4]], [[1,1],[2,2],[3,3],[4,4]]]

        # Para las barras de google, los datos deben quedar organizados de la forma
        # arr = [['Fecha', 'CAMPO1', 'CAMPO2'], ['Fecha', value1, 'value1', value2, 'value2']]

        # Grafico porcentaje Grupos Reportados
        for x, label in enumerate(labels_fecha):  # labels fecha contiene el tamaño de objetos base (No. semanas)
            # se agrega el label como iniacial para los valores de asistencia
            _lista = [label]
            for y, value in enumerate(_helper[x]):
                # se agrega cada elemento de la lista en el orden correspondiente
                _lista.append(_helper[x][y][0])
                _lista.append(_helper[x][y][1])
            # se agrega a el array principal
            values_asistencias.append(_lista)

        morosos = list(Grupo._objects.filter(id__in=[x for x in _morosos]))

        for moroso in reversed(morosos):
            for fecha in _morosos[moroso.id.__str__()]:
                _fecha = fecha.split(date_split)[0]
                _fecha = datetime.datetime.strptime(_fecha, format_date)
                if reunion_reportada(_fecha, moroso):
                    _morosos[moroso.id.__str__()].pop(_morosos[moroso.id.__str__()].index(fecha))
            if len(_morosos[moroso.id.__str__()]):
                moroso.fechas = '; '.join(_morosos[moroso.id.__str__()])
                moroso.no_reportes = len(_morosos[moroso.id.__str__()])
            else:
                morosos.pop(morosos.index(moroso))

        data['sin_reportar'] = morosos
        data['tabla'] = data_table
        data['grafico'] = True
        data['values_ofrenda'] = ofrendas or None
        data['grupos_inactivos'] = total_grupos_inactivos

        return data
