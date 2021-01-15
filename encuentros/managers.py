from django.db import models


class EncuentroManager(models.Manager):
    """
    Manager para los encuentros
    """

    def activos(self):
        return self.filter(estado=self.model.ACTIVO)

    def inactivos(self):
        return self.filter(estado=self.model.INACTIVO)
