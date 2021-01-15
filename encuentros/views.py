# Django
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db.models import Count
from django.db import transaction
from django.urls import reverse

# Apps
from .models import Encuentro, Encontrista
from .forms import CrearEncuentroForm, NuevoEncontristaForm, EditarEncuentroForm
from .utils import crear_miembros_con_encontristas, avisar_tesorero_coordinador_encuentro, solo_encuentros_miembro
from grupos.models import Red, Grupo
from miembros.models import Miembro
from common.decorators import permisos_requeridos

# Python
import time


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def crear_encuentro(request):
    """Vista de Creacion de Encuentros."""

    accion = 'Crear'
    data = {'accion': accion}

    if request.method == 'POST':
        form = CrearEncuentroForm(data=request.POST)

        if form.is_valid():
            nuevo_encuentro = form.save()
            avisar_tesorero_coordinador_encuentro(nuevo_encuentro.tesorero, nuevo_encuentro.coordinador)
            messages.success(
                request,
                _(
                    '''
                    Se ha creado el encuentro correctamente.
                    <a alt="Listar Encuentros" class="{2}" href="{0}"> Volver a la lista de encuentros</a> o
                    <a alt="Agregar encontrista" class="{2}" href="{1}"> agregar encontristas a este encuentro</a>
                    '''.format(
                            reverse('encuentros:listar_encuentros'),
                            reverse('encuentros:agregar_encontrista', args=(nuevo_encuentro.id, )),
                            "alert-link"
                        )
                )
            )
            return redirect('encuentros:crear_encuetro')
        else:
            if 'grupos' in request.POST:
                grupos = Grupo.objects.filter(id__in=request.POST.getlist('grupos'))
                grupo_errors = []
                for grupo in grupos:
                    grupo_errors.append([grupo.id.__str__(), str(grupo)])
                data['grupo_errors'] = grupo_errors
            messages.error(request, 'Aún hay errores en el formulario, verificalo, y envialo nuevamente')

    else:
        form = CrearEncuentroForm()

    data['form'] = form

    return render(request, 'encuentros/crear_encuentro.html', data)


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def editar_encuentro(request, id_encuentro):
    """Vista de edicion de encuentros."""

    accion = 'Editar'
    encuentro = get_object_or_404(Encuentro, pk=id_encuentro)
    data = {'accion': accion, 'encuentro': encuentro}

    tesorero = Miembro.objects.get(id=encuentro.tesorero.id)
    coordinador = Miembro.objects.get(id=encuentro.coordinador.id)

    if request.method == 'POST':
        form = EditarEncuentroForm(data=request.POST, instance=encuentro)

        if form.is_valid():
            nuevo_tesorero = form.cleaned_data['tesorero']
            nuevo_coordinador = form.cleaned_data['coordinador']
            if coordinador != nuevo_coordinador:
                grupo_coordinador = Group.objects.get(name__iexact='coordinador')
                if grupo_coordinador in coordinador.usuario.groups.all() and \
                   not coordinador.encuentros_coordinador.activos().exclude(id__in=[encuentro.id]):
                    coordinador.usuario.groups.remove(grupo_coordinador)
                    coordinador.usuario.save()
            if tesorero != nuevo_tesorero:
                grupo_tesorero = Group.objects.get(name__iexact='tesorero')
                if grupo_tesorero in tesorero.usuario.groups.all() and \
                   not tesorero.encuentros_tesorero.activos().exclude(id__in=[encuentro.id]):
                    tesorero.usuario.groups.remove(grupo_tesorero)
                    tesorero.usuario.save()
            encuentro_editado = form.save()
            avisar_tesorero_coordinador_encuentro(encuentro_editado.tesorero, encuentro_editado.coordinador)
            messages.success(
                request,
                _(
                    '''
                    Se ha editado el encuentro correctamente.
                    <a alt="Listar Encuentros" class="{2}" href="{0}"> Volver a la lista de encuentros</a> o
                    <a alt="Agregar encontrista" class="{2}" href="{1}"> agregar encontristas a este encuentro</a>
                    '''.format(
                            reverse('encuentros:listar_encuentros'),
                            reverse('encuentros:agregar_encontrista', args=(encuentro_editado.id, )),
                            'alert-link'
                        )
                )
            )
            return redirect(reverse('encuentros:editar_encuentro', args=(id_encuentro, )))
        else:
            if 'grupos' in request.POST:
                grupos = Grupo.objects.filter(id__in=request.POST.getlist('grupos'))
                grupo_errors = []
                for grupo in grupos:
                    grupo_errors.append([grupo.id.__str__(), str(grupo)])
                data['grupo_errors'] = grupo_errors
            messages.error(request, 'Aún hay errores en el formulario, verificalo, y envialo nuevamente')

    else:
        form = EditarEncuentroForm(instance=encuentro)
    data['form'] = form

    return render(request, 'encuentros/crear_encuentro.html', data)


@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_tesorero', 'miembros.es_coordinador')
def listar_encuentros(request):
    """Lista de los Encuentros en estado activo y no completados."""

    miembro = Miembro.objects.get(usuario=request.user)
    if miembro.usuario.has_perm('miembros.es_administrador'):
        encuentros = Encuentro.objects.activos()
    elif miembro.usuario.has_perm('miembros.es_coordinador'):
        encuentros = miembro.encuentros_coordinador.activos()
    elif miembro.usuario.has_perm('miembros.es_tesorero'):
        encuentros = miembro.encuentros_tesorero.activos()
    
    encuentros = (
        encuentros
            .prefetch_related('grupos__lideres')
            .select_related('coordinador', 'tesorero')
            .annotate(num_encontristas=Count('encontrista'))
        )

    return render(request, 'encuentros/listar_encuentros.html', locals())


@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_tesorero')
def agregar_encontrista(request, id_encuentro):
    """Vista que permite agregar un encontrista a un encuentro especifico."""

    accion = 'Crear'
    encuentro = get_object_or_404(Encuentro, pk=id_encuentro)
    data = {'accion': accion, 'encuentro': encuentro}
    mismo = solo_encuentros_miembro(request, encuentro)
    if mismo is not None:
        return mismo

    if request.method == 'POST':
        form = NuevoEncontristaForm(data=request.POST, encuentro=encuentro)

        if form.is_valid():
            encontrista = form.save(commit=False)
            encontrista.encuentro = encuentro
            encontrista.save()
            messages.success(
                request,
                _(
                    '''Se ha creado el encontrista exitosamente,
                    <a href="{}" class="alert-link">Volver a la lista de encuentros</a>'''.format(
                        reverse('encuentros:listar_encuentros')
                    )
                )
            )
            return redirect(reverse('encuentros:agregar_encontrista', args=(id_encuentro, )))
        else:
            messages.error(
                request,
                _('Parece que aun hay errores con el formulario, verificalo y envialo nuevamente')
            )
    else:
        form = NuevoEncontristaForm(encuentro=encuentro)
    data['ecuentro'] = encuentro
    data['form'] = form

    return render(request, 'encuentros/agregar_encontrista.html', data)


@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_tesorero')
def editar_encontrista(request, id_encontrista):
    """Vista para editar los encontristas agregados."""

    accion = 'Editar'
    encontrista = get_object_or_404(Encontrista, pk=id_encontrista)
    encuentro = encontrista.encuentro
    data = {'accion': accion, 'encuentro': encuentro, 'encontrista': encontrista}
    mismo = solo_encuentros_miembro(request, encuentro)
    if mismo:
        return mismo

    if request.method == 'POST':
        form = NuevoEncontristaForm(data=request.POST, instance=encontrista)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                _(
                    '''Se ha editado el encontrista exitosamente,
                    <a href="{}" class="alert-link">Volver a la lista de encuentros</a>'''.format(
                        reverse('encuentros:listar_encuentros')
                    )
                )
            )
        else:
            messages.error(
                request,
                _('Parece que aun hay errores con el formulario, verificalo y envialo nuevamente')
            )
    else:
        form = NuevoEncontristaForm(instance=encontrista)
    data['form'] = form

    return render(request, 'encuentros/agregar_encontrista.html', data)


@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_tesorero')
def borrar_encontrista(request, id_encontrista):
    """
    Vista sencilla que toma el id de un encontrista y lo elimina luego
    redirecciona a la lista de encontristas del encuentro actual
    """
    encontrista = get_object_or_404(Encontrista, pk=id_encontrista)
    encuentro = Encuentro.objects.get(id=encontrista.encuentro.id)
    encontrista.delete()
    return HttpResponseRedirect('/encuentro/listar_encontristas/%s/' % str(encuentro.id))


@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_tesorero', 'miembros.es_coordinador')
def listar_encontristas(request, id_encuentro):
    """Vista que lista los encontristas actuales que tiene cada encuentro."""

    encuentro = get_object_or_404(Encuentro, pk=id_encuentro)
    mismo = solo_encuentros_miembro(request, encuentro)
    if mismo:
        return mismo

    encontristas = encuentro.encontrista_set.all()
    return render(request, 'encuentros/listar_encontristas.html', locals())


@transaction.atomic
@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_tesorero')
def asistencia_encuentro(request, id_encuentro):
    """
    Lista de asistencia final en la cual se marca cuales de los encontristas asistieron
    al encuentro para posteriormente crearlos como miembros
    """
    encuentro = get_object_or_404(Encuentro, pk=id_encuentro)
    mismo = solo_encuentros_miembro(request, encuentro)
    if mismo:
        return mismo

    encontristas = encuentro.encontrista_set.all()
    if len(encontristas) == 0:
        mensaje = 'Este encuentro no tiene encontristas'

    if request.method == 'POST':
        if 'seleccionados' in request.POST:
            if encuentro.acabado:
                seleccionados = Encontrista.objects.filter(id__in=request.POST.getlist('seleccionados'))
                encontristas = encuentro.encontrista_set.all()
                for encontrista in encontristas:
                    if encontrista in seleccionados:
                        encontrista.asistio = True
                    else:
                        encontrista.asistio = False
                    encontrista.save()
                if request.user.has_perm('miembros.es_administrador'):
                    time.sleep(1)
                    crear_miembros_con_encontristas(seleccionados)
                return HttpResponseRedirect('/encuentro/encuentros/')
            else:
                pass
        if 'aceptarAsistencia' in request.POST and 'seleccionados' not in request.POST:
            encontristas = encuentro.encontrista_set.all()
            for encontrista in encontristas:
                if encontrista.asistio:
                    encontrista.asistio = False
                encontrista.save()

    return render(request, 'encuentros/asistencia_encuentro.html', locals())
