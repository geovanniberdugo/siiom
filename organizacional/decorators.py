# decorators for views

# Django Package
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

# Functools
from functools import wraps


def _all(iterable, key=lambda x: x):
    if not hasattr(iterable, '__iter__'):
        raise TypeError('Iterable must be a list, tuple, or dict')

    for obj in iterable:
        if not key(obj):
            return False
    return True


def login_empleado(*args, **kwargs):
    """
    Decorador para logear empleados
    """
    if isinstance(args[0], str):
        attributes = kwargs.pop('attributes', None) or args

        def decorator(function_view):
            @wraps(function_view)
            @login_required  # redirecciona al inicio de sesion o inicio si no está logeado
            def _wrapped_view(request, *args, **kwargs):
                if hasattr(request.user, 'empleado'):
                    if attributes is not None:
                        if _all(attributes, key=lambda x: isinstance(x, str)):
                            if _all(attributes, key=lambda x: getattr(request.user.empleado, x, False)):
                                return function_view(request, *args, **kwargs)
                            else:
                                # no tiene permiso
                                # return redirec('sin_permiso')
                                pass
                        else:
                            raise TypeError(
                                'Attributes Type must be a "str" instance, not, %s' % attributes.__class__.__name__
                            )
                    else:
                        return function_view(request, *args, **kwargs)
                return redirect('sin_permiso')
            return _wrapped_view
        return decorator

    if callable(args[0]):  # se asume que es la funcion principal
        @wraps(args[0])
        @login_required
        def wrapped_view(request, **kwargs):  # solo se aceptan variables con llave
            if hasattr(request.user, 'empleado'):
                return args[0](request, **kwargs)
            return redirect('sin_permiso')
        return wrapped_view
    else:
        return redirect('sin_permiso')
