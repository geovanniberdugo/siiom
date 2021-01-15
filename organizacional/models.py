from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _lazy

from .managers import AreaManager


__all__ = ('Departamento', 'Area', 'Empleado', )


class Departamento(models.Model):
    """Modelo para guardar los departamentos de una iglesia."""

    nombre = models.CharField(_lazy('nombre'), max_length=100)

    class Meta:
        verbose_name = _lazy('departamento')
        verbose_name_plural = _lazy('departamentos')

    def __str__(self):
        return self.nombre.title()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.lower()
        super(Departamento, self).save(*args, **kwargs)


class Area(models.Model):
    """Modelo para guardar las áreas de una iglesia."""

    nombre = models.CharField(_lazy('nombre'), max_length=100)
    departamento = models.ForeignKey(Departamento, verbose_name=_lazy('departamento'), related_name='areas', on_delete=models.CASCADE)

    objects = AreaManager()

    class Meta:
        verbose_name = _lazy('área')
        verbose_name_plural = _lazy('áreas')

    def __str__(self):
        return self.nombre.title()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.lower()
        super(Area, self).save(*args, **kwargs)


class Empleado(models.Model):
    """Modelo que guarda las personas que trabajan actualmente para una iglesia."""

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_lazy('usuario'), on_delete=models.CASCADE)
    areas = models.ManyToManyField(Area, verbose_name=_lazy('áreas'), related_name='empleados')
    cedula = models.BigIntegerField(_lazy('cédula'), unique=True)
    primer_nombre = models.CharField(_lazy('primer nombre'), max_length=100)
    segundo_nombre = models.CharField(_lazy('segundo nombre'), max_length=100, blank=True)
    primer_apellido = models.CharField(_lazy('primer apellido'), max_length=100)
    segundo_apellido = models.CharField(_lazy('segundo apellido'), max_length=100, blank=True)
    jefe_departamento = models.BooleanField(_lazy('jefe de departamento'), default=False)
    cargo = models.CharField(_lazy('cargo'), max_length=150)

    class Meta:
        verbose_name = _lazy('empleado')
        verbose_name_plural = _lazy('empleados')
        permissions = (
            ('es_administrador_sgd', 'Es Administrador de Sistema Gestion Documental'),
            ('buscar_registros', 'Puede Buscar Registros'),
            ('es_compras', 'Es usuario de compras'),
            ('es_presidente', 'Es presidente'),
        )

    def __str__(self):
        return '{0} {1}'.format(self.primer_nombre.upper(), self.primer_apellido.upper())

    def get_solicitudes(self):
        """
        Retorna las solicitudes actuales
        """
        from gestion_documental.models import SolicitudRegistro as Solicitud
        return self.solicitudes.filter(estado__in=[Solicitud.PENDIENTE, Solicitud.ENTREGADO_DIGITADOR])

    @property
    def is_jefe_comercial(self):
        """
        Retorna Verdadero si el empleado es jefe de el departamento comercial
        """
        if self.jefe_departamento:
            if any(self.areas.filter(departamento__nombre__icontains='comerci')):
                return True
        return False

    @property
    def is_jefe_administrativo(self):
        """
        Retorna verdadero si es jefe administrativo
        """
        if self.jefe_departamento:
            if any(self.areas.filter(departamento__nombre__icontains='administra')):
                return True
        return False

    @property
    def is_jefe_financiero(self):
        """
        Retorna verdadero si el jefe es del departamento financiero
        """
        if self.jefe_departamento:
            if any(self.areas.filter(departamento__nombre__icontains='financi')):
                return True
        return False

    @property
    def is_compras(self):
        """
        Retorna verdadero si el empleado es de el area de compras
        """
        if any(self.areas.filter(nombre__icontains='compra')):
            return True
        return False

    @property
    def is_usuario_pago(self):
        """
        Retorna verdadero si el usuario es encargado de pagos
        """
        if any(
            self.areas.filter(nombre__icontains='contab') | self.areas.filter(nombre__icontains='tesore')
        ):
            return True
        return False

    @property
    def is_servicio_cliente(self):
        """
        Retorna True si el empleado es de el area de servicio al cliente
        """
        return self.areas.filter(nombre__icontains='servicio').exists()

    @property
    def pqr_participa(self):
        """
        Retorna True si tiene pqr activas, en donde participe
        """
        return (self.casos_implicado.filter(cerrado=False) | self.casos_cargo.filter(cerrado=False)).exists()
