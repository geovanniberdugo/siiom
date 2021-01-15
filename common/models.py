from django.db import transaction
from django.utils.translation import ugettext_lazy as _


__all__ = ('UtilsModelMixin', 'DiasSemanaMixin', )


class UtilsModelMixin:
    """
    Mixin de utilidades para los modelos.
    """

    def update(self, **options):
        """
        Actualiza los datos de el modelo.

        :param *options:
            Las opciones en clave:valor que van a ser cambiadas de los atributos del modelo.
        """

        keys = []
        with transaction.atomic():
            for key, value in options.items():
                setattr(self, key, value)
                keys.append(key)
            self.save(update_fields=keys)


class DiasSemanaMixin:
    """
    Mixin para guardar los dias de la semana de una forma unica para todas las apps
    """

    LUNES = '0'
    MARTES = '1'
    MIERCOLES = '2'
    JUEVES = '3'
    VIERNES = '4'
    SABADO = '5'
    DOMINGO = '6'

    DIAS_SEMANA = (
        (LUNES, _('Lunes')),
        (MARTES, _('Martes')),
        (MIERCOLES, _('Miercoles')),
        (JUEVES, _('Jueves')),
        (VIERNES, _('Viernes')),
        (SABADO, _('Sabado')),
        (DOMINGO, _('Domingo')),
    )
