import datetime
# Django
from django.db import models, transaction
from django.db.models import OuterRef, Subquery
from django.utils.module_loading import import_string

# Third apps
from treebeard.al_tree import AL_NodeManager

def AsistenciaDiscipuladoModel():
        """
        :returns:
            Modelo de AsistenciaDiscipulado.
        """

        return import_string('grupos.models.AsistenciaDiscipulado')

def HistorialEstadoModel():
        """
        :returns:
            Modelo de HistorialEstado.
        """

        return import_string('grupos.models.HistorialEstado')

class GrupoQuerySet(models.QuerySet):
    """
    Queryset personalizado para los grupos.
    """

    @classmethod
    def get_historial_model(cls):
        """
        :returns:
            Modelo de HistorialEstado.
        """

        return import_string('grupos.models.HistorialEstado')
    
    @classmethod
    def get_reunionGAR_model(cls):
        """
        :returns:
            Modelo de ReunionGAR.
        """

        return import_string('grupos.models.ReunionGAR')

    def red(self, red):
        """
        :retunrs:
            Un queryset con los grupos filtrados por la red ingresada.

        :param red:
            La red usada para filtrar los grupos.
        """

        return self.filter(red=red)

    def annotate_estado(self, fecha=None):
        """
        Annotates los grupos estado actual.

        :param fecha:
            Fecha a partir de la cual se va a consultar el estado que tenia el grupo.
        
        :returns:
            Un annotated queryset de Grupo con el estado en el campo estado_anotado.
        """

        filters = {'grupo': OuterRef('pk')}
        if fecha:
            filters.update({'fecha__lte': fecha})

        latest_estado = HistorialEstadoModel().objects.filter(**filters).values('estado')[:1]
        return self.annotate(estado_anotado=Subquery(latest_estado))

    def _filter_queryset_by_estado(self, estado):
        """Retorna un queryset de acuerdo al estado en el historial del grupo."""

        return self.filter(estado_anotado=estado)

    def _exclude_queryset_by_estado(self, estado):
        """Retorna un queryset de acuerdo al estado en el historial del grupo."""

        return self.exclude(estado_anotado=estado)

    def activos(self):
        """
        :returns:
            Un queryset con los grupos con estado activo.
        """

        return self._filter_queryset_by_estado(HistorialEstadoModel().ACTIVO)

    def inactivos(self):
        """
        :returns:
            Un queryset con los grupos con estado inactivo.
        """

        return self._filter_queryset_by_estado(HistorialEstadoModel().INACTIVO)

    def suspendidos(self):
        """
        :returns:
            Un queryset con los grupos con estado suspendido.
        """

        return self._filter_queryset_by_estado(HistorialEstadoModel().SUSPENDIDO)

    def archivados(self):
        """
        :returns:
            Un queryset con los grupos con estado archivado.
        """

        return self._filter_queryset_by_estado(HistorialEstadoModel().ARCHIVADO)
    
    def no_archivados(self):
        """
        :returns:
            Un queryset con los grupos que no tengan estado archivado.
        """

        return self._exclude_queryset_by_estado(HistorialEstadoModel().ARCHIVADO)
    
    def no_activos(self):
        """
        :returns:
            Un queryset con los grupos que no tengan estado activo.
        """

        return self._exclude_queryset_by_estado(HistorialEstadoModel().ACTIVO)
    
    def no_inactivos(self):
        """
        :returns:
            Un queryset con los grupos que no tengan estado inactivo.
        """

        return self._exclude_queryset_by_estado(HistorialEstadoModel().INACTIVO)
    
    def no_suspendidos(self):
        """
        :returns:
            Un queryset con los grupos que no tengan estado suspendido.
        """

        return self._exclude_queryset_by_estado(HistorialEstadoModel().SUSPENDIDO)
    
    def sin_reportar_reunion_GAR(self, inicial, final):
        """
        :returns:
            Un queryset con los grupos que no han reportado reunión GAR en el rango de fechas ingresado.

        :param date inicial: Fecha inicial en la cual se va a buscar los grupos.
        :param date final: Fecha final en la cual se va a buscar los grupos.
        """

        grupos_que_reportaron = self.get_reunionGAR_model().objects.filter(
            fecha__range=(inicial, final)
        ).values_list('grupo', flat=True)
        return self.activos().exclude(id__in=grupos_que_reportaron)

    def pueden_reportar_discipulado(self):
        """
        :returns:
            Un queryset con los grupos que pueden reportar reunión de discipulado.
        """

        return self.no_suspendidos().exclude(id__in=self.model.objects.hojas())
    
    def faltantes_reportar_discipulado(self, predica):
        """
        :returns:
            Un queryset con lo grupos que no han reportado la reunión de discipulado para la predica ingresada.
        
        :param predica:
            Predica a partir de la cual se van a buscar los grupos.
        """

        return self.pueden_reportar_discipulado().exclude(reuniones_discipulado__predica=predica)

class GrupoManager(AL_NodeManager.from_queryset(GrupoQuerySet)):
    """
    Manager personalizado para los grupos. Se excluyen los grupos archivados por defecto.
    """

    def get_super_queryset(self):
        """
        :returns:
            Retorna el get_queryset() del padre.
        """
        return super().get_queryset()

    def get_queryset(self):
        return super().get_queryset().annotate_estado().no_archivados()  # se excluyen los archivados

    def get(self, *args, **kwargs):
        return self.model._objects.get(*args, **kwargs)

    def archivados(self):
        """
        :returns:
            Un queryset con los grupos que se encuentran en estado archivado.
        """
        return self.model._objects.archivados()

    def raiz(self):
        """
        :returns:
            La raiz del arbol de grupos de una iglesia. Si no existe retorna ``None``.
        """

        nodos = self.model.get_root_nodes()
        if nodos:
            return nodos[0]

        return None

    def sin_confirmar_ofrenda_GAR(self):
        """
        :returns:
            Un queryset con los grupos que tienen pendientes por confirmar la ofrenda de reuniones GAR.
        """

        return self.filter(reuniones_gar__confirmacionEntregaOfrenda=False).distinct()

    def sin_confirmar_ofrenda_discipulado(self):
        """
        :returns:
            Un queryset con los grupos que tienen pendientes por confirmar la ofrenda de reuniones de discipulado.
        """

        return self.filter(reuniones_discipulado__confirmacionEntregaOfrenda=False).distinct()

    def hojas(self):
        """
        :returns:
            Un QuerySet con los grupos que no tienen descendientes (Incluye los grupos que solo tienen descendientes
            archivados).
        """

        return self.exclude(children_set__in=self.model.objects.all())

    def declarar_vacaciones(self, inicio, fin):
        """
        Ingresa los sobres de amistad de los grupos activos en el rango de fecha escogido con un estado
        de no realizo grupo.
        Los limites del rango son incluyentes.

        :param date inicio: Fecha inicial de la vaciones (inclusive).
        :param date fin: Fecha final de la vaciones (inclusive).
        """

        reuniones = []
        ReunionGAR = GrupoQuerySet.get_reunionGAR_model()
        fecha = inicio - datetime.timedelta(days=inicio.isoweekday() - 1)

        while fecha < fin:
            fin_semana = fecha + datetime.timedelta(days=7 - fecha.isoweekday())
            grupos_sin_reunion = self.model.objects.sin_reportar_reunion_GAR(fecha, fin_semana)

            for grupo in grupos_sin_reunion:
                reuniones.append(ReunionGAR.no_realizada(fecha=fecha, grupo=grupo, digitada_por_miembro=False))

            fecha = fecha + datetime.timedelta(days=8 - fecha.isoweekday())
        
        ReunionGAR.objects.bulk_create(reuniones)

    def disponibles_ver(self, miembro):
        """
        :returns: 
            Un queryset con los grupos que tiene disponible para ver el miembro ingresado. Si el miembro es
            un administrador todos los grupos se encuentran disponibles, sino solo puede ver los grupos de
            su subred.

        :param miembro:
            Miembro sobre el cual se van a filtrar los grupos.
        """

        if miembro.usuario.has_perm('miembros.es_administrador'):
            return self.all()
        
        if miembro.grupo_lidera:
            return miembro.grupo_lidera.grupos_red
        
        return self.none()

class GrupoManagerStandard(AL_NodeManager.from_queryset(GrupoQuerySet)):
    """Clase de manager para mantener el get_queryset original proveido por django."""
    
    def get_queryset(self):
        return super().get_queryset().annotate_estado()


class HistorialManager(models.Manager):
    """Manager para el modelo de historialestado."""

    def estado(self, estado):
        """
        :returns:
            Un queryset con los historiales filtrados por el estado.

        :param estado:
            El estado a partir del cual se filtraran los historiales.
        """
        return self.filter(estado=estado)


class PredicaManager(models.Manager):
    """Manager para el modelo de predicas."""

    def disponibles(self, miembro):
        """
        :returns: Un queryset con las predicas que tiene disponibles para dar el miembro ingresado.

        :param miembro:
            Miembro sobre el cual se van a buscar las predicas.
        
        .. note::

            Si el miembro es un administrador todas las predicas se encuentran disponibles, sino solo
            puede ver las predicas que ha dictado un pastor que se encuentre entre sus ancestros.
        """

        if miembro.usuario.has_perm('miembros.es_administrador'):
            return self.all()

        return self.filter(miembro__in=miembro.pastores())


class ReunionDiscipuladoManager(models.Manager):
    """Manager para el modelo de reuniones de discipulado."""
    
    def _asistencia_instance(self, miembro, reunion):
        return AsistenciaDiscipuladoModel()(miembro=miembro, reunion=reunion, asistencia=True)

    @transaction.atomic
    def reportar_reunion(self, grupo, predica, novedades, ofrenda, asistentes):
        """
        Guarda una reunión de discipulado con los datos ingresados. Si el grupo ya registro una reunión con la
        predica ingresada, la reunión se editara de lo contrario, se creara una reunión nueva.

        :param grupo: Grupo al cual se le va a crear o editar la reunión.
        :param predica: Predica sobre la cual se creara o editara la reunión.
        :param str novedades: Novedades de la reunión.
        :param int ofrenda: Ofrenda recogida en la reunión.
        :param list asistencia: Lista de miembros que asistieron a la reunión.

        :returns:
            Una tupla (reunion, created), donde reunión es la reunión creada o editada y created es un booleano
            que indica si la reunión fue creada.
        
        :raises MultipleObjectsReturned:
        """

        reunion, created = self.model.objects.update_or_create(
            grupo=grupo, predica=predica,
            defaults={'novedades': novedades, 'ofrenda': ofrenda}
        )

        if not created:
            reunion.asistencia.all().delete()

        asistencia = [self._asistencia_instance(miembro, reunion) for miembro in asistentes]
        AsistenciaDiscipuladoModel().objects.bulk_create(asistencia)

        return reunion, created


class ReunionGARQuerySet(models.QuerySet):
    """QuerySet personalizado para el modelo ReunionGAR."""

    def no_realizadas(self, fecha_inicial, fecha_final):
        """
        :returns:
            Un queryset con las reuniones reportadas como no realizadas en el rango de fechas indicado.
        
        :param fecha_inicial: Fecha inicial del rango (inclusive).
        :param fecha_final: Fecha final del rango (inclusive).
        """

        return self.filter(numeroLideresAsistentes=0, numeroTotalAsistentes=0, fecha__range=(fecha_inicial, fecha_final))


class ReunionGARManager(models.Manager.from_queryset(ReunionGARQuerySet)):
    """Manager personalizado para el modelo ReunionGAR."""

    pass