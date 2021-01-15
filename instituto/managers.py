from django.db import models, transaction
from django.db.models.query import QuerySet


class CursoQuerySet(models.QuerySet):
    """
    Queryset personalizado para los cursos.
    """

    def activos(self):
        """
        :returns:
            Un queryset con los cursos con estado abierto.
        """
        return self.filter(estado=self.model.ABIERTO)

    def inactivos(self):
        """
        :returns:
            Un queryset co los cursos con estado cerrado.
        """
        return self.filter(estado=self.model.CERRADO)


class CursoManager(models.Manager.from_queryset(CursoQuerySet)):
    """
    Manager para los el modelo de Cursos.
    """
    pass
