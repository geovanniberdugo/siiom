from django.core import checks
from django.conf import settings

__author__ = 'German Alzate'


MIDDLEWARE_DOTTED_STRING = 'miembros.middleware.MiembroMiddleWare'


@checks.register()
def miembro_middleware_check(app_configs, **kwargs):
    """
    Checks para los miembros, verifica que el middleware del miembro esté
    en los middlewares de settings.
    """

    errors = []
    # support for Django 2.0
    MIDDLEWARE_CLASSES = settings.MIDDLEWARE + getattr(settings, 'MIDDLEWARE_CLASSES', [])

    if MIDDLEWARE_DOTTED_STRING not in MIDDLEWARE_CLASSES:
        errors.append(
            checks.Error(
                'No se encontró el middleware de miembros.',
                hint=('Asegurate de que el middleware "%s" se encuentre en settings.MIDDLEWARE_CLASSES' %
                      MIDDLEWARE_DOTTED_STRING),
                id='miembros.E001'
            )
        )
    return errors
