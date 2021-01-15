from django.db import models
from django.utils.translation import ugettext_lazy as _lazy
from tenant_schemas.models import TenantMixin


class Iglesia(TenantMixin):
    """
    Modelo para guardar la información de las iglesias gestionadas por la aplicación.
    """

    nombre = models.CharField(_lazy('nombre'), max_length=200)
    creada_el = models.DateTimeField(_lazy('creada el'), auto_now_add=True)
    logo = models.ImageField(_lazy('logo'), null=True, blank=True)

    # Terminos especificos de una iglesia.
    termino_gar = models.CharField(_lazy('termino GAR'), max_length=100, default='GAR')
    termino_visitas = models.CharField(_lazy('termino visitas'), max_length=100, default='visitas')

    class Meta:
        verbose_name = _lazy('iglesia')
        verbose_name_plural = _lazy('iglesias')

    def __str__(self):
        return self.nombre
