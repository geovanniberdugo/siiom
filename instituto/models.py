from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import ArrayField

from common.models import DiasSemanaMixin
from . import managers


__author__ = 'German Alzate'

__all__ = (
    'Materia', 'Modulo', 'Sesion', 'Salon',
    'Curso', 'Estudiante', 'Matricula', 'Abono',
    'Seguimiento'
)


class Materia(models.Model):
    """
    Modelo para guardar las materias que serán dadas en un instituto.
    """

    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    # grupos que deberia tener el lider para cursar esta materia
    grupos_minimo = models.IntegerField(default=0, verbose_name=_('Grupos mínimo'))
    dependencia = models.ForeignKey('self', related_name='dependecias_set', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.nombre.upper()


class Modulo(models.Model):
    """Modelo que guarda los datos de los módulos realizados en cada materia."""

    prioridad = models.IntegerField(verbose_name=_('Prioridad'))
    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    materia = models.ForeignKey(Materia, verbose_name=_('Materia'), related_name='modulos', on_delete=models.CASCADE)

    class Meta:
        unique_together = (('materia', 'prioridad'), )

    def __str__(self):
        return '({self.materia}) {self.prioridad}. {self.nombre}'.format(self=self)


class Sesion(models.Model):
    """Modelo que guarda las sesiones pertenecientes a cada modulo."""

    prioridad = models.IntegerField(verbose_name=_('Prioridad'))
    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    modulo = models.ForeignKey(Modulo, verbose_name=_('Módulo'), related_name='sesiones', on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = _('Sesiones')
        unique_together = (('modulo', 'prioridad'), )

    def __str__(self):
        return '({self.modulo.nombre}) {self.prioridad}. {self.nombre}'.format(self=self)


class Salon(models.Model):
    """Modelo para guardar los salones registrados, en los cuales se pueden hacer clases."""

    nombre = models.CharField(max_length=100, verbose_name=_('Nombre'))
    capacidad = models.IntegerField(verbose_name=_('Capacidad'))

    class Meta:
        verbose_name_plural = _('Salones')

    def __str__(self):
        return 'Salón "{self.nombre}" ({self.capacidad} cupos)'.format(self=self)

    def cupo_disponible_curso(self, curso):
        """
        :param curso:
            El curso a partir de el cual se quiere consultar la disponibilidad de cupo

        :rtype int:

        :returns:
            El cupo disponible de un salón, a partir de un curso.
        """
        if self.cursos.abiertos().filter(id=curso.id).exists():
            return self.capacidad - curso.matriculas.count() or 0
        return None


class Curso(DiasSemanaMixin, models.Model):
    """Modelo para guardar los cursos que se realizan en cada salon."""

    ABIERTO = 'A'
    CERRADO = 'C'

    OPCIONES_ESTADO = (
        (ABIERTO, _('Abierto')),
        (CERRADO, _('Cerrado')),
    )

    precio = models.IntegerField(verbose_name=_('Precio'))
    hora_fin = models.TimeField(verbose_name=_('Hora Fin'))
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateField(verbose_name=_('Fecha Fin'))
    hora_inicio = models.TimeField(verbose_name=_('Hora Inicio'))
    fecha_inicio = models.DateField(verbose_name=_('Fecha Inicio'))
    color = models.CharField(max_length=100, verbose_name=_('Color'))
    salon = models.ForeignKey(Salon, related_name='cursos', verbose_name=_('Salón'), on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, related_name='cursos', verbose_name=_('Materia'), on_delete=models.CASCADE)
    estado = models.CharField(max_length=1, choices=OPCIONES_ESTADO, verbose_name=_('Estado'))
    dia = ArrayField(models.CharField(max_length=1, choices=DiasSemanaMixin.DIAS_SEMANA, verbose_name=_('Día')))
    profesor = models.ManyToManyField(
        'miembros.Miembro', verbose_name=_('Profesor'), related_name='cursos_como_profesor')

    objects = managers.CursoManager()

    class Meta:
        ordering = ('fecha_inicio', )

    def __str__(self):
        return '{self.materia} - Salon {self.salon.nombre}'.format(self=self)

    @property
    def cupo_disponible(self):
        """
        :rtype int:

        :returns:
            Retorna el cupo disponible de este curso
        """
        return self.salon.cupo_disponible_curso(self)


class Estudiante(models.Model):
    """Modelo para guardar los estudiantes que se crean para asistir a un curso de academia."""

    nombres = models.CharField(max_length=255, verbose_name=_('Nombres'))
    apellidos = models.CharField(max_length=255, verbose_name=_('Apellidos'))
    identificacion = models.CharField(max_length=100, verbose_name=_('Identificación'))
    grupo = models.ForeignKey(
        'grupos.Grupo', related_name='estudiantes', verbose_name=_('Grupo'),
        help_text=_('Grupo al que asiste el estudiante'), on_delete=models.CASCADE
    )
    miembro = models.OneToOneField(
        'miembros.Miembro', related_name='estudiante', verbose_name=_('Líder'), blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        if getattr(self, 'miembro', None):
            return self.miembro.__str__()
        return '{self.nombres} {self.apellidos} ({self.identificacion})'.format(self=self)

    def __getattr__(self, attr):
        if attr.startswith('nota_materia_'):
            pk = attr[len('nota_materia_'):]
            matriculas = self.matriculas.filter(curso__materia__id=pk)
            matricula = matriculas.order_by('-fecha').first()
            if matricula:
                if matricula.paso or matricula.asistencias.exists():
                    return 'X'
            return ''
        raise AttributeError('Estudiante has not attribute `{}`'.format(attr))


class Matricula(models.Model):
    """Modelo para registrar cada matricula de un estudiante en un curso."""

    fecha = models.DateField(verbose_name=_('Fecha'))
    paso = models.NullBooleanField(verbose_name=_('Pasó'))
    curso = models.ForeignKey(Curso, verbose_name=_('Curso'), related_name='matriculas', on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Estudiante, related_name='matriculas', verbose_name=_('Estudiante'), on_delete=models.CASCADE)

    @property
    def pagos(self):
        """
        :rtype int:

        :returns:
            La sumatoria de los pagos que han hecho a la matricula.
        """
        aggregate = self.abonos.aggregate(suma=models.Sum('valor'))
        return aggregate.get('suma', 0)

    @property
    def saldo(self):
        """
        :rtype int:

        :returns:
            La diferencia entre el precio de el curso y los pagos realizados.
        """
        return self.curso.precio - self.pagos

    @property
    def pagada(self):
        """
        :rtype bool:

        :returns:
            Retorna verdadero si los pagos cubren el precio de el curso, de lo contrario, retorna
            falso.
        """
        return self.pagos >= self.curso.precio

    def __str__(self):
        return '{self.estudiante} - {self.curso}'.format(self=self)


class Abono(models.Model):
    """Modelo para guardar los pagos que son abonados a las matriculas"""

    valor = models.IntegerField(verbose_name=_('Valor'))
    fecha = models.DateTimeField(verbose_name=_('Fecha'))
    matricula = models.ForeignKey(Materia, related_name='abonos', on_delete=models.CASCADE)

    def __str__(self):
        return 'Abono ${self.valor} al curso {self.matricula.curso}'.format(self=self)


class Seguimiento(models.Model):
    """Modelo para guardar el seguimiento de asistencia y notas de un estudiante matriculado."""

    asistencia = models.BooleanField(verbose_name=_('Asistencia'))
    nota = models.IntegerField(verbose_name=_('Nota'))
    matricula = models.ForeignKey(Matricula, verbose_name=_('Matricula'), related_name='asistencias', on_delete=models.CASCADE)
    sesion = models.ForeignKey(Sesion, verbose_name=_('Sesión'), on_delete=models.CASCADE)
