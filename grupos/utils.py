# apps
from .models import Grupo
from common.utils import convertir_a_queryset

# Python package
import datetime


def convertir_lista_grupos_a_queryset(lista_grupos):
    """
    :returns:
        Un queryset de grupos.

    :param list[int] lista_grupos:
        Una lista de pks de los grupos los cuales quieren ser pasados a queryset.
    """

    return convertir_a_queryset(Grupo, [grupo.pk for grupo in lista_grupos])


def reunion_reportada(fecha, grupo, discipulado=False):
    """
    :returns:
        *True* si existe una reunion reportada en el rango de una semana.

    :rtype: bool

    :param fecha:
        Objeto del tipo ``datetime.date`` o ``datetime.datetime``, a partir del cual
        se crearán los rangos para buscar las reuniones.

    :param grupo:
        Grupo a partir del cual se buscarán las reuniones.

    :param bool discipulado:
        Especifica si la busqueda se realizará sobre reuniones de grupo o discipulado.
    """

    ini_semana = fecha - datetime.timedelta(days=fecha.isoweekday() - 1)
    fin_semana = fecha + datetime.timedelta(days=7 - fecha.isoweekday())

    if discipulado:  # discipulado
        reunion = grupo.reuniones_discipulado.filter(fecha__gte=ini_semana, fecha__lte=fin_semana)
    else:  # gar
        reunion = grupo.reuniones_gar.filter(fecha__gte=ini_semana, fecha__lte=fin_semana)

    return reunion.exists()


def obtener_fechas_semana(fecha):
    """
    :returns:
        Las fechas posibles en la semana de lunes a domingo, a partir de la fecha
        dada.
    """

    inicio_semana = fecha - datetime.timedelta(days=fecha.isoweekday() - 1)
    fin_semana = fecha + datetime.timedelta(days=7 - fecha.isoweekday())

    _fechas = []

    while inicio_semana <= fin_semana:
        _fechas.append(inicio_semana)
        inicio_semana += datetime.timedelta(days=1)

    return _fechas


def reunion_reportada_discipulado_predica(grupo, predica):
    """
    :returns:
        *True* si se encuentra que el grupo ya hizo un reporte de reunion discipulado
        con la predica dada.

    :rtype bool:

    :param grupo:
        El grupo del el cual se quiere hacer la consulta si se reportó la reunion,
        discipulado.

    :param predica:
        La predica sobre la cual se hará la consulta.
    """

    return grupo.reuniones_discipulado.filter(predica=predica).exists()
