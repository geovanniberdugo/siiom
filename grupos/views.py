# Python Packages
import logging
import datetime
import json
import copy

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.context import RequestContext
from django.utils.translation import ugettext as _

# Apps Imports
from django.views.generic import ListView
from .models import Grupo, ReunionGAR, ReunionDiscipulado, Red, AsistenciaDiscipulado, Predica, Enseñanza
from .utils import reunion_reportada, obtener_fechas_semana, reunion_reportada_discipulado_predica
from .forms import (
    FormularioEditarGrupo, FormularioReportarReunionGrupo,
    FormularioReportarReunionDiscipulado, FormularioSetGeoPosicionGrupo,
    FormularioCrearPredica, ArchivarGrupoForm, FormularioReportarReunionGrupoAdmin,
    FormularioReportesEnviados, FormularioEditarReunionGAR, GrupoRaizForm, NuevoGrupoForm,
    EditarGrupoForm, TrasladarGrupoForm, RedForm, TrasladarLideresForm, ReportarReunionDiscipuladoAdminForm
)
from miembros.decorators import user_is_cabeza_red, user_is_director_red
from miembros.forms import DesvincularLiderGrupoForm
from miembros.models import Miembro
from common.decorators import permisos_requeridos
from common.utils import eliminar

logger = logging.getLogger('siiom.{}'.format(__name__))


@login_required
@permission_required('miembros.es_lider', raise_exception=True)
def editar_horario_reunion_grupo(request, pk=None):
    g = True
    miembro = Miembro.objects.get(usuario=request.user)
    mismo = True
    draw_mapa = True
    form_desvincular = DesvincularLiderGrupoForm()
    # grupo.miembros.all()
    if pk:
        try:
            miembro = Miembro.objects.get(id=pk)
            mismo = False
            if Miembro.objects.get(usuario=request.user).id == miembro.id:
                mismo = True
        except Miembro.DoesNotExist:
            raise Http404

    grupo = miembro.grupo_lidera
    if mismo:
        puede_editar = True
    if grupo is None:
        puede_editar = False
        grupo = miembro.grupo
        no_lider = True
    if grupo is not None:
        miembros = grupo.miembrosGrupo()
        lideres = grupo.lideres.all()
    else:
        miembros = None
        lideres = None

    if request.method == 'POST':
        form = FormularioEditarGrupo(data=request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            ok = True
            ms = "El Grupo %s Fue Editado Correctamente" % grupo.nombre.upper()
            if mismo:
                ms = "Has Editado Tú Grupo Correctamente"
        else:
            ms = "Ocurrió un Error, Por Favor Verifica El Formulario"
    else:
        form = FormularioEditarGrupo(instance=grupo)

    return render(request, 'grupos/editar_grupo.html', locals())


@login_required
@permission_required('miembros.es_lider', raise_exception=True)
def reportar_reunion_grupo(request):
    """
    Vista para crear el reporte de grupos en el sistema.
    """

    miembro = Miembro.objects.get(usuario=request.user)
    grupo = miembro.grupo_lidera

    # se verifica que exista el grupo de el miembro en la sesion y que este, esté activo
    if grupo is not None and grupo.is_activo:
        if request.method == 'POST':
            form = FormularioReportarReunionGrupo(data=request.POST)
            if form.is_valid():
                reunion = form.save(commit=False)
                # se verifica que la reunion ya no haya sido reportada
                reportada = reunion_reportada(reunion.fecha, grupo)  # esta variable es enviada al template

                # si no esta reportada
                if not reportada:
                    # asigna el grupo y otros datos
                    reunion.grupo = grupo
                    reunion.digitada_por_miembro = True
                    # si no hicieron grupo, cambia la predica
                    if form.cleaned_data['no_realizo_grupo'] and not reunion.realizada:
                        reunion.predica = 'No se hizo Grupo'
                    # guarda el reporte en la base de datos
                    reunion.save()

                    messages.success(
                        request, _('Se ha Registrado el Reporte Existosamente, No olvides Llenar tu reporte Físico')
                    )
                    return redirect('grupos:reportar_reunion_grupo')
                else:
                    # envia mensaje de warning si ya fue reportada
                    messages.warning(
                        request,
                        _('''Parece que ya se ha reportado una reunion esta semana,\
                        Preguntale a tu Co-Líder o Administrador''')
                    )
            else:
                # si han ocurrido errores en el formulario, los envia
                logger.critical(form.errors)
                logger.critical(request.POST)
                messages.error(request, _('Ha ocurrido un error con el formulario, verifica los campos'))
        else:
            # carga el formulario en get
            form = FormularioReportarReunionGrupo()
    else:
        raise PermissionDenied('Grupo no se encuentra o está inactivo.')
    return render(request, 'grupos/reportar_reunion_grupo.html', locals())


@login_required
@user_is_director_red
def reportar_reunion_grupo_admin(request):
    if request.method == 'POST':
        form = FormularioReportarReunionGrupoAdmin(data=request.POST)
        if form.is_valid():
            reunion = form.save(commit=False)
            reportada = reunion_reportada(reunion.fecha, reunion.grupo)
            if not reportada:
                reunion.digitada_por_miembro = False
                reunion.confirmacionEntregaOfrenda = True
                if form.cleaned_data['no_realizo_grupo'] and not reunion.realizada:
                    reunion.predica = 'No se hizo Grupo'
                reunion.save()
                messages.success(
                    request,
                    _('Has reportado exitosamente la reunión de el grupo %s' % reunion.grupo.__str__())
                )
                return redirect('grupos:reportar_reunion_grupo_admin')
            else:
                messages.warning(
                    request,
                    _('Ya existe una reunión para esta semana')
                )
        else:
            messages.error(
                request,
                _('Ha ocurrido un error con el formulario, verifica los campos')
            )
    else:
        init = request.GET.get('grupo', None)
        initial = {'grupo': init}
        form = FormularioReportarReunionGrupoAdmin(initial=initial)
    return render(request, 'grupos/reportar_reunion_grupo_admin.html', locals())


@login_required
@permission_required('miembros.es_lider', raise_exception=True)
def reportar_reunion_discipulado(request):
    miembro = Miembro.objects.get(usuario=request.user)
    grupo = miembro.grupo_lidera
    if grupo:
        discipulos = grupo.discipulos

        if request.method == 'POST':
            asistentesId = request.POST.getlist('seleccionados')
            form = FormularioReportarReunionDiscipulado(miembro=miembro, data=request.POST)
            if form.is_valid():
                r = form.save(commit=False)
                if not reunion_reportada_discipulado_predica(grupo, r.predica):
                    r.grupo = grupo
                    r.save()
                    for m in discipulos:
                        AsistenciaDiscipulado.objects.create(miembro=m, reunion=r, asistencia=str(m.id) in asistentesId)
                    ok = True
                else:
                    ya_reportada = True
        else:
            form = FormularioReportarReunionDiscipulado(miembro=miembro)
    return render(request, 'grupos/reportar_reunion_discipulado.html', locals())


@login_required
@permission_required('miembros.es_pastor', raise_exception=True)
def listar_predicas(request):
    miembro = Miembro.objects.get(usuario=request.user)
    if request.method == "POST":
        if 'eliminar' in request.POST:
            okElim = eliminar(request, Predica, request.POST.getlist('seleccionados'))
            if okElim == 1:
                return HttpResponseRedirect('')
    predicas = list(Predica.objects.filter(miembro__id=miembro.id))

    if Group.objects.get(name__iexact='Administrador') in request.user.groups.all():
        predicas = list(Predica.objects.all())
    return render(request, 'grupos/listar_predicas.html', locals())


@login_required
@permission_required('miembros.es_pastor', raise_exception=True)
def crear_predica(request):
    miembro = Miembro.objects.get(usuario=request.user)
    accion = 'Crear'
    if request.method == "POST":
        form = FormularioCrearPredica(data=request.POST, miembro=miembro)
        if form.is_valid():
            form.save()
            ok = True
    else:
        form = FormularioCrearPredica(miembro=miembro)
    return render(request, 'grupos/crear_predica.html', locals())


@login_required
@permission_required('miembros.es_pastor', raise_exception=True)
def editar_predica(request, pk):
    accion = 'Editar'

    miembro = Miembro.objects.get(usuario=request.user)

    try:
        predica = Predica.objects.get(pk=pk)
    except Predica.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = FormularioCrearPredica(data=request.POST, instance=predica, miembro=miembro)
        if form.is_valid():
            ok = True
            form.save()
    else:
        form = FormularioCrearPredica(instance=predica, miembro=miembro)

    return render(request, "grupos/crear_predica.html", locals())


@login_required
@user_is_director_red
def ver_reportes_grupo(request):
    if request.method == 'POST' or (
        'post' in request.session and len(request.session['post']) > 1 and request.session.get('valid_post', False)
       ):
        if 'combo' in request.POST:
            value = request.POST['value']
            querys = Q(lideres__nombre__icontains=value) | Q(lideres__primer_apellido__icontains=value) | \
                Q(lideres__cedula__icontains=value)
            # Importante que se puedan escoger todos los grupos y no solo los 'Activos'
            busqueda = Grupo.objects.filter(querys)[:5]
            response = [{'pk': str(s.id), 'nombre': str(s)} for s in busqueda]
            return HttpResponse(json.dumps(response), content_type='aplicattion/json')

        data_from_session = request.session.get('post', None)
        valid_post = request.session.get('valid_post', False)

        if 'reportar' in request.POST:
            form_reporte = FormularioReportarReunionGrupoAdmin(data=request.POST)

            if form_reporte.is_valid():
                reunion = form_reporte.save(commit=False)
                reportada = reunion_reportada(reunion.fecha, reunion.grupo)

                if reportada:
                    messages.warning(request, "El Grupo ya cuenta con un reporte en esa semana")
                    form_reporte.add_error('fecha', 'Ya hay un reporte en esta semana')
                    click = True
                    if data_from_session is not None:
                        request.session['post'] = request.session['post']
                        # request.session['post'] = request.POST
                else:
                    reunion.digitada_por_miembro = False
                    reunion.confirmacionEntregaOfrenda = True
                    if form_reporte.cleaned_data['no_realizo_grupo'] and not reunion.realizada:
                        reunion.predica = 'No se hizo Grupo'
                    reunion.save()
                    messages.success(request, "Se Ha Reportado el Sobre Correctamente")
                    # request.session['post'] = request.POST
                    if data_from_session is not None:
                        request.session['post'] = request.session['post']
                        # request.session['post'] = request.POST
                        request.session['valid_post'] = True
                    return redirect('grupos:reportes_grupo')
            else:
                if data_from_session is not None:
                    request.session['post'] = request.session['post']
                    # request.session['post'] = request.POST
                if settings.DEBUG:
                    logger.info(form_reporte.errors)
                click = True

        else:
            form_reporte = FormularioReportarReunionGrupoAdmin()

        if 'confirmar' in request.POST:
            try:
                reunion = ReunionGAR.objects.get(id=request.POST['reporte'])
                reunion.confirmacionEntregaOfrenda = True
                reunion.save()
            except ReunionGAR.DoesNotExist:
                pass
            finally:
                if data_from_session is not None:
                    request.session['post'] = request.session['post']
                    # request.session['post'] = request.POST
                    request.session['valid_post'] = True
                return redirect('grupos:reportes_grupo')

        if data_from_session and 'fechai' not in request.POST:
            data = data_from_session
        else:
            data = request.POST

        form = FormularioReportesEnviados(data=data)

        if form.is_valid():
            grupo = form.cleaned_data['grupo']  # get_object_or_404(Grupo, id=request.POST['grupo'])
            fecha_inicial = form.cleaned_data['fechai']
            fecha_final = form.cleaned_data['fechaf']
            # se escribe la sesion con los datos de el POST
            request.session['post'] = {
                'grupo': form.cleaned_data['grupo'].id,
                'fechai': request.POST.get('fechai') or data_from_session['fechai'],
                'fechaf': request.POST.get('fechaf') or data_from_session['fechaf']
            }
            # request.session['valid_post'] = False
            request.session.pop('valid_post', None)
            fecha_final += datetime.timedelta(days=1)
            reuniones = grupo.reuniones_gar.filter(
                fecha__range=(fecha_inicial, fecha_final)
            ).order_by('-fecha')
            if len(reuniones) == 0:
                vacio = True

    else:
        form = FormularioReportesEnviados()
        form_reporte = FormularioReportarReunionGrupoAdmin()
        request.session.pop('valid_post', None)

    return render(request, "grupos/ver_reportes_grupo.html", locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def editar_runion_grupo(request, pk):
    """
    Funcion para editar una reunion de Grupo GAR
    """
    reunion = get_object_or_404(ReunionGAR, pk=pk)
    fecha_anterior = copy.deepcopy(reunion.fecha)

    # se sobreescriben las variables
    request.session['post'] = request.session.pop('post', None)

    if request.method == 'POST':
        form = FormularioEditarReunionGAR(data=request.POST, instance=reunion)

        if form.is_valid():
            reunion_formulario = form.save(commit=False)

            if reunion_formulario.fecha not in obtener_fechas_semana(fecha_anterior):
                reportada = reunion_reportada(reunion_formulario.fecha, reunion_formulario.grupo)

                if reportada:
                    messages.warning(
                        request,
                        _('Ya hay una reunion reportada en esta semana, verifica la fecha')
                    )
                    form.add_error('fecha', _('Fecha concuerda con otro reporte de reunion'))
                else:
                    # se envia que puede ir a la pagina de vista de reportes
                    request.session['valid_post'] = True
                    if form.cleaned_data['no_realizo_grupo'] and not reunion.realizada:
                        reunion.predica = 'No se hizo Grupo'
                    reunion_formulario.save()
                    messages.success(
                        request,
                        _('Se ha editado la reunion exitosamente. \
                        <a href="%(link)s" class="alert-link">Volver a reuniones.</a>' % {
                            'link': reverse('grupos:reportes_grupo')
                        })
                    )
            else:
                # se envia que puede ir a la pagina de vista de reportes
                request.session['valid_post'] = True
                if form.cleaned_data['no_realizo_grupo'] and not reunion.realizada:
                    reunion.predica = 'No se hizo Grupo'
                reunion_formulario.save()
                messages.success(
                    request,
                    _('Se ha editado la reunion exitosamente. \
                    <a href="%(link)s" class="alert-link">Volver a reuniones.</a>' % {
                        'link': reverse('grupos:reportes_grupo')
                    })
                )
        else:
            messages.error(request, _('Ha ocurrido un error al enviar el formulario, verifica los campos'))

    else:
        form = FormularioEditarReunionGAR(instance=reunion)

    return render(request, "grupos/editar_reunion_grupo.html", locals())


def set_position_grupo(request, id_grupo):
    """
    Vista para setear la posicion de un grupo.
    """

    grupo = get_object_or_404(Grupo, id=id_grupo)

    data = {}

    # latitud = request.GET.get('lat', None)
    # longitud = request.GET.get('long', None)
    form = FormularioSetGeoPosicionGrupo(data=request.GET, instance=grupo)

    if form.is_valid():
        form.save()
        data['code_response'] = 200
        data['message'] = 'Grupo %s editado correctamente' % grupo.get_nombre()
    else:
        data['error'] = form.errors
        data['code_response'] = 400

    return HttpResponse(json.dumps(data), content_type='application/json')

# --------------------------------

@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_lider')
def organigrama_grupos(request):
    """
    Muestra el organigrama de la red de grupos de la iglesia. Para un adminsitrador muestra toda la red, mientras que
    para un líder muestra su red.
    """

    usuario = request.user
    if usuario.has_perm('miembros.es_administrador'):
        arbol = Grupo.obtener_arbol()
    else:
        miembro = get_object_or_404(Miembro, usuario=usuario)
        arbol = Grupo.obtener_arbol(miembro.grupo_lidera)

    return render(request, 'grupos/organigrama_grupos.html', {'arbol': arbol})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def grupo_raiz(request):
    """
    Permite a un administrador crear el grupo raiz de la iglesia si aún no ha sido creado. Si ya existe lo permite
    editar.
    """

    raiz = Grupo.objects.raiz()  # Si no existe raiz devuelve None
    if request.method == 'POST':
        form = GrupoRaizForm(instance=raiz, data=request.POST)
        if form.is_valid():
            if form.save():
                messages.success(request, _('El grupo fue guardado correctamente.'))
                return redirect('grupos:raiz')
    else:
        form = GrupoRaizForm(instance=raiz)

    return render(request, 'grupos/grupo_raiz.html', {'form': form})


@login_required
@permisos_requeridos('miembros.buscar_todos', 'miembros.es_lider')
def detalle_grupo(request, pk):
    """
    Permite ver el detalle de un grupo. Si el usuario no puede buscar todos solo podrá ver sus descendientes.
    """

    grupo = get_object_or_404(Grupo, pk=pk)
    if not request.user.has_perm('miembros.buscar_todos'):
        grupo_lidera = Miembro.objects.get(usuario=request.user).grupo_lidera
        if grupo_lidera:
            if not grupo.is_descendant_of(grupo_lidera) and grupo_lidera != grupo:
                raise PermissionDenied
        else:
            raise PermissionDenied

    return render(request, 'grupos/detalle_grupo.html', {'grupo': grupo})


@login_required
@user_is_cabeza_red
def crear_grupo(request, pk):
    """
    Permite a un administrador o un cabeza de red crear un grupo de una iglesia en la red ingresada.
    """

    red = get_object_or_404(Red, pk=pk)

    if not request.user.has_perm('miembros.es_administrador') and \
       request.miembro.es_cabeza_red and str(request.miembro.grupo.red_id) != str(pk):
        # cuando no está visitando la red correspondiente al miembro, se redirecciona hasta la red
        return redirect('grupos:nuevo', request.miembro.grupo.red_id)

    if request.method == 'POST':
        form = NuevoGrupoForm(red=red, data=request.POST)
        if form.is_valid():
            if form.save():
                messages.success(request, _('El grupo se ha creado correctamente.'))
                return redirect('grupos:listar', pk)
    else:
        form = NuevoGrupoForm(red=red)

    # se agrega la red
    data = {'form': form, 'red_id': pk, 'VERBO': _('Crear')}

    return render(request, 'grupos/grupo_form.html', data)


@login_required
@user_is_cabeza_red
def editar_grupo(request, pk):
    """
    Permite a un administrador o cabeza de red editar un grupo de una iglesia.
    """

    grupo = get_object_or_404(Grupo, pk=pk)
    if request.method == 'POST':
        form = EditarGrupoForm(instance=grupo, data=request.POST)
        if form.is_valid():
            if form.save():
                messages.success(request, _('El grupo se ha editado correctamente.'))
                return redirect('grupos:listar', grupo.red.id)
    else:
        form = EditarGrupoForm(instance=grupo)

    # se agregan los datos como red y grupo
    data = {'form': form, 'red_id': grupo.red_id, 'grupo_id': grupo.id, 'VERBO': _('Editar')}

    return render(request, 'grupos/grupo_form.html', data)


@login_required
@user_is_cabeza_red
def listar_grupos(request, pk):
    """
    Permite a un administrador o cabeza de red listar los grupos de la red escogida.
    """

    red = get_object_or_404(Red, pk=pk)

    if not request.user.has_perm('miembros.es_administrador') and \
       str(request.miembro.grupo.red_id) != str(pk):
        return redirect('grupos:listar', request.miembro.grupo.red_id)

    if not request.user.has_perm('miembros.es_administrador'):
        grupos = request.miembro.grupo_lidera.grupos_red
    else:
        grupos = Grupo.objects.prefetch_related('lideres').red(red)
    
    grupos = grupos.select_related('barrio')
    return render(request, 'grupos/lista_grupos.html', {'red': red, 'grupos': grupos})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def trasladar(request, pk):
    """
    Permite a un administrador trasladar un grupo a una nueva posición en el organigrama de grupos.
    """

    grupo = get_object_or_404(Grupo, pk=pk)
    if request.method == 'POST':
        form = TrasladarGrupoForm(grupo, data=request.POST)
        if form.is_valid():
            form.trasladar()
            return redirect('grupos:trasladar', pk)
    else:
        form = TrasladarGrupoForm(grupo)

    return render(request, 'grupos/trasladar.html', {'grupo': grupo, 'form': form})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def sin_confirmar_ofrenda_GAR(request):
    """
    Permite a un administrador listar los grupos que faltan por confirmar la ofrenda de las reuniones GAR.
    """

    grupos = Grupo.objects.sin_confirmar_ofrenda_GAR().prefetch_related('lideres')
    return render(request, 'grupos/sin_confirmar_ofrenda_GAR.html', {'grupos': grupos})


@login_required
@permission_required('grupos.puede_confirmar_ofrenda_GAR', raise_exception=True)
def confirmar_ofrenda_GAR(request, pk):
    """
    Permite a un administrador o receptor confirmar la ofrenda de la reunión GAR del grupo especificado.
    """

    grupo = get_object_or_404(Grupo, pk=pk)

    if request.method == 'POST':
        reuniones_confirmar = request.POST.getlist('seleccionados')
        grupo.confirmar_ofrenda_reuniones_GAR(reuniones_confirmar)
        messages.success(request, _('Se han confirmado las reuniones escogidas.'))
        return redirect('grupos:confirmar_ofrenda_GAR', pk)
    else:
        reuniones = grupo.reuniones_GAR_sin_ofrenda_confirmada

    return render(request, 'grupos/confirmar_ofrenda_GAR.html', {'reuniones': reuniones})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def sin_confirmar_ofrenda_discipulado(request):
    """
    Permite a un administrador listar los grupos que faltan por confirmar la ofrenda de las reuniones de discipulado.
    """

    grupos = Grupo.objects.sin_confirmar_ofrenda_discipulado().prefetch_related('lideres')
    return render(request, 'grupos/sin_confirmar_ofrenda_discipulado.html', {'grupos': grupos})


@login_required
@permission_required('grupos.puede_confirmar_ofrenda_discipulado', raise_exception=True)
def confirmar_ofrenda_discipulado(request, pk):
    """
    Permite a un administrador o receptor confirmar la ofrenda de la reunión de discipulado del grupo especificado.
    """

    grupo = get_object_or_404(Grupo, pk=pk)

    if request.method == 'POST':
        reuniones_confirmar = request.POST.getlist('seleccionados')
        grupo.confirmar_ofrenda_reuniones_discipulado(reuniones_confirmar)
        messages.success(request, _('Se han confirmado las reuniones escogidas.'))
        return redirect('grupos:confirmar_ofrenda_discipulado', pk)
    else:
        reuniones = grupo.reuniones_discipulado_sin_ofrenda_confirmada

    return render(request, 'grupos/confirmar_ofrenda_discipulado.html', {'reuniones': reuniones})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def crear_red(request):
    """
    Permite a un administrador crear una red de su iglesia.
    """

    if request.method == 'POST':
        form = RedForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('La red se ha creado correctamente.'))
            return redirect('grupos:red_nueva')
    else:
        form = RedForm()

    return render(request, 'grupos/red_form.html', {'form': form, 'VERBO': _('Crear')})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def editar_red(request, pk):
    """
    Permite a un administrador editar una red de su iglesia.
    """

    red = get_object_or_404(Red, pk=pk)
    if request.method == 'POST':
        form = RedForm(data=request.POST, instance=red)
        if form.is_valid():
            form.save()
            messages.success(request, _('La red fue editada correctamente.'))
            return redirect('grupos:red_editar', pk=pk)
    else:
        form = RedForm(instance=red)

    return render(request, 'grupos/red_form.html', {'form': form, 'VERBO': _('Editar')})


@login_required
@user_is_cabeza_red
def listar_redes(request):
    """
    Permite a un administrador listar redes de su iglesia.
    """

    redes = Red.objects.all()
    return render(request, 'grupos/lista_redes.html', {'redes': redes})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def trasladar_lideres(request):
    """
    Permite a un administrador trasladar lideres de un grupo a otro en una iglesia.
    """

    if request.method == 'POST':
        form = TrasladarLideresForm(data=request.POST)
        if form.is_valid():
            form.trasladar()
            messages.success(request, _('Los lideres se han trasladado correctamente.'))
            return redirect('grupos:organigrama')
    else:
        form = TrasladarLideresForm()

    return render(request, 'grupos/trasladar_lideres.html', {'form': form})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def archivar_grupo(request):
    """
    Permite a un administrador archivar un grupo.
    """

    grupo = request.GET.get('grupo', None) or None

    if request.method == 'POST':
        form = ArchivarGrupoForm(data=request.POST)

        if form.is_valid():
            form.archiva_grupo()
            messages.success(request, _('Grupo eliminado correctamente.'))
            return redirect('grupos:organigrama')
        else:
            try:
                form.nombre_grupo = str(form.cleaned_data['grupo'])
            except:
                form.nombre_grupo = _('escogido')
            logger.critical(form.errors)

    else:
        form = ArchivarGrupoForm(initial={'grupo': grupo})

    return render(request, 'grupos/archivar_grupos.html', {'form': form})


@login_required
@user_is_director_red
def admin_reportar_reunion_discipulado(request):
    """Permite a un administrador o director de red reportar reunion de discipulado de un grupo."""

    if request.method == 'POST':
        form = ReportarReunionDiscipuladoAdminForm(request.miembro, data=request.POST)

        if form.is_valid():
            reunion, created = form.save()
            if reunion:
                accion = 'creado' if created else 'editado'
                messages.success(request, _('Se ha {0} la reunion satisfactoriamente.'.format(accion)))
                return redirect('grupos:admin_reportar_reunion_discipulado')
    else:
        form = ReportarReunionDiscipuladoAdminForm(request.miembro)

    return render(request, 'grupos/reportar_reunion_discipulado_admin.html', {'form': form})

class EnseñanzasListView(LoginRequiredMixin, PermissionRequiredMixin ,ListView):
    model = Enseñanza
    queryset = Enseñanza.objects.order_by('fecha_inicial')
    permission_required = 'grupos.can_see_enseñanzas'