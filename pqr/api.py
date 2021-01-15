# Python Package
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from organizacional.models import Empleado

from .models import Caso

import json


@csrf_exempt
def empleados_nombres_views(request, id_caso):
    """
    Retorna una lista con los nombres y la cedula de los empleados
    """

    caso = get_object_or_404(Caso, id=id_caso)

    data = [
        {'name': '{0} {1} ({2})'.format(empleado.primer_nombre, empleado.primer_apellido, empleado.cedula)}
        for empleado in Empleado.objects.exclude(id__in=caso.integrantes.all().values_list('id', flat=True))
    ]

    return HttpResponse(json.dumps(data), content_type='application/javascript')
