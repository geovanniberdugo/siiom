# Django imports
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _lazy, ugettext as _

# Locale imports
from .managers import MiembroManager
from common.models import UtilsModelMixin


__all__ = (
    'Zona', 'Barrio', 'TipoMiembro', 'CambioTipo', 'Miembro',
)


def _PredicaModel():
    return import_string('grupos.models.Predica')


class Escalafon(models.Model):
    """
    Modelo para crear las carreras del lider.
    """

    nombre = models.CharField(_lazy('nombre'), max_length=200)
    cantidad_grupos = models.IntegerField(_lazy('cantidad grupos'))

    class Meta:
        verbose_name_plural = _lazy('Escalafones')

    def __str__(self):
        return self.nombre.upper()


class Zona(models.Model):
    """Modelo para guardar las zonas."""

    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre.upper()


class Barrio(models.Model):
    """Modelo para guardar los barrios."""

    nombre = models.CharField(max_length=50)
    zona = models.ForeignKey(Zona, null=False, on_delete=models.CASCADE)

    def __str__(self):
        return '{}'.format(self.nombre.upper())


class TipoMiembro(models.Model):
    """Modelo para guardar los tipos de miembros que puede tener un miembro."""

    nombre = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre.upper()


class Miembro(UtilsModelMixin, models.Model):
    """
    Modelo para guardar los miembros de una iglesia.
    """

    def ruta_imagen(self, filename):
        ruta = 'media/profile_pictures/user_%s/%s' % (self.id, filename)
        return ruta

    FEMENINO = 'F'
    MASCULINO = 'M'

    GENEROS = (
        (FEMENINO, _lazy('Femenino')),
        (MASCULINO, _lazy('Masculino')),
    )

    ACTIVO = 'A'
    INACTIVO = 'I'
    RESTAURACION = 'R'

    ESTADOS = (
        (ACTIVO, _lazy('Activo')),
        (INACTIVO, _lazy('Inactivo')),
        (RESTAURACION, _lazy('Restauración')),
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

    #  autenticacion
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_lazy('usuario'), unique=True, null=True, blank=True, on_delete=models.SET_NULL
    )
    #  info personal
    nombre = models.CharField(_lazy('nombre'), max_length=50)
    primer_apellido = models.CharField(_lazy('primer apellido'), max_length=50)
    segundo_apellido = models.CharField(_lazy('segundo apellido'), max_length=50, null=True, blank=True)
    genero = models.CharField(_lazy('género'), max_length=1, choices=GENEROS)
    telefono = models.CharField(_lazy('teléfono'), max_length=50, null=True, blank=True)
    celular = models.CharField(_lazy('celular'), max_length=50, null=True, blank=True)
    talla = models.CharField(_lazy('talla'), max_length=5, blank=True)
    fecha_nacimiento = models.DateField(_lazy('fecha de nacimiento'), null=True, blank=True)
    cedula = models.CharField(
        _lazy('cédula'), max_length=25, unique=True, validators=[RegexValidator(r'^[0-9]+$', "Se aceptan solo numeros")]
    )
    direccion = models.CharField(_lazy('dirección'), max_length=100, null=True, blank=True)
    barrio = models.ForeignKey(Barrio, verbose_name=_lazy('barrio'), null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(_lazy('email'), unique=True)
    profesion = models.CharField(_lazy('profesion'), max_length=100, null=True, blank=True)
    estado_civil = models.CharField(
        _lazy('estado civil'), max_length=1, choices=ESTADOS_CIVILES, null=True, blank=True
    )
    conyugue = models.ForeignKey(
        'self', verbose_name=_lazy('cónyugue'), related_name='casado_con', null=True, blank=True, on_delete=models.SET_NULL
    )
    foto_perfil = models.ImageField(_lazy('foto perfil'), upload_to=ruta_imagen, null=True, blank=True)
    portada = models.ImageField(_lazy('portada'), upload_to=ruta_imagen, null=True, blank=True)

    estado = models.CharField(_lazy('estado'), max_length=1, choices=ESTADOS)
    grupo = models.ForeignKey(
        'grupos.Grupo', verbose_name=_lazy('grupo'),
        related_name='miembros', null=True, blank=True, on_delete=models.SET_NULL
    )  # grupo al que pertenece
    grupo_lidera = models.ForeignKey(
        'grupos.Grupo', verbose_name=_lazy('grupo que lidera'),
        related_name='lideres', null=True, blank=True, on_delete=models.SET_NULL
    )
    escalafon = models.ForeignKey(
        Escalafon, verbose_name=_lazy('escalafon'),
        related_name='lideres', null=True, blank=True, on_delete=models.SET_NULL
    )
    fecha_registro = models.DateField(_lazy('fecha de registro'), auto_now_add=True)

    # managers
    objects = MiembroManager()

    class Meta:
        permissions = (
            ("es_agente", "define si un miembro es agente"),
            ("es_lider", "indica si el usuario es lider de un GAR"),
            ("es_administrador", "es adminisitrador"),
            ("es_pastor", "indica si un miembro es pastor"),
            ("es_tesorero", "indica si un miembro es tesorero"),
            ("es_coordinador", "indica si un miembro es coordinador"),
            ("es_maestro", "indica si un miembro es maestro"),
            ("buscar_todos", "indica si un usuario puede buscar miembros"),
        )

    def __str__(self):
        return "{0} {1} ({2})".format(self.nombre.upper(), self.primer_apellido.upper(), self.cedula)

    @property
    def es_director_red(self):
        """
        Indica si el miembro es director de red. Un director de red es un miembro que lidere grupo y sea discipulo
        del pastor presidente.

        :returns:
            ``True`` si el miembro es director de red, de lo contrario retorna ``False``

        :rtype: ``bool``
        """

        return self.grupo_lidera and getattr(self.grupo_lidera, 'get_depth', lambda: None)() == 2

    @property
    def es_cabeza_red(self):
        """
        Indica si el miembro es cabeza de red. Un cabeza de red es un miembro que lidera grupo y que es discipulo
        de un director de red.

        :returns:
            ``True`` si el miembro es cabeza de red, de lo contrario retorna ``False``

        :rtype: ``bool``
        """

        return self.grupo_lidera and getattr(self.grupo_lidera, 'get_depth', lambda: None)() == 3

    @property
    def tiene_subred(self):
        """        
        :returns: ``True`` si grupo que lidera el miembro tiene grupos debajo, de lo contrario ``False``
        :rtype: ``bool``
        """

        return self.grupo_lidera and not self.grupo_lidera.is_leaf()
    
    @property
    def cabeza_red(self):
        """
        :returns:
            El grupo cabeza de red del miembro o ``None`` si el miembro se encuentra por encima de los
            cabezas de red.
        """

        grupo = self.grupo_lidera or self.grupo
        return grupo.cabeza_red
    
    def padre_subred(self, grupo):
        """
        :returns:
            El grupo padre(raíz) de la subred a la que pertenece el miembro actual, siendo el grupo ingresado
            a partir de donde se va a buscar el arbol.
        
        :param grupo:
            Grupo a partir del cual se van a buscar los hijos de donde se va a sacar la raiz de la subred.
        """

        grupo_lider = self.grupo_lidera or self.grupo
        return grupo_lider.padre_subred(grupo)

    def resetear_contrasena(self):
        """Resetea la contreseña del miembro actual. Coloca como nueva contreseña la cedula del miembro."""

        from common.utils import send_mail
        from django.template import loader
        from django.db import connection

        if self.usuario:
            self.usuario.set_password(self.cedula)

            protocol = 'https' if settings.SECURE_SSL_REDIRECT else 'http'
            context = {'nombre': self.nombre.upper(), 'dominio': connection.tenant.domain_url, 'protocolo': protocol}
            message = loader.render_to_string('miembros/emails/contrasena_reseteada.html', context=context)
            send_mail(_('Contraseña reseteada.'), message, [self.email])

    def trasladar(self, nuevo_grupo):
        """
        Traslada el miembro actual a un nuevo grupo.
        """

        if nuevo_grupo != self.grupo:
            self.grupo = nuevo_grupo
            self.save()

    def discipulos(self):
        """
        :returns:
            Un QuerySet con los discipulos del miembro, si no tiene, devuelve un QuerySet vacio.
        """

        grupo = self.grupo_lidera
        if grupo:
            return grupo.miembros.lideres()
        return self.__class__.objects.none()

    def pastores(self):
        """
        :returns:
            Un queryset con los pastores que se encuentran por encima del grupo del miembro actual. Si el
            miembro o alguno de sus colideres es pastor tambien se incluyen.
        """

        grupo = self.grupo_lidera or self.grupo
        ancestros = grupo.get_ancestors()
        ancestros.append(grupo)

        return self.__class__.objects.pastores().filter(grupo_lidera__in=ancestros)
    
    def predicas_recibidas(self):
        """
        :returns:
            Un queryset con las predicas que ha recibido el miembro.
        """

        predicas = self.discipulados.filter(asistencia=True).values_list('reunion__predica', flat=True)
        return _PredicaModel().objects.filter(id__in=predicas)


class CambioTipo(models.Model):
    """
    Modelo para guardar el tipo de cambio que ha tenido cada miembro.
    """

    miembro = models.ForeignKey(Miembro, related_name='miembro_cambiado', on_delete=models.CASCADE)
    autorizacion = models.ForeignKey(Miembro, related_name='miembro_autoriza', on_delete=models.CASCADE)
    nuevoTipo = models.ForeignKey(TipoMiembro, related_name='tipo_nuevo', verbose_name="tipo nuevo", on_delete=models.CASCADE)
    anteriorTipo = models.ForeignKey(TipoMiembro, related_name='tipo_anterior', null=True, verbose_name="tipo anterior", on_delete=models.SET_NULL)
    fecha = models.DateField()

    def __str__(self):
        return '{} - {}'.format(self.miembro, self.nuevoTipo)
