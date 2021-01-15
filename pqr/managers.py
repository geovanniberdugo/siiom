# Django Package
from django.db import models
from django.utils import timezone

# Locale Apps
from .resources import get_festivos

# Python Package
import datetime


class CasoManager(models.Manager):
    """
    Manager para el modelo de casos
    """

    def validos(self, *args, **kwargs):
        """
        Retorna los casos validos
        """
        return self.filter(valido=True, cerrado=False, *args, **kwargs)

    def nuevos(self, *args, **kwargs):
        """
        Retorna los casos que apenas han ingresado al sistema y no tienen usuarios empleados a cargo
        """
        return self.validos(empleado_cargo=None, fecha_ingreso_habil__lte=timezone.now().date(), *args, **kwargs)

    def habiles(self):
        """
        Retorna los casos que han superado su fecha limite de acuerdo a los dias habiles establecidos
        """
        # Falta hacer un filtro por fines de semana
        annotate = self.annotate(
            fecha_vencimiento=models.ExpressionWrapper(
                models.F('fecha_ingreso_habil') + datetime.timedelta(days=self.model.DIAS_PARA_EXPIRAR),
                output_field=models.DateField()
            )
        ).filter(fecha_vencimiento__lt=timezone.now()).exclude(fecha_vencimiento__in=get_festivos(timezone.now().year))
        # return (self.nuevos() | annotate).distinct()
        return self.filter(valido=True).exclude(cerrado=True)
