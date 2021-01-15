import random
import string
import warnings

from django.contrib import messages
from django.core import mail

__doc__ = '''
    Funciones utiles para el uso de la aplicación general
'''


__author__ = 'German Alzate'


def convertir_a_queryset(modelo, lista, param_key='pk'):
    """
    :returns:
        Un Queryset de acuerdo a un modelo y a una lista de datos.

    :param modelo:
        El modelo a partir de el cual se retornaran los registros.

    :param lista:
        La lista de registros que seran los parametros para transformar a queryset.

    :param_key:
        El parametro de busqueda para hacer la consulta en la base de datos por medio del metodo filter.
    """

    if not param_key.endswith('__in'):
        param_key += '__in'

    options = {param_key: lista}
    return getattr(modelo, '_objects', modelo.objects).filter(**options)


def eliminar_registros(modelo, lista):
    """
    Permite eliminar los registros de un modelo, a partir de un queryset.

    :param modelo:
        El modelo a partir de el cual se eliminarán los registros.

    :param list lista:
        La lista de ids con la cual se harán las consultas a la base de datos.
    """

    modelo.objects.filter(id__in=lista).delete()


def eliminar(request, modelo, lista):  # deprecated
    """
    .. danger::
        Funcion Obsoleta, use mejor common.utils.eliminar_registros

    Funcion para mantener la compatibilidad con las actuales vistas que usan
    la funcion de eliminar, esta funcion, elimina los registros de un modelo dado.

    :returns:
        ``int`` Un entero, dando ``0`` como que la lista estuvo vacia, ``1`` como que
        borró todos los registros encontrados en la lista y ``2`` como que ocurrió
        un error al momento de borrar.

    :param request:
        La peticion de la vista.

    :param modelo:
        El modelo a partir de el cual se eliminarán los registros.

    :param list lista:
        La lista de ids con la cual se harán las consultas a la base de datos.
    """

    warnings.warn(
        'Funcion `common.utils.eliminar` está obsoleta, mejor use `common.utils.eliminar_registros`'
    )
    code = 0
    if lista:
        code = 1
        try:
            eliminar_registros(modelo, lista)
        except ValueError:  # cuando entra con all
            pass
        except:
            code = 2
    if code == 1:
        messages.success(request, "Se ha eliminado correctamente")
    return code


def generar_random_string(length=12):
    """
    Puede ser reemplazado por ``django.utils.crypto.get_random_string``

    :returns:
        Un string con letras aleatoreas.

    :param length:
        El tamano del string que será devuelto
    """

    pswd = ''

    for letter in range(length):
        pswd += random.choice(string.ascii_letters + string.digits)
    return pswd


def send_mail(subject, message, recipient_list, **kwargs):
    """Wrapper de send_mail con la dirección de envvio ya configurada."""

    from django.conf import settings
    return mail.send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, **kwargs)
