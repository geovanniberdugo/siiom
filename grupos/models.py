# Django Package
from django.db import models, transaction, OperationalError
from django.utils.translation import ugettext_lazy as _lazy
from django.utils.functional import cached_property
from treebeard.al_tree import AL_Node

# Locale Apps
from miembros.models import CambioTipo
from common.decorators import cache_value
from common.models import DiasSemanaMixin
from consolidacion.utils import clean_direccion
from .managers import (
    GrupoManager, GrupoManagerStandard, HistorialManager, PredicaManager,
    ReunionDiscipuladoManager, ReunionGARManager
)
from .six import SixALNode

__all__ = (
    'Red', 'Grupo', 'Predica', 'ReunionGAR', 'HistorialEstado',
    'ReunionDiscipulado', 'AsistenciaDiscipulado',
)


class Red(models.Model):
    """Modelo para guardar las redes que tiene una iglesia."""

    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Grupo(DiasSemanaMixin, SixALNode, AL_Node):
    """
    Representa los grupos de una iglesia.

    Los grupos se categorizan se clasifican según su estado.

        * ``ACTIVO`` Este estado es aplicado a grupos que realicen todas las funciones
            que un grupo hace, es decir: reunion de G.A.R, reunion de discipulado, etc.

        * ``INACTIVO`` Este estado es aplicado a grupos que en la actualidad no se
            encuentran realizando reuniones de G.A.R, pero realizan encuentros, reuniones
            de dicipulado, etc.

        * ``SUSPENDIDO`` Este estado es aplicado a grupos que en la actualidad no realizan
            ninguna acción de grupos, pero no quiere ser archivado.

        * ``ARCHIVADO`` Este estado es aplicado a grupos que serán eliminados.
    """

    ACTIVO = 'A'
    INACTIVO = 'I'

    ESTADOS = (
        (ACTIVO, 'Activo'),
        (INACTIVO, 'Inactivo'),
    )

    parent = models.ForeignKey(
        'self', verbose_name=_lazy('grupo origen'), related_name='children_set', null=True, blank=True, db_index=True, on_delete=models.SET_NULL
    )
    direccion = models.CharField(verbose_name=_lazy('dirección'), max_length=50)
    fechaApertura = models.DateField(verbose_name=_lazy('fecha de apertura'))
    diaGAR = models.CharField(verbose_name=_lazy('dia G.A.R'), max_length=1, choices=DiasSemanaMixin.DIAS_SEMANA)
    horaGAR = models.TimeField(verbose_name=_lazy('hora G.A.R'))
    diaDiscipulado = models.CharField(
        verbose_name=_lazy('dia discipulado'), max_length=1, choices=DiasSemanaMixin.DIAS_SEMANA, blank=True, null=True
    )
    horaDiscipulado = models.TimeField(verbose_name=_lazy('hora discipulado'), blank=True, null=True)
    nombre = models.CharField(verbose_name=_lazy('nombre'), max_length=255)
    red = models.ForeignKey(Red, verbose_name=('red'), null=True, blank=True, on_delete=models.SET_NULL)
    barrio = models.ForeignKey('miembros.Barrio', verbose_name=_lazy('barrio'), on_delete=models.CASCADE)

    # campos para ubicaciones en mapas
    latitud = models.FloatField(verbose_name='Latitud', blank=True, null=True)
    longitud = models.FloatField(verbose_name='Longitud', blank=True, null=True)

    # managers
    _objects = GrupoManagerStandard()  # contiene los defaults de django
    objects = GrupoManager()

    node_order_by = ['id']

    class Meta:
        verbose_name = _lazy('grupo')
        verbose_name_plural = _lazy('grupos')
        base_manager_name = '_objects'

    def __str__(self):
        if self.estado == self.historiales.model.ARCHIVADO:
            return self.get_nombre()

        lideres = ["{0} {1}({2})".format(
            lider.nombre.upper(), lider.primer_apellido.upper(), lider.cedula
        ) for lider in self.lideres.all()]

        return " - ".join(lideres)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.historiales.exists():
            self.actualizar_estado(estado=self.historiales.model.ACTIVO)

    @classmethod
    def _obtener_arbol_recursivamente(cls, padre, resultado):
        """
        Construye el organigrama de forma recursiva.
        """

        lista_hijos = []
        for hijo in padre.get_children().prefetch_related('lideres'):
            cls._obtener_arbol_recursivamente(hijo, lista_hijos)

        resultado.append(padre)
        if lista_hijos:
            resultado.append(lista_hijos)

    @classmethod
    def obtener_arbol(cls, padre=None):
        """
        :returns:
            El organigrama en una lista de listas incluyendo el padre, que me indica como va el desarrollo de los
            grupos.

        :param padre:
            El grupo inicial desde donde sa va mostrar el organigrama. Si no se indica se muestra todo el organigrama
            de una iglesia.
        """

        # TODO Mejorar en la doc que retorna con un ejemplo usar como guia el metodo get get_annotated_list de
        # http://django-treebeard.readthedocs.io/en/latest/api.html#treebeard.models.Node.add_child

        arbol = []
        if padre is None:
            padre = cls.objects.raiz()

        if padre is not None:
            cls._obtener_arbol_recursivamente(padre, arbol)

        return arbol

    # Deprecado
    @classmethod
    def obtener_arbol_viejo(cls, raiz=None):  # pragma: no cover
        """
        :returns:
            El arbol en una lista de listas incluyendo el padre, que me indica como va el desarrollo de los
            grupos.
        """

        arbol = []
        if raiz is None:
            raiz = cls.objects.raiz()

        if raiz is not None:
            pila = [[raiz]]
            act = None
            bajada = True

            discipulos = list(raiz.get_children().select_related('parent').prefetch_related('lideres'))
            while len(discipulos) > 0:
                hijo = discipulos.pop()
                if hijo:
                    if act is not None:
                        pila.append(act)
                    sw = True
                    while len(pila) > 0 and sw:
                        act = pila.pop()
                        if act[len(act) - 1] == hijo.parent:
                            act.append([hijo])
                            bajada = True
                            sw = False
                        elif act[len(act) - 2] == hijo.parent:
                            act[len(act) - 1].append(hijo)
                            bajada = True
                            sw = False
                        elif isinstance(act[-1], (tuple, list)) and bajada:
                            pila.append(act)
                            pila.append(act[len(act) - 1])
                        elif not isinstance(act[-1], (tuple, list)):
                            bajada = False
                hijos = hijo.get_children().select_related('parent').prefetch_related('lideres')
                if len(hijos) > 0:
                    discipulos.extend(list(hijos))
            if pila:
                arbol = pila[0]
            else:
                arbol = act

        return arbol

    @classmethod
    def obtener_ruta(cls, inicial, final):
        """
        :returns:
            Una lista con los grupos que conforman la ruta que hay desde el grupo inicial al grupo final
            incluyendo estos grupos.

        :param inicial:
            Grupo en cual inicia la ruta.

        :param final:
            Grupo en el cual termina la ruta.
        """

        ruta = []
        grupo = final

        while grupo != inicial:
            ruta.insert(0, grupo)
            grupo = grupo.get_parent()

        ruta.insert(0, inicial)
        return ruta

    @cached_property
    def nombre_corto(self):
        """
        :returns:
            Un string con los primeros apellidos de los lideres del grupo.
        """

        apellidos = self.lideres.order_by('primer_apellido').values_list('primer_apellido', flat=True)
        return ' - '.join(apellidos).upper()

    @property
    def discipulos(self):
        """
        :returns:
            Un queryset con los miembros del grupo actual que son lideres.

        .. note::

            Es considerado lider todo miembro que tenga permiso de líder.
        """

        return self.miembros.lideres()

    @property
    def reuniones_GAR_sin_ofrenda_confirmada(self):
        """
        :returns:
            Un queryset con las reuniones GAR del grupo actual que no tienen la ofrenda confirmada.
        """

        return self.reuniones_gar.filter(confirmacionEntregaOfrenda=False)

    @property
    def reuniones_discipulado_sin_ofrenda_confirmada(self):
        """
        :returns:
            Un queryset con las reuniones de discipulado del grupo actual que no tienen la ofrenda confirmada.
        """

        return self.reuniones_discipulado.filter(confirmacionEntregaOfrenda=False)

    @cached_property
    def grupos_red(self):
        """
        :returns:
            Un queryset con la subred del grupo actual.

        .. note::

            Entiéndase por subred todos los descendientes del grupo actual incluyéndose asimismo.
        """

        from .utils import convertir_lista_grupos_a_queryset
        return convertir_lista_grupos_a_queryset(self.get_tree(self))

    @property
    @cache_value(key='cabeza_red', suffix='pk')
    def cabeza_red(self):
        """
        :returns:
            El grupo cabeza de red del grupo actual o ``None`` si el grupo actual se encuentra por encima de los
            cabezas de red.

        .. note::

            Entiéndase por cabeza de red un grupo que se encuentra dentro de los 72 del pastor presidente, es decir,
            un grupo que se encuentra dos niveles mas abajo que la raiz del arbol.
        """

        ancestros = self.get_ancestors()
        if self.get_depth() == 3:
            return self
        elif len(ancestros) > 2:
            return ancestros[2]
        else:
            return None

    @property
    @cache_value(key='numero_celulas', suffix='pk')
    def numero_celulas(self):
        """
        :returns:
            El numero de grupos a cargo que tiene el grupo actual, incluyendose el mismo.
        """

        return self.get_descendant_count() + 1

    @property
    def estado(self):
        """
        Retorna el estado del grupo de acuerdo a su historial.

        :rtype: str
        """

        return getattr(self, 'estado_anotado', None) or getattr(self.historiales.first(), 'estado', None)

    @property
    def is_activo(self):
        """
        :returns:
            ``True`` si el estado del grupo es activo.

        :rtype: bool
        """
        return self.estado == self.historiales.model.ACTIVO
    
    def padre_subred(self, grupo):
        """
        :returns:
            El grupo padre(raíz) de la subred a la que pertenece el grupo actual, siendo el grupo ingresado
            a partir de donde se va a buscar el arbol.
        
        :param grupo:
            Grupo a partir del cual se van a buscar los hijos de donde se va a sacar la raiz de la subred.
        """

        ruta = self.obtener_ruta(grupo, self)
        if len(ruta) > 1:
            return ruta[1]
        
        return None

    def get_estado_display(self):
        """
        :returns:
            Estado display del grupo de acuerdo a su historial.
        """

        return [estado[1] for estado in self.historiales.model.OPCIONES_ESTADO if estado[0] == self.estado][0]

    def confirmar_ofrenda_reuniones_GAR(self, reuniones):
        """
        Confirma la ofrenda de las reuniones GAR ingresadas del grupo actual.

        :param list[int] reuniones:
            Contiene los ids de las reuniones a confirmar.
        """

        self.reuniones_gar.filter(id__in=reuniones).update(confirmacionEntregaOfrenda=True)

    def confirmar_ofrenda_reuniones_discipulado(self, reuniones):
        """
        Confirma la ofrenda de las reuniones de discipulado ingresadas del grupo actual.

        :param list[int] reuniones:
            Contiene los ids de las reuniones a confirmar.
        """

        self.reuniones_discipulado.filter(id__in=reuniones).update(confirmacionEntregaOfrenda=True)

    def trasladar(self, nuevo_padre):
        """
        Traslada el grupo actual y sus descendientes debajo de un nuevo grupo en el arbol. A los lideres del grupo
        actual, se les modifica el grupo al que pertenecen, al nuevo grupo.

        :param nuevo_padre:
            Grupo que va ser usado como nuevo padre del grupo actual que se esta trasladando.

        :raise InvalidMoveToDescendant:
            Cuando se intenta trasladar el grupo actual debajo de uno de sus descendientes.
        """

        with transaction.atomic():
            if nuevo_padre != self.parent:
                self.move(nuevo_padre, pos='sorted-child')
                self.lideres.all().update(grupo=nuevo_padre)

                if nuevo_padre.red != self.red:
                    grupos = [grupo.id for grupo in self._get_tree(self)]
                    Grupo._objects.filter(id__in=grupos).update(red=nuevo_padre.red)

    def _trasladar_miembros(self, nuevo_grupo):
        """
        Traslada todos los miembros que no lideran grupo del grupo actual al nuevo grupo.

        :param nuevo_grupo:
            Grupo al cual van a pertenecer los miembros que se van a trasladar.
        """

        self.miembros.filter(grupo_lidera=None).update(grupo=nuevo_grupo)

    def _trasladar_visitas(self, nuevo_grupo):
        """
        Traslada todas las visitas del grupo actual al nuevo grupo.

        :param nuevo_grupo:
            Grupo al cual van a pertenecer las visitas que se van a trasladar.
        """

        self.visitas.update(grupo=nuevo_grupo)

    def _trasladar_encontristas(self, nuevo_grupo):
        """
        Traslada todos los encontristas del grupo actual al nuevo grupo.

        :param nuevo_grupo:
            Grupo al cual van a pertenecer los encontristas que se van a trasladar.
        """

        self.encontristas.update(grupo=nuevo_grupo)

    def _trasladar_reuniones_gar(self, nuevo_grupo):
        """
        Traslada todas las reuniones GAR del grupo actual al nuevo grupo.

        :param nuevo_grupo:
            Grupo al cual van a pertenecer las reuniones GAR que se van a trasladar.
        """

        self.reuniones_gar.update(grupo=nuevo_grupo)

    def _trasladar_reuniones_discipulado(self, nuevo_grupo):
        """
        Traslada todas las reuniones de discipulado del grupo actual al nuevo grupo.

        :param nuevo_grupo:
            Grupo al cual van a pertenecer las reuniones de discipulado que se van a trasladar.
        """

        self.reuniones_discipulado.update(grupo=nuevo_grupo)

    def fusionar(self, nuevo_grupo):
        """
        Traslada la información asociada al grupo actual (visitas, encontristas, reuniones, miembros, etc) al
        nuevo grupo y elimina el grupo actual.

        :param nuevo_grupo:
            Grupo al cual va a pertenecer la información que se va a trasladar.
        """

        if self != nuevo_grupo:
            with transaction.atomic():
                for hijo in self.get_children():
                    hijo.trasladar(nuevo_grupo)

                self._trasladar_visitas(nuevo_grupo)
                self._trasladar_miembros(nuevo_grupo)
                self._trasladar_encontristas(nuevo_grupo)
                self._trasladar_reuniones_gar(nuevo_grupo)
                self._trasladar_reuniones_discipulado(nuevo_grupo)

                self.delete()

    def get_nombre(self):
        """
        Retorna el nombre del grupo.

        :rtype: str
        """
        return self.nombre

    def miembrosGrupo(self):
        """Devuelve los miembros de un grupo (queryset) sino tiene, devuelve el queryset vacio."""

        lideres = CambioTipo.objects.filter(nuevoTipo__nombre__iexact='lider').values('miembro')
        miembros = CambioTipo.objects.filter(nuevoTipo__nombre__iexact='miembro').values('miembro')
        return self.miembros.filter(id__in=miembros).exclude(id__in=lideres)

    def get_direccion(self):
        """
        :returns:
            La direccion de manera legible para los buscadores de mapas
        """
        if self.get_position() is None:
            return clean_direccion(self.direccion)
        else:
            return ','.join([str(x) for x in self.get_position()])

    def get_position(self):
        """
        :returns:
            Las coordenadas de un grupo o `None` en caso de no tener last coordenadas.
        """
        if self.latitud is not None and self.longitud is not None:
            return [self.latitud, self.longitud]
        return None

    def actualizar_estado(self, estado, **kwargs):
        """
        Actualiza el estado de el grupo en su historial.

        :param estado:
            El estado que se asignara.
        """

        actual = self.historiales.first()

        if actual is None:
            self.__class__.objects.get_queryset().get_historial_model().objects.create(
                grupo=self, estado=estado, **kwargs)
        elif estado != actual.estado:
            if estado not in list(map(lambda x: x[0], actual.OPCIONES_ESTADO)):
                raise OperationalError(_lazy('Estado "{}" no está permitido'.format(estado)))
            actual.__class__.objects.create(grupo=self, estado=estado, **kwargs)

    def reunion_discipulado_reportada(self, predica):
        """
        :returns:
            ``True`` si la reunión ya fue reportada
        
        :param :class:`Predica` predica: Predica a partir de la cual se buscara la reunión.

        :rtype: bool
        """

        return self.reuniones_discipulado.filter(predica=predica).exists()

class Predica(models.Model):
    """Modelo para guardar las predicas que se registran."""

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(max_length=500, blank=True)
    miembro = models.ForeignKey('miembros.Miembro', on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)

    # Managers
    objects = PredicaManager()

    def __str__(self):
        return self.nombre.upper()


class Enseñanza(models.Model):
    """Modelo para guardar el documento de enseñanza que se sube a siiom."""

    GRUPO = 'GR'
    DISCIPULADO = 'DI'

    OPCIONES_ENSEÑANZA = (
        (GRUPO, 'GRUPO'),
        (DISCIPULADO, 'DISCIPULADO'),
    )

    def ruta_archivo(self, filename):
        return "ensenanzas/%s/%s" % (self.tipo, filename)

    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=2, choices=OPCIONES_ENSEÑANZA, verbose_name=_lazy('tipo')) 
    creado_por = models.ForeignKey('miembros.Miembro', related_name='enseñanzas_creadas', on_delete=models.CASCADE)
    fecha_inicial = models.DateField()
    fecha_final = models.DateField()
    archivo = models.FileField(_lazy('archivo'), upload_to=ruta_archivo)

    class Meta:
        permissions = (
            ("can_see_enseñanzas", "Usuario puede ver enseñanzas"),
        )

    def __str__(self):
        return self.nombre.upper()

class ReunionGAR(models.Model):
    """Modelo para guardar las reuniones de grupo de amistad que hace cada grupo."""

    fecha = models.DateField()
    grupo = models.ForeignKey(Grupo, related_name='reuniones_gar', on_delete=models.CASCADE)
    predica = models.CharField(max_length=100, verbose_name='prédica')
    numeroTotalAsistentes = models.PositiveIntegerField(verbose_name='Número total de asistentes')
    numeroLideresAsistentes = models.PositiveIntegerField(verbose_name='Número de líderes asistentes')
    numeroVisitas = models.PositiveIntegerField(verbose_name='Número de visitas:')
    novedades = models.TextField(max_length=500, default="nada", null=True, blank=True)
    ofrenda = models.DecimalField(max_digits=19, decimal_places=2)
    confirmacionEntregaOfrenda = models.BooleanField(default=False)
    digitada_por_miembro = models.BooleanField(default=True)

    # Managers
    objects = ReunionGARManager()

    def __str__(self):
        return self.grupo.__str__()

    class Meta:
        permissions = (
            ("puede_confirmar_ofrenda_GAR", "puede confirmar la entrega de dinero GAR"),
        )

    @classmethod
    def no_realizada(cls, grupo, fecha, digitada_por_miembro=True):
        """
        Crea una reunionGAR no guardada en la base de datos.

        :param grupo: Grupo al cual se le va a crear la reunión.
        :param date fecha: Fecha de la reunión.
        :param bool digitada_por_miembro: Indica si la reunión es ingresada por un miembro. Por defecto es ``True``.

        :rtype: :py:class:`ReunionGAR`
        """

        return cls(
            fecha=fecha, grupo=grupo, digitada_por_miembro=digitada_por_miembro,
            predica='No se hizo grupo', ofrenda=0, numeroTotalAsistentes=0,
            numeroLideresAsistentes=0, numeroVisitas=0, confirmacionEntregaOfrenda=True,
        )

    @property
    def realizada(self):
        """
        :returns:
            ``True`` si la reunionGAR fue realizada.
        """
        if self.numeroLideresAsistentes > 0:
            return True
        else:
            if self.numeroTotalAsistentes > 0:
                return True
        return False


class ReunionDiscipulado(models.Model):
    """Modelo para guardar las reuniones de discpulados por grupo."""

    fecha = models.DateField(auto_now_add=True)
    grupo = models.ForeignKey(Grupo, related_name='reuniones_discipulado', on_delete=models.CASCADE)
    predica = models.ForeignKey(Predica, verbose_name='prédica', on_delete=models.CASCADE)
    novedades = models.TextField(max_length=500)
    ofrenda = models.DecimalField(max_digits=19, decimal_places=2)
    confirmacionEntregaOfrenda = models.BooleanField(default=False)

    objects = ReunionDiscipuladoManager()

    def __str__(self):
        return str(self.grupo)

    class Meta:
        permissions = (
            ("puede_confirmar_ofrenda_discipulado", "puede confirmar la entrega de dinero discipulado"),
        )


class AsistenciaDiscipulado(models.Model):
    """Modelo para guardar la asistencia de los miembros a los discipulados."""

    miembro = models.ForeignKey('miembros.Miembro', related_name='discipulados', on_delete=models.CASCADE)
    reunion = models.ForeignKey(ReunionDiscipulado, related_name='asistencia', on_delete=models.CASCADE)
    asistencia = models.BooleanField()

    def __str__(self):
        return '{} - {}'.format(self.miembro, self.reunion)


class HistorialEstado(models.Model):
    """
    Modelo para guardar historial de cambio de estado de los grupos.

        **Significado de cada estado**

           * ``ACTIVO`` Este estado es aplicado a grupos que realicen todas las funciones
             que un grupo hace, es decir: reunion de G.A.R, reunion de discipulado, etc.

           * ``INACTIVO`` Este estado es aplicado a grupos que en la actualidad no se
             encuentran realizando reuniones de G.A.R, pero realizan encuentros, reuniones
             de dicipulado, etc.

           * ``SUSPENDIDO`` Este estado es aplicado a grupos que en la actualidad no realizan
             ninguna acción de grupos, pero no quiere ser archivado.

           * ``ARCHIVADO`` Este estado es aplicado a grupos que serán eliminados.


        **Usabilidad**

            Solo se podrá tener un ``estado`` diferente de seguido para cada grupo, es decir,
            no se podrán tener dos estados de ``ACTIVO`` de seguido para el mismo grupo.

            Ante el caso de una posible repetición de ``estado``, la creación de el historial del
            estado será abortada.
    """

    ACTIVO = 'AC'
    INACTIVO = 'IN'
    SUSPENDIDO = 'SU'
    ARCHIVADO = 'AR'

    OPCIONES_ESTADO = (
        (ACTIVO, 'ACTIVO'),
        (INACTIVO, 'INACTIVO'),
        (SUSPENDIDO, 'SUSPENDIDO'),
        (ARCHIVADO, 'ARCHIVADO'),
    )

    grupo = models.ForeignKey(Grupo, related_name='historiales', verbose_name=_lazy('grupo'), on_delete=models.CASCADE)
    fecha = models.DateTimeField(verbose_name=_lazy('fecha'), auto_now_add=True)
    estado = models.CharField(max_length=2, choices=OPCIONES_ESTADO, verbose_name=_lazy('estado'))

    objects = HistorialManager()

    def __str__(self):
        return 'Historial {estado} para grupo: {self.grupo}'.format(self=self, estado=self.get_estado_display())

    class Meta:
        verbose_name = _lazy('Historial')
        verbose_name_plural = _lazy('Historiales')
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        """
        Guarda una instancia de EstadoHistorial

        .. warning::
            Si el grupo tiene en su último historial, el mismo estado del historial actual
            a guardar, entonces, este será omitido.
        """

        with transaction.atomic():
            last = self.grupo.historiales.first()
            if last is None or last.estado != self.estado:
                if self.estado == self.ARCHIVADO:
                    self.grupo.nombre = '{} (ARCHIVADO)'.format(self.grupo.__str__())
                    self.grupo.save()
                return super().save(*args, **kwargs)
