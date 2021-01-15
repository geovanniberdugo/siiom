# Django Packages
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Locale Apps
from .managers import SolicitudRegistroManager
from .utils import pdf_to_png, get_media_url, get_filenames

# Python Packages
import re


__all__ = (
    'TipoDocumento', 'PalabraClave', 'Registro', 'Documento',
    'SolicitudRegistro', 'SolicitudCustodiaDocumento',
)


class TipoDocumento(models.Model):
    """Modelo para guardar los tipos de documentos que manejan las distintas áreas de una iglesia."""

    nombre = models.CharField(_('nombre'), max_length=100)
    areas = models.ManyToManyField('organizacional.Area', verbose_name=_('áreas'), related_name='tipos_documento')

    class Meta:
        verbose_name = _('tipo de documento')
        verbose_name_plural = _('tipos de documento')

    def __str__(self):
        return self.nombre.capitalize()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.lower()
        super(TipoDocumento, self).save(*args, **kwargs)


class PalabraClave(models.Model):
    """Modelo que guarda las palabras claves que se usan en los registros."""

    nombre = models.CharField(_('nombre'), max_length=250, unique=True)

    class Meta:
        verbose_name = _('palabra clave')
        verbose_name_plural = _('palabras claves')

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.lower()
        super(PalabraClave, self).save(*args, **kwargs)


class Registro(models.Model):
    """Modelo para guardar los registros de información de una iglesia."""

    area = models.ForeignKey('organizacional.Area', verbose_name=_('área'), related_name='registros', on_delete=models.CASCADE)
    descripcion = models.TextField(_('descripción'))
    fecha = models.DateField(_('fecha'))
    palabras_claves = models.ManyToManyField(
        PalabraClave,
        verbose_name=_('palabras claves'),
        related_name='registros',
        blank=True
    )
    estante = models.IntegerField(verbose_name=_('estante'))
    caja = models.IntegerField(verbose_name=_('caja'))
    modificado_por = models.ForeignKey(
        'organizacional.Empleado', verbose_name=_('Modificado Por'), blank=True, null=True, on_delete=models.SET_NULL
    )
    ultima_modificacion = models.DateField(verbose_name=_('Fecha Última Modificación'), blank=True, null=True)

    class Meta:
        verbose_name = _('registro')
        verbose_name_plural = _('registros')

    def __str__(self):
        return "Estante {0} Caja {1}".format(self.estante, self.caja)

    @property
    def solicitado(self):
        """
        Retorna True si el registro esta solicitado
        """
        if self.solicitudregistro_set.exclude(estado=SolicitudRegistro.DEVUELTO_CONSULTA):
            return True
        return False


class Documento(models.Model):
    """Modelo que guarda los archivos relacionados a un registro."""

    def ruta_archivo(self, filename):
        match = re.compile(r'[a-zA-ZñNáÁéÉíÍóÓúÚ\s0-9_]')
        data_name = filename.split('.')
        ext = data_name[len(data_name) - 1]
        del data_name[data_name.index(ext)]
        name = ''.join(match.findall(''.join(data_name)))
        filename = name + '.' + ext
        registro = self.registro
        return 'gestion_documental/area_{}/registro_{}/{}'.format(registro.area.id, registro.id, filename)

    registro = models.ForeignKey(Registro, verbose_name=_('registro'), related_name='documentos', on_delete=models.CASCADE)
    tipo_documento = models.ForeignKey(TipoDocumento, verbose_name=_('tipo de documento'), related_name='documentos', on_delete=models.CASCADE)
    archivo = models.FileField(_('archivo'), upload_to=ruta_archivo)

    class Meta:
        verbose_name = _('documento')
        verbose_name_plural = _('documentos')

    def __str__(self):
        name = self.archivo.name.split('/')
        return "{}".format(name[len(name) - 1].split('.')[0])

    @property
    def is_image(self):
        if self.archivo.path.endswith('.pdf'):
            return False
        return True

    def get_absolute_url(self):
        """
        Devuelve la ruta url de el documento
        """
        if self.is_image:
            return self.archivo.url
        # ruta = pdf_to_png(self.archivo, ruta=True)
        ruta = pdf_to_png(self.archivo)
        archivos = get_filenames(self.archivo)
        return [get_media_url(ruta + x) for x in archivos]

    def save(self, *args, **kwargs):
        super(Documento, self).save(*args, **kwargs)
        if not self.is_image:
            pdf_to_png(self.archivo, save=True)


class SolicitudRegistro(models.Model):
    """
    Modelo de solicitud de registros
    """
    PENDIENTE = 'PE'
    ENTREGADO_DIGITADOR = 'ED'
    DEVUELTO_CONSULTA = 'DC'

    OPCIONES_ESTADO = (
        (PENDIENTE, 'PENDIENTE'),
        (ENTREGADO_DIGITADOR, 'ENTREGADO POR DIGITADOR'),
        (DEVUELTO_CONSULTA, 'DEVUELTO POR USUARIO DE CONSULTA'),
    )

    registro = models.ForeignKey(Registro, verbose_name=_('Registro'), on_delete=models.CASCADE)
    usuario_solicita = models.ForeignKey(
        'organizacional.Empleado', related_name='solicitudes', verbose_name=_('Solicitante'), on_delete=models.CASCADE
    )
    estado = models.CharField(max_length=2, verbose_name=_('Estado Solicitud'), choices=OPCIONES_ESTADO)
    fecha_solicitud = models.DateField(auto_now_add=True, verbose_name=_('Fecha Solicitud'))
    fecha_devolucion = models.DateField(blank=True, verbose_name=_('Fecha Devolución'), null=True)
    comentario = models.TextField(verbose_name=_('Comentario'), blank=True)
    usuario_autoriza = models.ForeignKey(
        'organizacional.Empleado', related_name='autorizaciones', verbose_name=_('Autoriza'),
        blank=True, null=True, on_delete=models.SET_NULL
    )

    objects = SolicitudRegistroManager()

    class Meta:
        verbose_name = _('Solicitud de Registro')
        verbose_name_plural = _('Solicitudes de Registro')

    def __str__(self):
        return "Solicitud No. {}".format(self.id)


class SolicitudCustodiaDocumento(models.Model):
    """
    Modelo para las solicitudes de custodia de documentos
    """
    PENDIENTE = 'PE'
    PROCESO = 'PR'
    REALIZADO = 'RE'

    OPCIONES_ESTADO = (
        (PENDIENTE, 'PENDIENTE'),
        (REALIZADO, 'REALIZADO'),
        (PROCESO, 'PROCESO'),
    )

    fecha_solicitud = models.DateField(auto_now_add=True, verbose_name=_('Fecha Solicitud'))
    solicitante = models.ForeignKey(
        'organizacional.Empleado', verbose_name=_('Solicitante'), related_name='solicitudes_custodia', on_delete=models.CASCADE
    )
    area = models.ForeignKey('organizacional.Area', verbose_name=_('Área'), on_delete=models.CASCADE)
    tipo_documento = models.ForeignKey(TipoDocumento, verbose_name=_('Tipo de Documento'), on_delete=models.CASCADE)
    descripcion = models.TextField(verbose_name=_('Descripción'))
    estado = models.CharField(max_length=2, choices=OPCIONES_ESTADO, verbose_name=_('Estado'), default=PENDIENTE)
    usuario_recibe = models.ForeignKey(
        'organizacional.Empleado', verbose_name=_('Usuario Recibe Documento'),
        related_name='solicitudes_custodia_recibidas', on_delete=models.CASCADE
    )
