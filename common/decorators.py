import json
from functools import wraps
from threading import Thread
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import status
from django.views.decorators.http import require_http_methods
from . import constants


def permisos_requeridos(*permisos):
    """
    Decorador para vistas que chequea si el usuario tiene algún permiso habilitado. Si no tiene ningún permiso se
    levanta la excepción PermissionDenied.
    """

    def chequear_permisos(user):
        for permiso in permisos:
            if user.has_perm(permiso):
                return True

        raise PermissionDenied

    return user_passes_test(chequear_permisos)


def login_required_api(view_func):
    """Decorador para saber si un usuario está logeado o no en una API, retornando una respuesta JSON."""

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        return HttpResponse(
            json.dumps({
                constants.RESPONSE_CODE: status.HTTP_401_UNAUTHORIZED,
                'message': 'User not authenticated'
            }),
            status=status.HTTP_401_UNAUTHORIZED,
            content_type=constants.CONTENT_TYPE_API
        )
    return wrapped_view


def concurrente(function):
    """
    Funcion para manejar concurrencia.

    :returns:
        Un hilo con la ejecución de la funcion asignada.
    """

    @wraps(function)
    def decorator(*args, **kwargs):
        hilo = Thread(target=function, args=args, kwargs=kwargs)
        hilo.daemon = True
        hilo.start()
        return hilo
    return decorator


def POST(view_func):
    """
    Decorador para que solo pueda ser ingresada a la pagina con POST.
    """
    return require_http_methods(['POST'])(view_func)


def GET(view_func):
    """
    Decorador para que solo pueda ser ingresada a la pagina con GET.
    """
    return require_http_methods(['GET'])(view_func)


def cache_value(key, timeout=120, suffix=None):
    """
    Decorador que guarda el valor de una función en la cache, según la key ingresada.

    :param str key:
        El nombre con que se va a guardar el valor en la cache.

    :param int timeout:
        Tiempo en segundos el cual va a durar el valor en la cache. Para mayor información ver
        `timeout <https://docs.djangoproject.com/en/1.8/topics/cache/#basic-usage>`_.

    :param str suffix:
        Nombre de atributo del objeto a ser usado como sufijo en la llave ingresada. El objeto en el cual se va a
        buscar el atributo, es el primer parámetro de la función que se esta decorando.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            key_ = key
            if suffix is not None:
                suffix_value = getattr(args[0], suffix)
                key_ = '{}_{}'.format(key, suffix_value)

            result = cache.get(key_)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(key_, result, timeout=timeout)

            return result
        return wrapper

    return decorator
