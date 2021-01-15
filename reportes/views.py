import json
import copy
import datetime

from urllib import parse
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail, send_mass_mail
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import render
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from excel_response import ExcelResponse

# Apps imports
# from .charts import PdfTemplate
from .utils import fechas_reporte_generador
from common.decorators import permisos_requeridos
from grupos.utils import reunion_reportada
from grupos.models import ReunionGAR, Grupo, ReunionDiscipulado, AsistenciaDiscipulado
from miembros.models import Miembro
from miembros.decorators import user_tiene_subred_administrador
from .forms import (
    FormularioRangoFechas, FormularioPredicas, EstadisticoReunionesGARForm,
    FormularioReportesSinConfirmar,
    EstadisticoDiscipuladoForm, ReporteAsistenciaDiscipuladoExcelForm
)

@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_lider')
def estadistico_reuniones_discipulado(request):
    """Muestra un estadistico de los reportes de reunion discipulado segun los grupos,
    las opciones y el rango de fecha escogidos."""

    miembro = Miembro.objects.get(usuario=request.user)
    if miembro.usuario.has_perm("miembros.es_administrador"):
        listaGrupo_i = Grupo.objects.prefetch_related('lideres').all()  # ._suspendidos()  #.filter(estado='A')
    else:
        listaGrupo_i = Grupo.get_tree(miembro.grupo_lidera)
    descendientes = False
    ofrenda = False
    lid_asis = False
    asis_reg = False  # discipulos

    if request.method == 'POST':
        if 'combo' in request.POST:
            grupo_i = Grupo.objects.get(id=request.POST['id'])
            grupos = Grupo.get_tree(grupo_i)
            data = [{'pk': grupo.id, 'nombre': str(grupo)} for grupo in grupos]
            return HttpResponse(json.dumps(data), content_type="application/json")
        else:
            form = FormularioPredicas(miembro=miembro, data=request.POST)
            if form.is_valid():
                predica = form.cleaned_data['predica']
                grupo_i = Grupo.objects.get(id=request.POST['menuGrupo_i'])
                opciones = {'predica': predica.nombre.capitalize(), 'gi': grupo_i.nombre.capitalize()}
                sw = True

                if 'descendientes' in request.POST and request.POST['descendientes'] == 'S':
                    descendientes = True
                    opciones['gf'] = 'Descendientes'
                    grupos = Grupo._get_tree(grupo_i)
                else:
                    grupo_f = Grupo.objects.get(id=request.POST['menuGrupo_f'])
                    opciones['gf'] = grupo_f.nombre.capitalize()
                    listaGrupo_f = grupo_i.grupos_red.prefetch_related('lideres')
                    grupos = Grupo.obtener_ruta(grupo_i, grupo_f)

                values = [['Predica']]
                sw_while = True

                if 'ofrenda' in request.POST and request.POST['ofrenda'] == 'S':
                    titulo = "'Ofrenda'"
                    ofrenda = True
                    if 'Ofrenda' not in values[0]:
                        values[0].append('Ofrenda')
                    sum_ofrenda = ReunionDiscipulado.objects.filter(predica=predica,
                                                                    grupo__in=grupos).aggregate(Sum('ofrenda'))
                    if sum_ofrenda['ofrenda__sum'] is None:
                        sum = 0
                    else:
                        sum = sum_ofrenda['ofrenda__sum']
                    values.append([str(predica), float(sum)])
                else:
                    l = [predica.nombre]
                    if 'lid_asis' in request.POST and request.POST['lid_asis'] == 'S':
                        titulo = "'Lideres Asistentes'"
                        lid_asis = True
                        if 'Lideres asistentes' not in values[0]:
                            values[0].append('Lideres asistentes')
                        numlid = ReunionDiscipulado.objects.filter(predica=predica,
                                                                   grupo__in=grupos).aggregate(
                                                                       Sum('numeroLideresAsistentes'))
                        if numlid['numeroLideresAsistentes__sum'] is None:
                            sumLid = 0
                        else:
                            sumLid = numlid['numeroLideresAsistentes__sum']
                        l.append(sumLid)
                    if 'asis_reg' in request.POST and request.POST['asis_reg'] == 'S':
                        titulo = "'Asistentes Regulares'"
                        asis_reg = True
                        if 'Asistentes regulares' not in values[0]:
                            values[0].append('Asistentes regulares')
                        # reg = ReunionDiscipulado.objects.filter(fecha__range = (fechai, sig), grupo__in = grupos)
                        reg = ReunionDiscipulado.objects.filter(predica=predica, grupo__in=grupos)
                        numAsis = AsistenciaDiscipulado.objects.filter(reunion__in=reg, asistencia=True).count()
                        l.append(numAsis)
                    values.append(l)
                if 'reportePDF' in request.POST:
                    from .charts import PdfTemplate
                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'attachment; filename=report.pdf'
                    PdfTemplate(response, 'Estadistico de reuniones Discipulado', opciones, values, 2)
                    return response
    else:
        form = FormularioPredicas(miembro=miembro)
        sw = False

    return render(request, 'reportes/estadistico_discipulado.html', locals())


@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_lider')
def estadistico_totalizado_reuniones_gar(request):
    """Muestra un estadistico de los reportes de reunion GAR totalizado
    por discipulo segun el grupo, las opciones y el rango de fecha escogidos."""

    miembro = Miembro.objects.get(usuario=request.user)
    if miembro.usuario.has_perm("miembros.es_administrador"):
        listaGrupo_i = Grupo.objects.prefetch_related('lideres').all()
    else:
        listaGrupo_i = miembro.grupo_lidera.grupos_red.prefetch_related('lideres')
    ofrenda = False
    lid_asis = False
    visitas = False
    asis_reg = False

    if request.method == 'POST':
        form = FormularioRangoFechas(request.POST)
        if form.is_valid():
            fechai = form.cleaned_data['fechai']
            fechaf = form.cleaned_data['fechaf']
            grupo_i = Grupo.objects.get(id=request.POST['menuGrupo_i'])
            grupoDis = grupo_i.get_children()
            lista_redes = [Grupo.get_tree(grupo) for grupo in grupoDis]
            opciones = {'fi': fechai, 'ff': fechaf, 'g': grupo_i.nombre.capitalize()}
            sw = True

            n = ['Dates']
            n.extend(["%s" % nom for nom in grupoDis.values_list('nombre', flat=True)])
            values = [n]
            sw_while = True
            while sw_while:
                sig = fechai + datetime.timedelta(days=6)
                l = [fechai.strftime("%d/%m/%y") + '-' + sig.strftime("%d/%m/%y")]

                for grupos in lista_redes:

                    if 'opcion' in request.POST and request.POST['opcion'] == 'O':
                        ofrenda = True
                        opciones['opt'] = 'Ofrendas'
                        titulo = "'Ofrendas'"
                        sum_ofrenda = ReunionGAR.objects.filter(fecha__range=(fechai, sig),
                                                                grupo__in=grupos).aggregate(Sum('ofrenda'))
                        if sum_ofrenda['ofrenda__sum'] is None:
                            suma = 0
                        else:
                            suma = sum_ofrenda['ofrenda__sum']
                        l.append(float(suma))
                    else:
                        if 'opcion' in request.POST and request.POST['opcion'] == 'L':
                            lid_asis = True
                            opciones['opt'] = 'Lideres Asistentes'
                            titulo = "'Lideres Asistentes'"
                            numlid = ReunionGAR.objects.filter(fecha__range=(fechai, sig),
                                                               grupo__in=grupos).aggregate(
                                                                   Sum('numeroLideresAsistentes'))
                            if numlid['numeroLideresAsistentes__sum'] is None:
                                sumLid = 0
                            else:
                                sumLid = numlid['numeroLideresAsistentes__sum']
                            l.append(sumLid)
                        else:
                            if 'opcion' in request.POST and request.POST['opcion'] == 'V':
                                visitas = True
                                opciones['opt'] = 'Visitas'
                                titulo = "'Visitas'"
                                numVis = ReunionGAR.objects.filter(fecha__range=(fechai, sig),
                                                                   grupo__in=grupos).aggregate(Sum('numeroVisitas'))
                                if numVis['numeroVisitas__sum'] is None:
                                    sumVis = 0
                                else:
                                    sumVis = numVis['numeroVisitas__sum']
                                l.append(sumVis)
                            else:
                                if 'opcion' in request.POST and request.POST['opcion'] == 'A':
                                    asis_reg = True
                                    opciones['opt'] = 'Asistentes Regulares'
                                    titulo = "'Asistentes Regulares'"
                                    reg = ReunionGAR.objects.filter(fecha__range=(fechai, sig), grupo__in=grupos)
                                    numAsis = 0
                                    l.append(numAsis)
                values.append(l)
                fechai = sig + datetime.timedelta(days=1)
                if sig >= fechaf:
                    sw_while = False

            if 'reportePDF' in request.POST:
                from .charts import PdfTemplate
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename=report.pdf'
                PdfTemplate(response, 'Estadistico de reuniones GAR totalizadas por discipulo', opciones, values, 2)
                return response
    else:
        form = FormularioRangoFechas()
        sw = False

    return render(request, 'reportes/estadistico_total_gar.html', locals())

@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_lider')
def confirmar_ofrenda_grupos_red(request):
    """Vista para confirmar la ofrenda de los grupos de acuerdo a un grupo inicial"""

    data = {}
    miembro = Miembro.objects.get(usuario=request.user)
    if miembro.usuario.has_perm('miembros.es_administrador'):
        queryset = Grupo.objects.prefetch_related('lideres').all().distinct()
    else:
        queryset = miembro.grupo_lidera.grupos_red.prefetch_related('lideres')

    if request.method == 'POST':
        if 'confirmar' in request.POST:
            data = {}
            try:
                reunion = ReunionGAR.objects.get(id=request.POST.get('confirmar'))
                reunion.confirmacionEntregaOfrenda = True
                reunion.save()
                data['response_code'] = 200
                data['message'] = 'Reporte confirmado exitosamente'
            except ReunionGAR.DoesNotExist:
                data['response_code'] = 400
                data['message'] = 'Lo sentimos pero no se ha podido confirmar el reporte'

            return HttpResponse(json.dumps(data), content_type='application/json')

        form = FormularioReportesSinConfirmar(data=request.POST, queryset=queryset)

        if form.is_valid():
            grupo = form.cleaned_data['grupo']
            fecha_inicial = form.cleaned_data['fecha_inicial']
            fecha_final = form.cleaned_data['fecha_final']
            descendientes = form.cleaned_data['descendientes']

            fecha_final += datetime.timedelta(days=1)

            if descendientes:
                grupos = grupo._grupos_red.prefetch_related('lideres').only('fechaApertura', 'id')
            else:
                grupos = Grupo._objects.filter(id=grupo.id)

            reuniones = ReunionGAR.objects.filter(
                grupo__id__in=grupos.values_list('id', flat=True),
                fecha__range=(fecha_inicial, fecha_final),
                confirmacionEntregaOfrenda=False
            ).order_by('-fecha')

            data['reuniones'] = reuniones
            if len(reuniones) == 0:
                data['vacio'] = True

    else:
        form = FormularioReportesSinConfirmar(queryset=queryset)

    data['form'] = form

    return render(request, 'reportes/confirmar_ofrenda_grupos_red.html', data)

# ------------------

@login_required
@user_tiene_subred_administrador
def estadistico_reunion_discipulado(request):
    """Permite ver un estadistico de las reuniones discipulados por predica y por subred."""

    is_post = False
    faltantes = data = []
    total_lideres = total_lideres_predica = total_porcentaje = 0
    if request.method == 'POST':
        form = EstadisticoDiscipuladoForm(request.miembro, data=request.POST)
        if form.is_valid():
            is_post = True
            faltantes = form.get_faltantes_reunion_discipulado()
            data, total_lideres, total_lideres_predica, total_porcentaje = form.get_data_estadistico_discipulos_recibido_predica()
    else:
        form = EstadisticoDiscipuladoForm(request.miembro)
    return render(request, 'reportes/estadistico_reunion_discipulado.html', {
        'form': form, 'faltantes': faltantes, 'data_estadistico': data, 'is_post': is_post,
        'total_lideres': total_lideres, 'total_lideres_predica': total_lideres_predica,
        'total_porcentaje': total_porcentaje
    })

@login_required
@user_tiene_subred_administrador
def reporte_asistencia_discipulado_excel(request):

    if request.method == 'POST':
        form = ReporteAsistenciaDiscipuladoExcelForm(request.miembro, data=request.POST)
        if form.is_valid():
            data = form.data_reporte()
            nombre = parse.quote(form.get_nombre_archivo())
            response = ExcelResponse(data, output_filename=nombre, content_type='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename="{}.xls"'.format(nombre)
            return response
    else:
        form = ReporteAsistenciaDiscipuladoExcelForm(request.miembro)

    return render(request, 'reportes/reporte_asistencia_discipulado_excel.html', {'form': form})

@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_lider')
def reporte_estadistico_reuniones_gar(request):
    """Muestra un estadistico de reuniones gar según el grupo y fechas escogidas."""

    context = {}
    if request.method == 'POST':
        form = EstadisticoReunionesGARForm(request.miembro, data=request.POST)

        if form.is_valid():
            context = form.datos_reporte()
    else:
        form = EstadisticoReunionesGARForm(request.miembro, initial={'descendientes': True})

    context['form'] = form
    return render(request, 'reportes/estadistico_reuniones_gar.html', context)