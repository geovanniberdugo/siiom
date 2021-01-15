from django.db import models
# from .models import Departamento


class AreaManager(models.Manager):
    """
    Manager para la clase de Area
    """

    def departamentos(self):
        """
        Retorna los departamentos de un área
        """
        Departamento = self.model._meta.get_field('departamento').related_model
        return Departamento.objects.filter(id__in=self.all().values_list('departamento', flat=True))
