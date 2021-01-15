from django.db import models
from django.utils.translation import ugettext_lazy as _lazy

from .managers import EncuentroManager

import datetime


__all__ = ('Encuentro', 'Encontrista', )


class Encuentro(models.Model):
    """
    Modelo para la creacion de encuentros
    """

    ACTIVO = 'A'
    INACTIVO = 'I'
    OPCIONES_ESTADO = (
        (ACTIVO, _lazy('ACTIVO')),
        (INACTIVO, _lazy('INACTIVO')),
    )

    fecha_inicial = models.DateTimeField(verbose_name=_lazy('Fecha Inicial'))
    fecha_final = models.DateField(verbose_name=_lazy('Fecha Final'))
    hotel = models.CharField(max_length=100, verbose_name=_lazy('Hotel'))
    grupos = models.ManyToManyField('grupos.Grupo', verbose_name=_lazy('Grupos'))
    coordinador = models.ForeignKey('miembros.Miembro',
                                    verbose_name=_lazy('Coordinador'), related_name='encuentros_coordinador', on_delete=models.CASCADE)
    tesorero = models.ForeignKey('miembros.Miembro', verbose_name=_lazy('Tesorero'), related_name='encuentros_tesorero', on_delete=models.CASCADE)
    direccion = models.CharField(max_length=100, verbose_name=_lazy('Direccion'), blank=True)
    observaciones = models.TextField(verbose_name=_lazy('Observaciones'), blank=True)
    dificultades = models.TextField(verbose_name=_lazy('Dificultades'), blank=True)
    estado = models.CharField(max_length=1, choices=OPCIONES_ESTADO, default=ACTIVO, verbose_name=_lazy('Estado'))

    objects = EncuentroManager()

    def __str__(self):
        return '{0} - {1}'.format(self.fecha_inicial, self.fecha_final)

    def save(self, *args, **kwargs):
        self.hotel = self.hotel.upper()
        super(Encuentro, self).save(*args, **kwargs)

    @property
    def en_curso(self):
        """
        :returns: ``True`` si el encuentro actual está en curso o no ha finalizado.

        :rtype: bool
        """
        if datetime.date.today() >= self.fecha_inicial.date() and datetime.date.today() <= self.fecha_final:
            return True
        return False

    @property
    def acabado(self):
        """
        :returns: ``True`` si el encuentro actual ha finalizado.

        :rtype: bool
        """
        return datetime.date.today() > self.fecha_final

    @property
    def tiene_asistencia(self):
        """
        :returns: ``True`` si el encuentro actual le fue marcada la asistencia de miembros.

        :rtype: bool
        """

        return self.encontrista_set.filter(asistio=True).exists()

    @property
    def no_empieza(self):
        """
        :returns: ``True`` si el encuentro actual no ha empezado aún.

        :rtype: bool
        """

        return datetime.date.today() < self.fecha_inicial.date()


class Encontrista(models.Model):
    """
    Modelo de creacion de encontristas
    """

    MASCULINO = 'M'
    FEMENINO = 'F'
    OPCIONES_GENERO = (
        (MASCULINO, _lazy('MASCULINO')),
        (FEMENINO, _lazy('FEMENINO')),
    )

    primer_nombre = models.CharField(max_length=60, verbose_name=_lazy('Primer Nombre'))
    segundo_nombre = models.CharField(max_length=60, blank=True, verbose_name=_lazy('Segundo Nombre'))
    primer_apellido = models.CharField(max_length=60, verbose_name=_lazy('Primer Apellido'))
    segundo_apellido = models.CharField(max_length=60, blank=True, verbose_name=_lazy('Segundo Apellido'))
    talla = models.CharField(max_length=3, verbose_name=_lazy('Talla'), blank=True)
    genero = models.CharField(max_length=1, choices=OPCIONES_GENERO, verbose_name=_lazy('Género'))
    identificacion = models.BigIntegerField(verbose_name=_lazy('Identificación'))
    email = models.EmailField(verbose_name=_lazy('Email'))
    grupo = models.ForeignKey('grupos.Grupo', related_name='encontristas', verbose_name=_lazy('Grupo'), on_delete=models.CASCADE)
    encuentro = models.ForeignKey(Encuentro, verbose_name=_lazy('Encuentro'), on_delete=models.CASCADE)
    asistio = models.BooleanField(default=False, verbose_name=_lazy('Asistio'))

    def __str__(self):
        return '{0} {1} ({2})'.format(self.primer_nombre, self.primer_apellido, self.identificacion)

    def save(self, *args, **kwargs):
        self.primer_nombre = self.primer_nombre.upper()
        self.primer_apellido = self.primer_apellido.upper()
        if self.segundo_nombre:
            self.segundo_nombre = self.segundo_nombre.upper()
        if self.segundo_apellido:
            self.segundo_apellido = self.segundo_apellido.upper()
        super(Encontrista, self).save(*args, **kwargs)
