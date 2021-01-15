import json
import logging
# Django imports
from django.core import serializers
from django.http import HttpResponse, Http404, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from common.utils import send_mail

# Locale imports
from common.decorators import login_required_api
from django.contrib.auth.decorators import permission_required
from common import constants
from .models import Grupo, ReunionDiscipulado
from .serializers import ReunionDiscipuladoSerializer

logger = logging.getLogger('siiom.{}'.format(__name__))

@login_required_api
def lideres_grupo(request, pk):
    """
    :returns:
        Un JSON con los lideres del grupo pasado en el pk.

    :param pk:
        El pk de el grupo a partir del cual se quieren sacar los lideres.
    """

    grupo = Grupo.objects.get(pk=pk)
    response = [{'pk': lider.pk, 'nombre': str(lider)} for lider in grupo.lideres.all()]
    return HttpResponse(json.dumps(response), content_type=constants.CONTENT_TYPE_API)


@login_required_api
def discipulos_miembros_grupo(request, pk):
    """
    :returns:
        Un JSON con los discipulos y miembros de un grupo.

    :param pk:
        El pk de el grupo a partir del cual se quieren obtener los miembros y discipulos.
    """

    grupo = get_object_or_404(Grupo, pk=pk)

    string = serializers.serialize(
        queryset=grupo.miembros.all().order_by('nombre'),
        format='json', fields=['nombre', 'primer_apellido']
    )

    serialized = json.loads(string)
    return HttpResponse(json.dumps(serialized), content_type=constants.CONTENT_TYPE_API)

@login_required_api
def discipulos_grupo(request, pk):
    """
    :returns:
        Un JSON con los discipulos del grupo ingresado.
    
    :param pk: Pk del grupo del cual se van a obtener los discipulos.
    """

    grupo = get_object_or_404(Grupo, pk=pk)
    response = [{'id': discipulo.id, 'nombre': str(discipulo)} for discipulo in grupo.discipulos]
    return HttpResponse(json.dumps(response), content_type=constants.CONTENT_TYPE_API)

@api_view(['GET'])
@login_required_api
def reunion_discipulado(request, grupo, predica):
    """
    :returns:
        Un JSON con la reunión de discipulado del grupo para la predica ingresada.
    
    :param int grupo: Pk del grupo.
    :param int predica: Pk de la predica.
    """
    try:
        reunion = get_object_or_404(ReunionDiscipulado, grupo=grupo, predica=predica)
        serializer = ReunionDiscipuladoSerializer(reunion)
        return Response(serializer.data)
    except ReunionDiscipulado.MultipleObjectsReturned:
        logger.exception("Mas de una reunion encontrada para el mismo grupo.")
        return Response({'detail': 'Multiples objetos encontrados.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required_api
@permission_required('miembros.es_administrador', raise_exception=True)
def mail_missing_gar_envelopes_to_report(request, pk):
    """
    :returns:
        Un JSON con la respuesta del envío del email.

    :param pk:
        El pk del grupo al cual se le va a enviar el email.
    """

    group = get_object_or_404(Grupo, pk=pk)
    email_list = [lider.email for lider in group.lideres.all()]
    message = \
        """
        ¡Hola Líder de Grupo!\n
        Esperamos que te encuentres muy bien en este día. Apreciamos la labor que como líder desempeñas semana a semana.\n
        Al parecer existen sobres de grupo pendientes por registrar en el Sistema y queremos darte la información correspondiente de cada semana, asi como la cantidad de sobres.\n
            Cantidad de Sobres pendientes por reportar:
                "%(quantity)s"\n
            Semanas a las cuales corresponde cada sobre:
                "%(dates)s"\n
        No olvides ingresar a la plataforma para registrar la informacion de tu reunión de grupo. Si tienes alguna inquietud no dudes en contactarnos.
        """
    subject = 'Sobres de Grupo pendientes por Reportar'
    response = {"status": "True"}
    try:
        data = {
            'quantity': request.GET['quantity'],
            'dates': request.GET['dates']
        }
        send_mail(subject, message % data, email_list, fail_silently=False)
    except:
        response = {"status": "False"}

    return JsonResponse(response)    