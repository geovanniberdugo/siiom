# Django Package
from django.db import models

# Python Package
import datetime


class SolicitudRegistroManager(models.Manager):
    """
    Manager para la clase de Solicitud de Registro
    """

    def ultimos_dos_meses(self):
        """
        Devuelve las solicitudes de los dos ultimos meses
        """
        hoy = datetime.date.today() + datetime.timedelta(days=1)
        hace_dos_meses = hoy - datetime.timedelta(weeks=8)
        # [self.PENDIENTE, self.ENTREGADO_DIGITADOR, self.DEVUELTO_CONSULTA]
        return self.exclude(
            estado=self.model.DEVUELTO_CONSULTA, fecha_devolucion__lte=hace_dos_meses
        ).order_by('-fecha_solicitud')
