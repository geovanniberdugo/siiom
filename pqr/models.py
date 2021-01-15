# Django Package
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.utils import timezone

# Locale Apps
from .resources import get_festivos
from .managers import CasoManager

# Python Package
import datetime
import calendar
import re


__all__ = ('Caso', 'Comentario', 'Invitacion', 'Documento', )


class Caso(models.Model):
    """
    Modelo de casos para Preguntas, Quejas y Reclamos, el cual tendrá la razón de la
    aplicación
    """

    # Constantes

    # semaforo
    VERDE = 'green'  # range(0, 72)
    AMARILLO = 'yellow'  # range(73, 96)
    ROJO = 'red'  # range(97, ^)
    TEAL = 'teal'  # cuando esta terminada

    # horas de expiracion
    DIAS_PARA_PRESIDENCIA = 4  # equivale a 96 horas
    DIAS_PARA_EXPIRAR = 3  # equivale a 72 horas
    HORAS_RANGO_HABILES = (8, 18)  # Tupla de horas habiles
    #  HORAS_RANGO_NO_HABILES = (19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7)

    # valores de dias de la semana
    LUNES = 0
    MARTES = 1
    MIERCOLES = 2
    JUEVES = 3
    VIERNES = 4
    SABADO = 5
    DOMINGO = 6

    # dias de semana y fines de semana en listas
    _DIAS_SEMANA = [LUNES, MARTES, MIERCOLES, JUEVES, VIERNES]

    _FINES_SEMANA = [SABADO, DOMINGO]

    fecha_acontecimiento = models.DateField(verbose_name=_('fecha acontecimiento'), blank=True, null=True)
    nombre = models.CharField(verbose_name=_('nombre'), max_length=255)
    identificacion = models.BigIntegerField(verbose_name=_('identificación'))
    direccion = models.CharField(verbose_name=_('dirección'), max_length=255, blank=True)
    telefono = models.BigIntegerField(verbose_name=_('teléfono'))
    email = models.EmailField(verbose_name=_('email'))
    descripcion = models.TextField(verbose_name=_('descripción'))
    asunto = models.CharField(verbose_name=_('asunto'), max_length=255)
    fecha_registro = models.DateTimeField(verbose_name=_('fecha registro'), auto_now_add=True)
    integrantes = models.ManyToManyField(
        'organizacional.Empleado', verbose_name=_('integrantes'), related_name='casos_implicado',
        blank=True
    )
    empleado_cargo = models.ForeignKey(
        'organizacional.Empleado', verbose_name=_('empleado a cargo'), related_name='casos_cargo',
        blank=True, null=True, on_delete=models.SET_NULL
    )
    cerrado = models.BooleanField(default=False, verbose_name=_('cerrado'))
    llave = models.SlugField(verbose_name=_('llave'))
    valido = models.BooleanField(default=False, verbose_name=_('valido'))
    fecha_ingreso_habil = models.DateField(verbose_name=_('fecha ingreso hábil'), blank=True, null=True)

    objects = CasoManager()

    class Meta:
        verbose_name = _('Caso PQR')
        verbose_name_plural = _('Casos PQR')

    def __str__(self):
        return 'Caso #{}'.format(self.id)

    def _validacion_expirada(self):
        """
        Retorna verdadero si no se ha validado dentro de 3 dias
        """
        # si no es valido aun
        if not self.valido:
            hoy = timezone.now().date()
            return hoy > self.fecha_registro.date() + datetime.timedelta(days=3)
        # si es valido ya se acabo el tiempo de validacion
        return True

    def _add_days(self, fecha_conteo):
        """
        Funcion que agrega dias a una fecha hasta que esta no sea un fin de semana o festivo
        """
        # se saca el dia de la semana a partir de la fecha parametro
        while calendar.weekday(fecha_conteo.year, fecha_conteo.month, fecha_conteo.day) \
                in self.__class__._FINES_SEMANA or \
                fecha_conteo.date() in get_festivos(self.fecha_registro.year):  # or fecha_conteo
            # se agrega un dia mientras se cumpla la condicion
            fecha_conteo += datetime.timedelta(days=1)
        # luego la devuelve
        return fecha_conteo

    def get_fecha_expiracion(self):
        """
        Devuelve la fecha en que se expira el caso inicialmente para pasar a presidencia
        """
        # la fecha de expiracion existe mientras el caso no este cerrado
        if not self.cerrado:
            # se saca el dia de ingreso
            dia_ingreso = calendar.weekday(
                self.fecha_registro.year, self.fecha_registro.month, self.fecha_registro.day
            )
            # si es un fin de semana o es festivo se agregan los dias hasta que no lo sea
            if dia_ingreso in self.__class__._FINES_SEMANA or \
               self.fecha_registro.date() in get_festivos(self.fecha_registro.year):
                fecha_conteo = self._add_days(self.fecha_registro)
            else:
                fecha_conteo = self.fecha_registro

            # le suma los dias necesarios para saber si esta expirada
            fecha_return = fecha_conteo + datetime.timedelta(days=self.DIAS_PARA_EXPIRAR)

            # se vuelve a validar que no sea festivo o fin de semana
            if calendar.weekday(
               fecha_return.year, fecha_return.month, fecha_return.day
               ) in self.__class__._FINES_SEMANA or \
                    fecha_return in get_festivos(fecha_return.year):
                # de serlo, se le vuelven a sumar los dias hasta que no sea festivo o fin de semana
                fecha_return = self._add_days(fecha_return)
            # se devuelve la fecha
            return fecha_return
        # no se devuelve nada en caso de que este cerrada
        return None

    def get_semaforo(self):
        """
        Devuelve el color de el semaforo de acuerdo a la cantidad de horas pasadas desde que se
        hace valida la solicitud
        """
        hoy = timezone.now()

        if not self.cerrado:
            fecha = self.fecha_ingreso_habil
            # Devuelve Rojo si la fecha para ir a presidencia ya paso y si la fecha de expiracion paso
            if fecha + datetime.timedelta(days=self.__class__.DIAS_PARA_PRESIDENCIA) <= hoy.date() and \
               self._add_days(self.get_fecha_expiracion() + datetime.timedelta(days=1)).date() <= hoy.date():
                return self.__class__.ROJO
            # Devuelve Amarillo si la fecha en la que hace el ingreso mas los dias que debe expirar ya pasaron
            # y si la fecha de expiracion tambien ya paso
            if fecha + datetime.timedelta(days=self.__class__.DIAS_PARA_EXPIRAR) <= hoy.date() \
               and self.get_fecha_expiracion().date() <= hoy.date():
                return self.__class__.AMARILLO
            # De lo contrario devuelve VERDE
            return self.__class__.VERDE
        # retorna otro color
        return self.__class__.TEAL

    def get_documentos_iniciales(self):
        """
        Retorna una lista de los documentos que fueron ingresados por la persona que ingreso el caso
        """
        documentos = []
        for documento in self.documentos.all():
            if not self.comentario_set.filter(mensaje__icontains=documento.get_name()).exists():
                documentos.append(documento)
        return documentos


class Comentario(models.Model):
    """
    Modelo para guardar cada comentario que se le hace a un CASO o PQR, guardando asi
    todos los metadatos relevantes, y respuestas que genere este caso
    """

    mensaje = models.TextField(verbose_name=_('mensaje'))
    fecha = models.DateTimeField(auto_now_add=True, verbose_name=_('fecha'))
    empleado = models.ForeignKey('organizacional.Empleado', verbose_name=_('empleado'), on_delete=models.CASCADE)
    caso = models.ForeignKey(Caso, verbose_name=_('caso'), on_delete=models.CASCADE)
    importante = models.BooleanField(default=False, verbose_name=_('importante'))
    documento = models.BooleanField(default=False, verbose_name=_('documento'))

    def __str__(self):
        return 'Comentario Caso # {0}-{1}'.format(self.caso.id, self.id)

    @property
    def is_documento(self):
        return self.documento


class Invitacion(models.Model):
    """
    Modelo para guardar las posibles invitaciones que se le hagan a los empleados de el
    sistema para invitar a colaborar a un caso
    """

    mensaje = models.TextField(verbose_name=_('mensaje'))
    fecha = models.DateTimeField(auto_now_add=True, verbose_name=_('fecha'))
    emisor = models.ForeignKey(
        'organizacional.Empleado', verbose_name=_('emisor'), related_name='invitaciones_realizadas', on_delete=models.CASCADE
    )
    receptor = models.ForeignKey(
        'organizacional.Empleado', verbose_name=_('receptor'), related_name='invitaciones_recibidas', on_delete=models.CASCADE
    )
    caso = models.ForeignKey(Caso, verbose_name=_('caso'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Invitación')
        verbose_name_plural = _('Invitaciones')

    def __str__(self):
        return 'Invitación a {0}, caso {1}'.format(self.receptor.__str__(), self.caso.id)


class Documento(models.Model):
    """
    Modelo para guardar los documentos de cada Caso
    """

    def ruta_archivo(self, filename):
        match = re.compile(r'[a-zA-ZñÑáÁéÉíÍóÓúÚ\s0-9_]')
        data_name = filename.split('.')
        ext = data_name[len(data_name) - 1]
        del data_name[data_name.index(ext)]
        name = ''.join(match.findall(''.join(data_name)))
        filename = name + '.' + ext
        caso = self.caso
        return 'pqr/caso_{}/{}'.format(caso.id, filename)

    archivo = models.FileField(_('Archivo'), upload_to=ruta_archivo)
    caso = models.ForeignKey(Caso, verbose_name=_('Caso'), related_name='documentos', on_delete=models.CASCADE)

    def __str__(self):
        return self.get_name()

    def save(self, *args, **kwargs):
        empleado = kwargs.pop('empleado', None)
        if empleado is not None:
            self.save_file_as_comment(self, empleado)
        super(Documento, self).save(*args, **kwargs)

    @property
    def is_image(self):
        """"""
        from common.constants import IMAGES
        return self.get_name().split('.')[1] in IMAGES.keys()

    def get_name(self):
        """
        Retorna el nombre de el archivo
        """

        path = self.archivo.path.split('/')
        return path[len(path) - 1]

    def get_absolute_url(self):
        """
        Retorna la url de el archivo para descargar
        """
        return reverse('pqr:descargar_archivos', args=(self.id, ))

    def get_url(self):
        """
        Retorna la url de el archivo para previsualizar
        """
        if self.is_image:
            return self.archivo.url
        return self.get_absolute_url()

    def save_file_as_comment(self, empleado):
        """
        Guarda un archivo como un comentario
        """

        if empleado in self.caso.integrantes.all() or empleado == self.caso.empleado_cargo:
            mensaje = """
                <strong>
                    <a href="{get_absolute_url}" class="c-white">
                    <img src="{get_url}" alt="{get_name}" width="150px"/></a>
                </strong>
            """.format(get_absolute_url=self.get_absolute_url(), get_name=self.get_name(), get_url=self.get_url())
            return Comentario.objects.create(
                empleado=empleado,
                caso=self.caso,
                mensaje=mensaje,
                documento=True
            )
        raise TypeError("Empleado no pertenece a caso")
