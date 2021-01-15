from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q

from .forms import FormularioObtenerGrupoAPI, FormularioObtenerTesoreroCoordinadorAPI
from grupos.models import Grupo
from miembros.models import Miembro
from common.constants import RESPONSE_SUCCESS, RESPONSE_CODE, RESPONSE_ERROR, RESPONSE_DENIED, URL_SIN_PERMISOS as URL
from common.decorators import permisos_requeridos

import json


@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_tesorero')
def obtener_grupos(request):
    """Vista que devuelve una lista de grupos en JSON de acuerdo a un valor inicial enviado."""

    if request.method == 'POST':
        form = FormularioObtenerGrupoAPI(data=request.POST)

        if form.is_valid():
            red = form.cleaned_data.get('red')
            value = form.cleaned_data.get('value')

            querys = (
                Q(lideres__nombre__icontains=value) |
                Q(lideres__primer_apellido__icontains=value) |
                Q(lideres__cedula__icontains=value)
            )

            grupos = Grupo.objects.filter(
                querys, red=red
            ).prefetch_related('lideres').distinct()[:10]

            response = {
                'grupos': [{'id': str(x.id), 'nombre': str(x)} for x in grupos],
                RESPONSE_CODE: RESPONSE_SUCCESS
            }
        else:
            _errors = []
            for error in form.errors:
                _errors.append(error)
            response = {
                'error': ', '.join(_errors),
                RESPONSE_CODE: RESPONSE_ERROR
            }
    else:
        response = {
            RESPONSE_CODE: RESPONSE_DENIED
        }

    return HttpResponse(json.dumps(response), content_type='application/json')


def obtener_coordinadores_tesoreros(request):
    """Retorna un JSON con los posibles coordinadores y tesoreros para un encuentro"""

    respose = {}

    if request.method == 'POST':
        if 'grupos[]' in request.POST:
            POST = {'grupos': request.POST.getlist('grupos[]')}
            POST['value'] = request.POST.get('value')

            form = FormularioObtenerTesoreroCoordinadorAPI(data=POST)

            if form.is_valid():
                grupos = form.cleaned_data.get('grupos')
                value = form.cleaned_data.get('value')

                querys = (
                    Q(nombre__icontains=value) |
                    Q(primer_apellido__icontains=value) |
                    Q(cedula__icontains=value)
                )

                ids_lideres = []
                for grupo in grupos:
                    for _id in grupo.grupos_red.prefetch_related('lideres').values_list('lideres__id', flat=True):
                        if _id not in ids_lideres:
                            ids_lideres.append(_id)
                miembros = Miembro.objects.filter(
                    querys, id__in=ids_lideres
                ).select_related('grupo_lidera', 'grupo').distinct()[:10]

                response = {
                    'miembros': [{'id': str(x.id), 'nombre': str(x)} for x in miembros],
                    RESPONSE_CODE: RESPONSE_SUCCESS
                }
            else:
                _errors = []
                for error in form.errors:
                    _errors.append(error)
                response = {
                    'error': ', '.join(_errors),
                    RESPONSE_CODE: RESPONSE_ERROR
                }
    else:
        response = {
            RESPONSE_CODE: RESPONSE_DENIED
        }

    return HttpResponse(json.dumps(response), content_type='application/json')
