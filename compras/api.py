# Django Package
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse

# Locale Apps
from .models import Requisicion, Adjunto, Parametros
from common import constants
from organizacional.models import Departamento

# Python Package
import json
import datetime


@login_required
@csrf_exempt
def detalles_requisicion_api(request, id_requisicion):
    """
    Devuelve en formato json los detalles de una requisicion
    """

    try:
        requisicion = Requisicion.objects.get(id=id_requisicion)

        data = []

        to_data_1 = [
            {
                'cantidad': detalle.cantidad or 1, 'descripcion': detalle.descripcion,
                'referencia': detalle.referencia or '', 'marca': detalle.marca or '',
                'valor_aprobado': detalle.valor_aprobado or 0, 'total_aprobado': detalle.total_aprobado or 0,
                'forma_pago': detalle.get_forma_pago_display(), 'class': 'success c-white' if detalle.cumplida else ''
            } for detalle in requisicion.detallerequisicion_set.all()
        ]

        data.insert(0, to_data_1)

        to_data_2 = [
            {
                'justificacion': requisicion.observaciones
            }
        ]

        data.insert(1, to_data_2)

        if requisicion.presupuesto_aprobado == Requisicion.ESPERA:
            to_data_3 = [
                {
                    'fecha_pago': 'INDEFINIDA',
                    'estado_pago': 'EN ESPERA DE PRESUPUESTO',
                    'class': 'warning'
                }
            ]

        else:
            to_data_3 = [
                {
                    'fecha_pago': requisicion.fecha_pago or '',
                    'estado_pago': requisicion.get_estado_pago_display() or '',
                    'class': 'info'
                }
            ]

            if requisicion.fecha_pago:
                to_data_3 = [
                    {
                        'fecha_pago': requisicion.fecha_pago.strftime('%d/%m/%Y') or '',
                        'estado_pago': requisicion.get_estado_pago_display() or '',
                        'class': 'info'
                    }
                ]

        data.insert(2, to_data_3)

        return HttpResponse(json.dumps(data), content_type=constants.CONTENT_TYPE_API)
    except Exception as e:
        return HttpResponse(e, content_type='text/plain')


@login_required
@csrf_exempt
def observaciones_requisicion(request, id_requisicion):
    """
    Devuelve la observacion ligada a la requisicion y el nombre del usuario
    """

    try:
        requisicion = Requisicion.objects.get(id=id_requisicion)
        clase = ''
        try:
            empleado = request.user.empleado
        except:
            raise Http404
        if requisicion.get_rastreo() == Requisicion.DATA_SET['compras']:
            dias = Parametros.objects.dias()
            ultimo = requisicion.historial_set.last()
            fecha_plazo = ultimo.fecha + datetime.timedelta(days=dias)
            if datetime.date.today() < fecha_plazo.date():
                clase = 'info'
            elif datetime.date.today() >= fecha_plazo.date() and empleado.is_compras:
                clase = 'danger'
            else:
                clase = 'warning'
        elif requisicion.get_rastreo() in [Requisicion.DATA_SET[x] for x in Requisicion._FAILED]:
            clase = 'danger'
        if requisicion.estado == Requisicion.TERMINADA:
            clase = 'success'
        data = []
        data1 = [
            {
                'progreso': float(str(requisicion.get_progreso())[:4]),
                'clase': 'progress-bar-' + clase if clase else ''
            }
        ]
        data2 = [
            {
                'observacion': historia.observacion,
                'usuario': historia.empleado.__str__(),
                'fecha': historia.fecha.strftime('%d/%m/%Y')
            } for historia in requisicion.historial_set.all() if historia.observacion
        ]
        data3 = [
            {
                'archivo': archivo.get_name(),
                'ruta': reverse('compras:descargar_archivos_api', args=(archivo.id,))
            } for archivo in requisicion.adjunto_set.all()
        ]
        data.insert(0, data1)
        data.insert(1, data2)
        if data3:
            data.insert(2, data3)
        return HttpResponse(json.dumps(data), content_type=constants.CONTENT_TYPE_API)
    except Exception as e:
        return HttpResponse(e, content_type='text/plain')


@login_required
@csrf_exempt
def requisicion_comentada_api(request, id_requisicion):
    """
    Retorna un valor para ser evaluado en javascript con true o false si esta comentada
    devuelve true si fue comentada por jefe de departamento
    """
    # if requisicion.historial_set.last().empleado.usuario.has_perm('organizacional.es_compras'):
    try:
        requisicion = Requisicion.objects.get(id=id_requisicion)
        _choices = [
            Requisicion.DATA_SET['compras'], Requisicion.DATA_SET['administrativo'],
            Requisicion.DATA_SET['financiero'], Requisicion.DATA_SET['pago'],
            Requisicion.DATA_SET['terminada'], Requisicion.DATA_SET['presidencia'],
            Requisicion.DATA_SET['espera_presupuesto'], Requisicion.DATA_SET['solicitante']
        ]
        if requisicion.get_rastreo() in _choices:
            return HttpResponse('true', content_type='text/plain')
        else:
            return HttpResponse('false', content_type='text/plain')
    except:
        return HttpResponse('', content_type='text/plain')


@login_required
@csrf_exempt
def requisicion_comentada_compras_api(request, id_requisicion):
    """
    Retorna un valor para ser evaluado en javascript con true o false si esta comentada
    devuelve true si fue comentada por usuario de compras
    """
    # if requisicion.historial_set.last().empleado.usuario.has_perm('organizacional.es_compras'):
    try:
        requisicion = Requisicion.objects.get(id=id_requisicion)
        _choices = [
            Requisicion.DATA_SET['administrativo'], Requisicion.DATA_SET['financiero'],
            Requisicion.DATA_SET['pago'], Requisicion.DATA_SET['terminada'],
            Requisicion.DATA_SET['presidencia'], Requisicion.DATA_SET['espera_presupuesto'],
            Requisicion.DATA_SET['solicitante']
        ]
        if requisicion.get_rastreo() in _choices:
            return HttpResponse('true', content_type='text/plain')
        else:
            return HttpResponse('false', content_type='text/plain')
    except:
        return HttpResponse('', content_type='text/plain')


@login_required
@csrf_exempt
def requisicion_comentada_jefe_administrativo_api(request, id_requisicion):
    """
    Retorna un valor para ser evaluado en javascript con true o false si esta comentada
    devuelve true si fue comentada por jefe administrativo
    """

    try:
        requisicion = Requisicion.objects.get(id=id_requisicion)
        _choices = [
            Requisicion.DATA_SET['financiero'], Requisicion.DATA_SET['pago'],
            Requisicion.DATA_SET['terminada'], Requisicion.DATA_SET['presidencia'],
            Requisicion.DATA_SET['espera_presupuesto'], Requisicion.DATA_SET['solicitante']
        ]
        if requisicion.get_rastreo() in _choices:
            return HttpResponse('true', content_type='text/plain')
        else:
            return HttpResponse('false', content_type='text/plain')
    except:
        return HttpResponse('', content_type='text/plain')


@login_required
@csrf_exempt
def requisicion_comentada_presidencia_api(request, id_requisicion):
    """
    Retorna un valor para ser evaluado en javascript con true o false si esta comentada
    devuelve true si fue comentada por jefe administrativo
    """

    try:
        requisicion = Requisicion.objects.get(id=id_requisicion)
        _choices = [
            Requisicion.DATA_SET['financiero'], Requisicion.DATA_SET['pago'],
            Requisicion.DATA_SET['terminada'], Requisicion.DATA_SET['espera_presupuesto'],
            Requisicion.DATA_SET['administrativo'], Requisicion.DATA_SET['solicitante']
        ]
        if requisicion.get_rastreo() in _choices:
            return HttpResponse('true', content_type='text/plain')
        else:
            return HttpResponse('false', content_type='text/plain')
    except:
        return HttpResponse('', content_type='text/plain')


@login_required
@csrf_exempt
def descargar_archivos_api(request, id_archivo):
    """
    Vista para devolver un archivo listo para descargar
    """
    try:
        adjunto = get_object_or_404(Adjunto, pk=id_archivo)

        try:
            ext = adjunto.get_name.split('.')
            if ext:
                ext = ext[len(ext) - 1]
            response = HttpResponse(adjunto.archivo, content_type=constants.CONTENT_TYPES[ext])
        except:
            response = HttpResponse(adjunto.archivo)
        response['Content-Disposition'] = "attachment; filename='%s'" % adjunto.get_name()
        return response
    except Exception as e:
        return HttpResponse(e, content_type='text/plain')


@login_required
@csrf_exempt
def get_areas_by_departamento_json(request, id_departamento):
    """
    Retorna un JSON con las areas pertenecientes a un departamento
    """

    try:
        departamento = Departamento.objects.get(id=id_departamento)
    except:
        data = []
        return HttpResponse(json.dumps(data), content_type=constants.CONTENT_TYPE_API)

    data = [
        {'area': area.nombre.upper(), 'id': area.id} for area in departamento.areas.all()
    ]

    return HttpResponse(json.dumps(data), content_type=constants.CONTENT_TYPE_API)
