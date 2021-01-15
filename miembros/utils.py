__doc__ = '''
    Funciones utiles para los miembros.
'''

__author__ = 'German Alzate'


def divorciar_miembro(miembro, estado_civil=None):
    """
    Funcion para divorciar a un miembro de su conyugue.

    :param miembro:
        El miembro a partir de el cual se va a hacer la separacion.

    :param str estado_civil:
        El estado civil que se le pondra a cada miembro implicado.
    """

    conyugue = miembro.conyugue
    if estado_civil is None:
        estado_civil = miembro.DIVORCIADO

    if conyugue:
        conyugue.update(conyugue=None, estado_civil=estado_civil)

    miembro.update(conyugue=None, estado_civil=estado_civil)


def divorciar(miembro, conyugue, estado_civil):  # deprecated
    """
    .. danger::
        Funcion Obsoleta, use mejor miembros.utils.divorciar_miembro

    Funcion para divorciar miembros y sus conyugues.

    :param miembro:
        Miembro inicial para divorciar.

    :param conyugue:
        Conyugue del miembro a divorciar.

    :param str estado_civil:
        Estado civil que será puesto a cada miembro.
    """

    miembro.estado_civil = estado_civil
    miembro.conyugue = None
    miembro.save()
    conyugue.estado_civil = estado_civil
    conyugue.conyugue = None
    conyugue.save()


def calcular_grupos_miembro(miembro):
    """
    Funcion para obtener el número de grupos que tiene un miembro debajo.

    :returns:
        El numero de grupos que hay debajo de el miembro en un entero.

    :rtype int:

    :param miembro:
        El miembro a partir de el cual se quieren ver el numero de grupos.
    """

    celulas = 0
    if miembro.grupo_lidera:
        celulas = miembro.grupo_lidera.get_descendant_count() + 1
    return celulas
