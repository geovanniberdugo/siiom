from common.decorators import permisos_requeridos
from django.core.exceptions import PermissionDenied

from functools import wraps


def miembro_property_test_decorator(view_func, property, *permissions, function=lambda x: x):
    """
    Decorador para usuarios miembros, la cual verifica un property de el modelo del miembro,
    y evalua una funcion como prueba, de no cumplir la prueba, verifica los permisos enviados,
    al no cumplir ninguna condición levanta una excepcion.

    :returns:
        view_func, la funcion o vista a la cual se está asignando el decorador.

    :param view_func:
        Funcion decorada

    :param property:
        La propiedad de el objeto de miembro que será evaluada, lo recomendable es usar una propiedad
        que retorne ``True`` o ``False`` para ser evaluada como ``bool``.

    :param \*permissions:
        Los permisos que serán evaluados para los miembros, se pueden pasar como strings independientes,
        ya que serán tomados en \*args, y enviados al decorador `permisos_requeridos`.

    :param function:
        Una función la cual es evaluada al momento de verificar la propiedad de el miembro,
        con el fin de hacer una prueba mas completa y exacta.
    """

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if hasattr(request, 'miembro'):
            if function(getattr(request.miembro, property)):
                return view_func(request, *args, **kwargs)
            else:
                if permissions:
                    return \
                        permisos_requeridos(*permissions)(view_func)(request, *args, **kwargs)
                return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied('No se encontró el miembro')

    return wrapped_view


def user_is_director_red(view_func):
    """
    Decorador para usuarios que son directores de red o administradores, en caso no pertenecer a
    ningún grupo, levanta una exception de PermissionDenied con código http 403.

    :returns: view_func, la funcion de vista a la que fue asignado el decorador.
    """

    return miembro_property_test_decorator(view_func, 'es_director_red', 'miembros.es_administrador')


def user_is_cabeza_red(view_func):
    """
    Decorador para usuarios que son cabeza de red o administradores, en caso de no pertenecer a ningún
    area, levanta una excepcion de PermissionDenied con código http 403.

    :returns: view_func, la funcion de vista a la que fue asignado el decorador.
    """

    return miembro_property_test_decorator(view_func, 'es_cabeza_red', 'miembros.es_administrador')

def user_tiene_subred_administrador(view_func):
    """
    Decorador para usuarios que tienen subred o administradores, en caso de no pertenecer a ningún
    area, levanta una excepcion de PermissionDenied con código http 403.

    :returns: view_func, la funcion de vista a la que fue asignado el decorador.
    """

    return miembro_property_test_decorator(view_func, 'tiene_subred', 'miembros.es_administrador')


def user_is_miembro_or_empleado(view_func):
    """
    Decorador para ver si el usuario que entra, tiene permisos de miembro o permisos de empleado

    :returns: view_func, la funcion de a vista que le fue asiganada el decorador
    """

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'empleado'):
            return view_func(request, *args, **kwargs)
        else:
            permissions = (
                'miembros.es_administrador', 'miembros.es_lider', 'miembros.es_agente',
                'grupos.puede_confirmar_ofrenda_discipulado', 'puede_confirmar_ofrenda_GAR'
            )
            for permission in permissions:
                if request.user.has_perm(permission):
                    return view_func(request, *args, **kwargs)

        raise PermissionDenied('No se encontro el miembro o empleado.')

    return wrapped_view
