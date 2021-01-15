from django.db import models
from django.utils.translation import ugettext_lazy as _lazy


__all__ = ('Visita', )


class Visita(models.Model):
    """
    Modelo para las visitas que ingresan en el sistema
    """

    MASCULINO = 'M'
    FEMENINO = 'F'
    OPCIONES_GENERO = (
        (MASCULINO, _lazy('MASCULINO')),
        (FEMENINO, _lazy('FEMENINO')),
    )

    VIUDO = 'V'
    CASADO = 'C'
    SOLTERO = 'S'
    DIVORCIADO = 'D'
    ESTADOS_CIVILES = (
        (VIUDO, _lazy('Viudo')),
        (CASADO, _lazy('Casado')),
        (SOLTERO, _lazy('Soltero')),
        (DIVORCIADO, _lazy('Divorciado')),
    )

    primer_nombre = models.CharField(verbose_name=_lazy('primer nombre'), max_length=255)
    segundo_nombre = models.CharField(verbose_name=_lazy('segundo nombre'), max_length=255, blank=True)
    primer_apellido = models.CharField(verbose_name=_lazy('primer apellido'), max_length=255)
    segundo_apellido = models.CharField(verbose_name=_lazy('segundo apellido'), max_length=255, blank=True)
    direccion = models.CharField(verbose_name=_lazy('dirección'), max_length=255, blank=True)
    telefono = models.BigIntegerField(verbose_name=_lazy('teléfono'))
    email = models.EmailField(verbose_name=_lazy('email'), blank=True)
    grupo = models.ForeignKey('grupos.Grupo', related_name='visitas', verbose_name=_lazy('grupo'), blank=True, null=True, on_delete=models.SET_NULL)
    fecha_ingreso = models.DateField(verbose_name=_lazy('fecha ingreso'), auto_now_add=True)
    genero = models.CharField(verbose_name=_lazy('género'), max_length=1, choices=OPCIONES_GENERO)
    retirado = models.BooleanField(verbose_name=_lazy('retirado'), default=False)
    edad = models.CharField(verbose_name=_lazy('edad'), max_length=50, blank=True)
    estado_civil = models.CharField(
        _lazy('estado civil'), max_length=1, choices=ESTADOS_CIVILES, blank=True
    )


    def __str__(self):
        return self.get_nombre()

    def get_nombre(self):
        nombre = '%(primer_nombre)s %(segundo_nombre)s %(primer_apellido)s %(segundo_apellido)s' % {
            'primer_nombre': self.primer_nombre,
            'segundo_nombre': self.segundo_nombre or '.',
            'primer_apellido': self.primer_apellido,
            'segundo_apellido': self.segundo_apellido or '.'
        }
        return nombre.replace('.', '')

    def migrar_visita_miembro(self):
        """
        Funcion que migra a la visita a un miembro
        """
        if self.grupo is not None:
            from miembros.models import Miembro
            miembro = Miembro()
            miembro.nombre = self.primer_nombre + ' ' + self.segundo_nombre
            miembro.primer_apellido = self.primer_apellido
            miembro.grupo = self.grupo
            miembro.fecha_registro = self.fecha_ingreso
            miembro.telefono = self.telefono
            if self.segundo_apellido != '':
                miembro.segundo_apellido = self.segundo_apellido
            if self.direccion != '':
                miembro.direccion = self.direccion
            if self.email != '':
                miembro.email = self.email
            miembro.save()
            return miembro
        else:
            raise ValueError('No se puede migrar Visita a Miembro si aun no pertenece a grupo')
