# Django
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect

# Apps
from miembros.models import TipoMiembro, CambioTipo, Miembro
from common.decorators import concurrente

# Python
import datetime


Miembro.algun_encuentro_como_coordinador = property(
    lambda x: [f for f in x.encuentros_coordinador.all() if f.no_empieza]
)

Miembro.algun_encuentro_como_tesorero = property(
    lambda x: [f for f in x.encuentros_tesorero.all() if f.no_empieza]
)


@concurrente
def crear_miembros_con_encontristas(encontristas):
    """
    Nota: Importante en esta vista al momento de ejecutar esta funcion, cuando se ejecuta
    la vista en html que reenderiza ve el encuentro como ACTIVO ya que el estado INACTIVO
    se pone luego de que acaba la funcion, hay que buscar la forma de avisarle al
    request.user que aun no se ha actualizado...
    """
    tesorero_group = Group.objects.get(name__iexact='tesorero')
    coordinador_group = Group.objects.get(name__iexact='coordinador')
    tipo_miembro = TipoMiembro.objects.get(nombre__iexact='miembro')
    for encontrista in encontristas:
        if encontrista.asistio:
            try:
                Miembro.objects.get(cedula=encontrista.identificacion)
            except Miembro.DoesNotExist:
                nuevo_miembro = Miembro()
                if encontrista.segundo_nombre:
                    nombre = encontrista.primer_nombre + ' ' + encontrista.segundo_nombre
                else:
                    nombre = encontrista.primer_nombre
                nuevo_miembro.nombre = nombre
                nuevo_miembro.primer_apellido = encontrista.primer_apellido
                if encontrista.segundo_apellido:
                    nuevo_miembro.segundo_apellido = encontrista.segundo_apellido
                nuevo_miembro.cedula = encontrista.identificacion
                nuevo_miembro.genero = encontrista.genero
                nuevo_miembro.email = encontrista.email
                nuevo_miembro.grupo = encontrista.grupo
                nuevo_miembro.save()
                cambio = CambioTipo()
                cambio.miembro = nuevo_miembro
                cambio.fecha = datetime.date.today()
                cambio.anteriorTipo = tipo_miembro
                cambio.nuevoTipo = tipo_miembro
                cambio.autorizacion = encontrista.encuentro.tesorero
                cambio.save()
    encuentro = encontrista.encuentro
    encuentro.estado = encuentro._meta.model.INACTIVO
    encuentro.save()
    # Si el tesorero tiene el grupo de 'Tesorero'
    if tesorero_group in encuentro.tesorero.usuario.groups.all():
        # # Si no hay encuentros que no se han cumplido
        # if not encuentro.tesorero.algun_encuentro_como_tesorero:
        # Si no hay algun encuentro que siga activo
        if not any(enc for enc in encuentro.tesorero.encuentros_tesorero.activos()):
            encuentro.tesorero.usuario.groups.remove(tesorero_group)
            encuentro.tesorero.usuario.save()
    if coordinador_group in encuentro.coordinador.usuario.groups.all():
        # if not encuentro.coordinador.algun_encuentro_como_coordinador:
        if not any(enc for enc in encuentro.coordinador.encuentros_coordinador.activos()):
            encuentro.coordinador.usuario.groups.remove(coordinador_group)
            encuentro.coordinador.usuario.save()


def avisar_tesorero_coordinador_encuentro(tesorero, coordinador):
    """
    Funcion para agregar los permisos de tesorero y coordinador de un encuentro
    a un miembro.
    """
    tesorero_group = Group.objects.get(name__iexact='tesorero')
    coordinador_group = Group.objects.get(name__iexact='coordinador')
    if tesorero_group not in tesorero.usuario.groups.all():
        tesorero.usuario.groups.add(tesorero_group)
        tesorero.usuario.save()
    if coordinador_group not in coordinador.usuario.groups.all():
        coordinador.usuario.groups.add(coordinador_group)
        coordinador.save()


def solo_encuentros_miembro(request, encuentro):
    """
    Funcion para verificar que los encuentros que pueda ver el miembro de la sesion,
    sean solo los encuentros en los cuales participa.

    :returns:
        HttpResponseRedirect si no puede ver el encuentro, de lo contrario retorna ``None``.
    """

    if not request.user.has_perm('miembros.es_administrador'):
        if request.user.has_perm('miembros.es_coordinador'):
            if encuentro not in Miembro.objects.get(usuario=request.user).encuentros_coordinador.all():
                return HttpResponseRedirect('/dont_have_permissions/')
        if request.user.has_perm('miembros.es_tesorero'):
            if encuentro not in Miembro.objects.get(usuario=request.user).encuentros_tesorero.all():
                return HttpResponseRedirect('/dont_have_permissions/')
    return None
