# Third Apps
import waffle

# Python Packages
import datetime
import json
import os

# Django Imports
from datetime import date
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.db import transaction
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect

# Apps Imports
from .forms import *
from .forms import TrasladarMiembroForm, NuevoMiembroForm, DesvincularLiderGrupoForm
from .decorators import user_is_miembro_or_empleado
from .models import Miembro, CambioTipo, TipoMiembro, Zona, Barrio
from .utils import divorciar
from grupos.forms import FormularioEditarDiscipulado
from grupos.models import Grupo, Red
from common.decorators import permisos_requeridos
from common.utils import eliminar
from compras.models import Requisicion, Parametros, DetalleRequisicion


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    """
    Vista para el logeo de usuarios al sistema, permite el login de usuarios
    miembros, y de usuarios empleados, luego de autenticarlos, retorna a una
    vista de acuerdo a los permisos que el usuario tenga.
    """

    siguiente = request.session.get('next', '')

    if request.user.is_authenticated:
        if request.user.has_perm("miembros.es_administrador"):
            return redirect('administracion')
        return redirect('miembros:miembro_inicio')

    if request.method == 'POST':
        form = LoginForm(request=request, data=request.POST)

        if form.is_valid():
            auth.login(request, form.get_user())
            if form.is_safe_url(siguiente):
                next = siguiente
            else:
                next = form.get_next()
            return HttpResponseRedirect(next)  # No usar redirect
    else:
        form = LoginForm()

    return render(request, 'miembros/login.html', {'form': form})


@csrf_protect
@never_cache
def logout(request):
    """Vista para hacer el logout del usuario que se encuentra actualmente logeado."""
    auth.logout(request)
    return redirect('inicio')


@login_required
@user_is_miembro_or_empleado
def miembro_inicio(request):
    miembro = None
    empleado = None
    try:
        miembro = Miembro.objects.get(usuario=request.user)
    except Miembro.DoesNotExist:
        empleado = request.user.empleado

    if request.user.has_perm("miembros.es_administrador"):
        return HttpResponseRedirect("/administracion/")

    if miembro:
        grupo = miembro.grupo_lidera
        if grupo:
            miembrosGrupo = grupo.miembros.all()
            tipo = TipoMiembro.objects.get(nombre__iexact='visita')
            visitantes = []
            for mg in miembrosGrupo:
                ct = CambioTipo.objects.filter(miembro=mg).order_by('id')
                if ct.exists():
                    ct = list(ct).pop()
                    if ct.nuevoTipo == tipo and ct.anteriorTipo == tipo:
                        visitantes.append(ct.miembro)
        else:
            visitantes = []

        discipulos = list()
        inactivos = list()
        grupos = list()

        def lid_gru(miem):
            visitas = CambioTipo.objects.filter(nuevoTipo__nombre__iexact='lider').values('miembro')
            grupo = miem.grupo_lidera
            if grupo:
                return grupo.miembros.filter(id__in=visitas)
            else:
                return []

        k = Grupo.get_tree(grupo)

        discipulos = Miembro.objects.lideres().filter(grupo_lidera__in=k)
        totalLideres = len(discipulos)
        totalGrupos = len(k)  # len(grupos)
        lideresGrupo = len(lid_gru(miembro)) - 1
        if lideresGrupo == -1:
            lideresGrupo = 0
    if empleado:
        if waffle.switch_is_active('compras'):
            if empleado.requisicion_set.filter(estado=Requisicion.PROCESO).exists():
                mis_requisiciones_activas = empleado.requisicion_set.filter(estado=Requisicion.PROCESO)

            if empleado.is_compras:
                # se sacan las ulimas requisiciones
                ultimas_requisiciones = Requisicion.objects.ingresadas_compras()
                hoy = timezone.now().date()

                # se sacan las requisiciones ingresadas en el ultimo mes
                requisiciones_ingresadas_mes = Requisicion.objects.ultimo_mes().count()

                # se sacan las requisiciones que fueron atendidas por el empleado
                if requisiciones_ingresadas_mes > 0:
                    porcentage_atencion_mes = (Requisicion.objects.ultimo_mes(
                        historial__empleado=empleado
                    ).count() * 100) / requisiciones_ingresadas_mes
                else:
                    porcentage_atencion_mes = 0

                # Requisiciones en compras
                requisiciones_empleado = ultimas_requisiciones.count()

                try:
                    # porcentaje total de requisiciones en comrpas
                    porcetaje_total_en_compras = (ultimas_requisiciones.count() * 100) / Requisicion.objects.filter(
                        estado=Requisicion.PROCESO
                    ).count()
                except ZeroDivisionError:
                    porcetaje_total_en_compras = 0
            if empleado.is_jefe_administrativo:
                dias = Parametros.objects.dias()
                hoy = timezone.now().date()

                # las terminadas en este mes
                requisiciones_terminadas = Requisicion.objects.finalizadas_mes().count()

                # que han ingresado a trazabilidad
                requisiciones_faltantes_aprobar_trazabilidad = Requisicion.objects.ingresadas_administrativo().count()

                requisiciones_recientes = Requisicion.objects.ingresadas_administrativo()

                # que han ingresado a departamento
                requisiciones_faltantes_aprobar_departamento = Requisicion.objects.filter(
                    historial=None, empleado__areas__departamento__nombre__icontains='administra'
                ).count()

                requisiciones_mora = len([
                    requisicion for requisicion in Requisicion.objects.ingresadas_compras().prefetch_related(
                        'historial_set'
                    )
                    if requisicion.historial_set.last().fecha.date() + datetime.timedelta(days=dias) <= hoy
                ])

                if Requisicion.objects.filter(estado=Requisicion.PROCESO).exists():
                    porcetaje_total_en_compras = (requisiciones_faltantes_aprobar_trazabilidad * 100) /\
                        Requisicion.objects.filter(
                            estado=Requisicion.PROCESO
                        ).count()
                else:
                    porcetaje_total_en_compras = 0

            if empleado.is_jefe_financiero:
                hoy = timezone.now().date()
                requisiciones_faltantes_aprobar_departamento = Requisicion.objects.filter(
                    historial=None, empleado__areas__departamento__nombre__icontains='financi'
                ).count()

                requisiciones_faltantes_aprobar_trazabilidad = len(Requisicion.objects.ingresadas_financiero())

                requisiciones_espera = [requisicion for requisicion in Requisicion.objects.filter(
                    estado=Requisicion.PROCESO
                ) if requisicion.get_rastreo() == Requisicion.DATA_SET['espera_presupuesto']]

                salida_credito = DetalleRequisicion.objects.salida_credito_mes()['total_aprobado__sum'] or 0

                salida_efectivo = DetalleRequisicion.objects.salida_efectivo_mes()['total_aprobado__sum'] or 0

    return render(request, "miembros/miembro.html", locals())


@login_required
@permisos_requeridos(
    'miembros.es_administrador', 'miembros.es_lider', 'miembros.es_agente',
    'grupos.puede_confirmar_ofrenda_discipulado', 'puede_confirmar_ofrenda_GAR'
)
def editar_perfil_miembro(request, pk=None):
    p = True
    miembro = Miembro.objects.get(usuario=request.user)
    casado = False
    mismo = True
    form_desvincular = DesvincularLiderGrupoForm()
    if pk:
        try:
            miembro = Miembro.objects.get(id=pk)
            mismo = False
            if Miembro.objects.get(usuario=request.user).id == miembro.id:
                mismo = True
        except Miembro.DoesNotExist:
            raise Http404

    if miembro.estado_civil == 'C' and miembro.conyugue is not None:
        casado = True

    foto = False
    if miembro.foto_perfil:
        rut_perfil = miembro.foto_perfil.path
        foto = True
    if request.method == 'POST':

        if 'file' in request.POST:
            dat = {}
            f = FormularioFotoPerfil(data=request.POST, files=request.FILES, instance=miembro)
            if f.is_valid():
                if miembro.foto_perfil != '' or miembro.foto_perfil is not None:
                    if foto:
                        r = settings.MEDIA_ROOT + "/media/profile_pictures/user_%s/" % miembro.id
                        if os.path.exists(rut_perfil) and os.path.isfile(rut_perfil):
                            if settings.DEBUG:
                                print("Se borra el archivo anterior")
                            os.remove(rut_perfil)
                f.save()
                ok = True
                dat['ms'] = "Foto editada Correctamente"
                dat['status'] = 'success'
                dat['ruta'] = str(miembro.foto_perfil.url)
                return HttpResponse(json.dumps(dat), content_type="application/json")
            else:
                dat['ms'] = "Foto demasiado Grande Tamaño maximo aceptado: 2000x2000"
                dat['status'] = 'danger'
                if foto:
                    dat['ruta'] = str(miembro.foto_perfil.url)
                else:
                    dat['ruta'] = settings.STATIC_URL + 'Imagenes/profile-none.jpg'
                return HttpResponse(json.dumps(dat), content_type="application/json")

        if 'contrasena' in request.POST:
            return redirect('miembros:cambiar_contrasena')

        elif 'aceptar' in request.POST:
            if request.user.has_perm('miembros.es_administrador'):
                form = FormularioAdminAgregarMiembro(data=request.POST, files=request.FILES, instance=miembro)
                admin = True
            else:
                form = FormularioLiderAgregarMiembro(data=request.POST, files=request.FILES, instance=miembro)
            if form.is_valid():
                miembroEditado = form.save()
                if miembroEditado.usuario is not None:
                    miembroEditado.usuario.username = '{}'.format(miembroEditado.cedula)
                    miembroEditado.usuario.email = miembroEditado.email
                    miembroEditado.usuario.save()
                    miembroEditado.save()
                if miembroEditado.conyugue is not None:
                    conyugue = Miembro.objects.get(id=miembroEditado.conyugue.id)
                    conyugue.conyugue = miembroEditado
                    conyugue.estado_civil = 'C'
                    conyugue.save()
                    miembroEditado.estado_civil = 'C'
                    miembroEditado.save()
                if casado and miembroEditado.estado_civil != 'C':
                    conyugue = Miembro.objects.get(conyugue=miembroEditado)
                    divorciar(miembroEditado, conyugue, miembroEditado.estado_civil)

                ok = True
                ms = "Miembro Editado Correctamente"
                if mismo:
                    ms = "Te has Editado Correctamente"
            else:
                ms = "Ha Ocurrido un Error, Verifica el Formulario"
        else:
            return redirect('miembros:miembro_inicio')
    else:
        if request.user.has_perm('miembros.es_administrador'):
            form = FormularioAdminAgregarMiembro(instance=miembro, g=miembro.genero)
            admin = True
        else:
            form = FormularioLiderAgregarMiembro(instance=miembro, g=miembro.genero, c=miembro.conyugue)
    return render(request, "miembros/editar_perfil.html", locals())


@login_required
@permisos_requeridos('miembros.es_administrador', 'miembros.es_agente')
def asignar_grupo(request, id):
    try:
        miembroEditar = Miembro.objects.get(id=id)
    except:
        raise Http404
    miembro = Miembro.objects.get(usuario=request.user)

    form = FormularioAsignarGrupo(instance=miembroEditar)
    if request.method == 'POST':
        form = FormularioAsignarGrupo(data=request.POST, instance=miembroEditar)
        if form.is_valid():
            nuevoMiembro = form.save(commit=False)
            if nuevoMiembro.grupo is not None or nuevoMiembro.grupo != '':
                mailLideres = nuevoMiembro.grupo.lideres.values('email')
                receptores = ["%s" % (k['email']) for k in mailLideres]
                camposMail = ['Nuevo Miembro', "Lider de la iglesia %s,\n\n\
                        Se ha agregado un nuevo miembro a su G.A.R, por favor \
                        ingrese al sistema para registrar la llamada:\n\
                        http://iglesia.webfactional.com/iniciar_sesion\n\n\
                        Cordialmente,\n\
                        Admin" % Site.objects.get_current().name, receptores]
            nuevoMiembro.save()
            ok = True
    return render(request, "miembros/asignar_grupo.html", locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def crear_zona(request):
    accion = 'Crear'
    miembro = Miembro.objects.get(usuario=request.user)
    if request.method == "POST":
        form = FormularioCrearZona(data=request.POST)
        if form.is_valid():
            nuevaZona = form.save()
            ok = True
    else:
        form = FormularioCrearZona()
    return render(request, 'miembros/crear_zona.html', locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def editar_zona(request, pk):
    accion = 'Editar'
    miembro = Miembro.objects.get(usuario=request.user)

    try:
        zona = Zona.objects.get(pk=pk)
    except Zona.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = FormularioCrearZona(request.POST or None, instance=zona)

        if form.is_valid():
            ok = True
            form.save()

    else:
        form = FormularioCrearZona(instance=zona)

    return render(request, "miembros/crear_zona.html", locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def listar_zonas(request):
    miembro = Miembro.objects.get(usuario=request.user)
    if request.method == "POST":

        if 'eliminar' in request.POST:
            okElim = eliminar(request, Zona, request.POST.getlist('seleccionados'))
            if okElim == 1:
                messages.success(request, "Se eliminaron las zonas seleccionadas")
                return HttpResponseRedirect('')
    zonas = list(Zona.objects.all())
    return render(request, 'miembros/listar_zonas.html', locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def barrios_zona(request, id):
    """
    Esta función permite listar los barrios que están registrados en determinada
    zona.
    """

    zona = get_object_or_404(Zona, id=id)

    if request.method == "POST":
        if 'eliminar' in request.POST:
            okElim = eliminar(request, Barrio, request.POST.getlist('seleccionados'))

    barrios = zona.barrio_set.all()
    return render(request, 'miembros/barrios.html', {'barrios': barrios, 'zona': zona})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def crear_barrio(request, id):
    """
        Esta función permite crear barrios de una zona en la base de datos
    """
    accion = 'Crear'
    # miembro = Miembro.objects.get(usuario=request.user)
    try:
        zona = Zona.objects.get(id=id)
    except:
        raise Http404
    if request.method == "POST":
        form = FormularioCrearBarrio(data=request.POST)
        if form.is_valid():
            nuevoBarrio = Barrio.objects.create(zona=zona, nombre='')
            nuevoBarrio.save()
            form = FormularioCrearBarrio(data=request.POST, instance=nuevoBarrio)
            nuevoBarrio = form.save()
            ok = True
    else:
        form = FormularioCrearBarrio()
    return render(request, 'miembros/crear_barrio.html', locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def editar_barrio(request, id, pk):
    accion = 'Editar'
    # miembro = Miembro.objects.get(usuario=request.user)
    zona = get_object_or_404(Zona, id=id)
    barrio = get_object_or_404(Barrio, pk=pk)

    if request.method == "POST":
        form = FormularioCrearBarrio(request.POST, instance=barrio)
        if form.is_valid():
            form.save()
            ok = True
    else:
        form = FormularioCrearBarrio(instance=barrio)

    return render(request, "miembros/crear_barrio.html", locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def crear_tipo_miembro(request):
    accion = 'Crear'
    miembro = Miembro.objects.get(usuario=request.user)
    if request.method == "POST":
        form = FormularioCrearTipoMiembro(data=request.POST)
        if form.is_valid():
            nuevoTipoMiembro = form.save()
            ok = True
    else:
        form = FormularioCrearTipoMiembro()
    return render(request, 'miembros/crear_tipo_miembro.html', locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def listar_tipos_miembro(request):
    miembro = Miembro.objects.get(usuario=request.user)
    if request.method == "POST":
        if 'editar' in request.POST:
            request.session['seleccionados'] = request.POST.getlist('seleccionados')
            return HttpResponseRedirect('/miembro/editar_tipo_miembro/')
        if 'eliminar' in request.POST:
            okElim = eliminar(request, TipoMiembro, request.POST.getlist('seleccionados'))
    tipos = list(TipoMiembro.objects.all().order_by('nombre'))
    return render(request, 'miembros/listar_tipo_miembro.html', locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def editar_tipo_miembro(request, pk):
    accion = 'Editar'

    try:
        tipo = TipoMiembro.objects.get(pk=pk)
    except TipoMiembro.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = FormularioCrearTipoMiembro(request.POST or None, instance=tipo)

        if form.is_valid():
            ok = True
            form.save()

    else:
        form = FormularioCrearTipoMiembro(instance=tipo)

    return render(request, "miembros/crear_tipo_miembro.html", locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def crear_usuario_miembro(request, id):
    try:
        miembroCambio = Miembro.objects.get(id=id)
    except:
        raise Http404

    if miembroCambio.usuario:
        return HttpResponseRedirect("/dont_have_permissions/")

    sesion = True

    if 'tipo' not in request.session:
        sesion = False

    if request.method == "POST":
        form = FormularioAsignarUsuario(data=request.POST)
        if form.is_valid() and form.cleaned_data['contrasena'] == form.cleaned_data['contrasenaVerificacion']:
            nuevoUsuario = User()
            if form.cleaned_data['email'] != miembroCambio.email:
                miembroCambio.correo = form.cleaned_data['email']
            nuevoUsuario.username = form.cleaned_data['email']
            nuevoUsuario.email = form.cleaned_data['email']
            nuevoUsuario.set_password(form.cleaned_data['contrasena'])
            nuevoUsuario.save()
            miembroCambio.usuario = nuevoUsuario
            miembroCambio.save()
            if sesion:
                if request.session['tipo'].lower() == "lider":
                    miembroCambio.usuario.groups.add(Group.objects.get(name__iexact='Lider'))
                if request.session['tipo'].lower() == "agente":
                    miembroCambio.usuario.groups.add(Group.objects.get(name__iexact='Agente'))
                if request.session['tipo'].lower() == "maestro":
                    miembroCambio.usuario.groups.add(Group.objects.get(name__iexact='Maestro'))
                if request.session['tipo'].lower() == "receptor":
                    miembroCambio.usuario.groups.add(Group.objects.get(name__iexact='Receptor'))
                if request.session['tipo'].lower() == "administrador":
                    miembroCambio.usuario.groups.add(Group.objects.get(name__iexact='Administrador'))
            return redirect(reverse('miembros:editar_perfil', args=(miembroCambio.id)))
    else:
        form = FormularioAsignarUsuario()
    form.email = miembroCambio.email
    return render(request, 'miembros/asignar_usuario.html', locals())


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def eliminar_cambio_tipo_miembro(request, id):
    """
    El cambio que se va a eliminar se guarda en la var cambio y si esta es un
    tipo de cambio aceptable, es eliminado. En caso de que el usuario no cuente
    con ningún otro tipo de miembro luego de eliminar el cambio. El usuario será
    eliminado y no podrá loguearse en el sistema.
    """

    miembro = Miembro.objects.get(usuario=request.user)
    try:
        cambio = CambioTipo.objects.get(id=id)
    except:
        raise Http404

    if cambio.nuevoTipo.nombre.lower() == "lider":
        cambio.miembro.usuario.groups.remove(Group.objects.get(name__iexact='Lider'))
    elif cambio.nuevoTipo.nombre.lower() == "agente":
        cambio.miembro.usuario.groups.remove(Group.objects.get(name__iexact='Agente'))
    elif cambio.nuevoTipo.nombre.lower() == "maestro":
        cambio.miembro.usuario.groups.remove(Group.objects.get(name__iexact='Maestro'))
    elif cambio.nuevoTipo.nombre.lower() == "receptor":
        cambio.miembro.usuario.groups.remove(Group.objects.get(name__iexact='Receptor'))
    elif cambio.nuevoTipo.nombre.lower() == "administrador":
        cambio.miembro.usuario.groups.remove(Group.objects.get(name__iexact='Administrador'))
    elif cambio.nuevoTipo.nombre.lower() == "pastor":
        cambio.miembro.usuario.groups.remove(Group.objects.get(name__iexact='Pastor'))

    try:
        if cambio.miembro.usuario.groups.count() == 0:
            if hasattr(cambio.miembro.usuario, 'empleado'):
                if not cambio.miembro.usuario.empleado:
                    cambio.miembro.usuario.delete()
            else:
                cambio.miembro.usuario.delete()
            cambio.miembro.usuario = None
            cambio.miembro.save()
    except:
        pass
    cambio.delete()


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def administracion(request):
    miembro = Miembro.objects.get(usuario=request.user)
    total_grupos = Grupo.objects.count()
    grupos_activos = Grupo.objects.activos().count()
    grupos_inactivos = Grupo.objects.inactivos().count()
    total_miembros = Miembro.objects.count()
    miembros_activos = Miembro.objects.filter(estado='A').count()
    miembros_restauracion = Miembro.objects.filter(estado='R').count()
    miembros_inactivos = Miembro.objects.filter(estado='I').count()
    total_lideres = CambioTipo.objects.filter(nuevoTipo=TipoMiembro.objects.get(nombre__iexact="Lider")).count()
    total_maestros = CambioTipo.objects.filter(nuevoTipo=TipoMiembro.objects.get(nombre__iexact="Maestro")).count()
    grupos_discipulado = Grupo.objects.pueden_reportar_discipulado().inactivos()
    grupos_amistad = Grupo.objects.activos().exclude(id__in=grupos_discipulado).count()

    return render(request, 'miembros/administracion.html', {
        'total_grupos': total_grupos, 'grupos_activos': grupos_activos, 'grupos_inactivos': grupos_inactivos,
        'total_lideres': total_lideres, 'total_miembros': total_miembros, 'miembros_activos': miembros_activos,
        'miembros_inactivos': miembros_inactivos, 'miembros_restauracion': miembros_restauracion, 'maestros': total_maestros,
        'grupos_discipulados': grupos_discipulado.count(), 'grupos_amistad': grupos_amistad
    })


@login_required
def ver_discipulos(request, pk=None):
    d = True
    miembro = Miembro.objects.get(usuario=request.user)
    mismo = True
    form_desvincular = DesvincularLiderGrupoForm()
    if pk:
        try:
            miembro = Miembro.objects.get(id=pk)
            mismo = False
            if Miembro.objects.get(usuario=request.user).id == miembro.id:
                mismo = True
        except Miembro.DoesNotExist:
            raise Http404

    grupo = miembro.grupo_lidera or None

    if request.method == 'POST':
        if grupo is not None or grupo != '':
            form = FormularioEditarDiscipulado(request.POST or None, instance=grupo)

            if form.is_valid():
                form.save()
                # return HttpResponseRedirect('')
                ok = True
                ms = "Discipulado del grupo %s editado Correctamente" % grupo.nombre
                if mismo:
                    ms = "Tu Discipulado ha sido editado Correctamente"
            else:
                ms = "Ocurrió un Error, Por Favor Verifica el Formulario"
    else:
        if grupo is not None or grupo != '':
            form = FormularioEditarDiscipulado(instance=grupo)

    # discipulos = miembro.discipulos()
    if grupo is not None:
        discipulos = grupo.discipulos
        if len(discipulos) > 0:
            discipulos = discipulos.order_by('nombre')
        else:
            no_discipulos = True

    return render(request, "miembros/discipulos_perfil.html", locals())


@login_required
@transaction.atomic
def ver_informacion_miembro(request, pk=None):
    i = True
    miembro = Miembro.objects.get(usuario=request.user)
    mismo = True
    form_desvincular = DesvincularLiderGrupoForm()
    if pk:
        try:
            miembro = Miembro.objects.get(id=pk)
            mismo = False
            if Miembro.objects.get(usuario=request.user).id == miembro.id:
                mismo = True
        except Miembro.DoesNotExist:
            raise Http404

    if request.user.has_perm('miembros.es_administrador'):
        if request.method == 'POST':
            form = FormularioInformacionIglesiaMiembro(request.POST, instance=miembro)
            form_cambio_tipo = FormularioTipoMiembros(request.POST, instance=miembro)

            if form.is_valid() and form_cambio_tipo.is_valid():
                form.save()
                tipos = form_cambio_tipo.cleaned_data['tipos']
                tpvisita = TipoMiembro.objects.get(nombre__iexact='visita')
                tpmiembro = TipoMiembro.objects.get(nombre__iexact='miembro')
                tplider = TipoMiembro.objects.get(nombre__iexact='lider')

                cambio = CambioTipo.objects.filter(miembro=miembro)
                tipos_cambio = [c.nuevoTipo for c in cambio]
                eliminar = [cambio_iter for cambio_iter in tipos_cambio if cambio_iter not in tipos]

                if len(eliminar):
                    for e in eliminar:
                        try:
                            c = CambioTipo.objects.get(miembro=miembro, nuevoTipo=e)
                        except:
                            c = CambioTipo.objects.get(miembro=miembro, anteriorTipo=e)
                        eliminar_cambio_tipo_miembro(request, c.id)
                    cambio = CambioTipo.objects.filter(miembro=miembro)
                    tipos_cambio = [c_iter.nuevoTipo for c_iter in cambio]

                for tipo in tipos:
                    if tipo not in tipos_cambio:
                        cambio = CambioTipo()
                        cambio.miembro = miembro
                        cambio.autorizacion = Miembro.objects.get(usuario=request.user)
                        cambio.fecha = date.today()
                        if tipo not in tipos_cambio:
                            if tipo == tpvisita:
                                cambio.anteriorTipo = tipo
                            elif tipo == tpmiembro:
                                cambio.anteriorTipo = tpvisita
                            elif tipo == tplider:
                                cambio.anteriorTipo = tpmiembro
                            else:
                                cambio.anteriorTipo = tipo
                        if tipo not in [tpvisita, tpmiembro]:
                            if not cambio.miembro.usuario:
                                import re
                                cedula = re.findall(r'\d+', cambio.miembro.cedula)
                                cedula = ''.join(cedula)
                                try:
                                    usuario = User.objects.get(email=cambio.miembro.email)
                                except:
                                    usuario = User()
                                    usuario.username = '{}'.format(cambio.miembro.cedula)
                                    usuario.email = cambio.miembro.email
                                usuario.set_password(cedula)
                                usuario.save()
                                cambio.miembro.usuario = usuario
                                cambio.miembro.save()
                            if tipo == tplider:
                                cambio.miembro.usuario.groups.add(Group.objects.get(name__iexact='lider'))
                            elif tipo == TipoMiembro.objects.get(nombre__iexact='agente'):
                                cambio.miembro.usuario.groups.add(Group.objects.get(name__iexact='Agente'))
                            elif tipo == TipoMiembro.objects.get(nombre__iexact='maestro'):
                                cambio.miembro.usuario.groups.add(Group.objects.get(name__iexact='Maestro'))
                            elif tipo == TipoMiembro.objects.get(nombre__iexact='receptor'):
                                cambio.miembro.usuario.groups.add(Group.objects.get(name__iexact='Receptor'))
                            elif tipo == TipoMiembro.objects.get(nombre__iexact='administrador'):
                                cambio.miembro.usuario.groups.add(Group.objects.get(name__iexact='Administrador'))
                            elif tipo == TipoMiembro.objects.get(nombre__iexact='pastor'):
                                cambio.miembro.usuario.groups.add(Group.objects.get(name__iexact='Pastor'))
                            cambio.miembro.usuario.save()
                        cambio.nuevoTipo = tipo
                        cambio.save()
                    else:
                        # return HttpResponse(eliminar, content_type='text/plain')
                        continue

                ok = True
                ms = "Miembro %s %s Editado Correctamente" % (miembro.nombre.upper(), miembro.primer_apellido.upper())
                if mismo:
                    ms = "Te has Editado Correctamente"
                # return redirect(reverse('miembros:ver_informacion', args=(miembro.id, )))
            else:
                if form_cambio_tipo.errors:
                    form.add_error('estado', 'Error en formulario')
                ms = "Ocurrió un Error, Por Favor Verifica el Formulario"
        else:
            form = FormularioInformacionIglesiaMiembro(instance=miembro)
            form_cambio_tipo = FormularioTipoMiembros(instance=miembro)

    if miembro.grupo:
        lideres_miembro = miembro.grupo.lideres.all()

    tipos = CambioTipo.objects.filter(miembro=miembro).order_by('-fecha')
    return render(request, "miembros/informacion_perfil.html", locals())


@login_required
def eliminar_foto_perfil(request, pk):
    miembro = Miembro.objects.get(usuario=request.user)
    # mismo = True
    response = {}

    if pk:
        try:
            miembro = Miembro.objects.get(pk=pk)
            # mismo = False
            if Miembro.objects.get(usuario=request.user).id == miembro.id:
                # mismo = True
                pass
        except Miembro.DoesNotExist:
            raise Http404

    foto = False
    if miembro.foto_perfil:
        rut_perfil = miembro.foto_perfil.path
        foto = True
    if request.method == 'POST':
        if 'delete_file' in request.POST:
            if miembro.foto_perfil != '' or miembro.foto_perfil is not None:
                if foto:
                    if os.path.isfile(rut_perfil):
                        os.remove(rut_perfil)
                    try:
                        miembro.foto_perfil.delete(save=True)
                        response['status'] = 'warning'
                        response['ruta'] = settings.STATIC_URL + 'Imagenes/profile-none.jpg'
                        response['ms'] = 'Foto Eliminada Exitosamente'
                    except:
                        response['status'] = 'danger'
                        response['ruta'] = settings.STATIC_URL + 'Imagenes/profile-none.jpg'
                        response['ms'] = 'Hubo un error al intentar eliminar la foto'
                else:
                    response['status'] = 'danger'
                    response['ruta'] = settings.STATIC_URL + 'Imagenes/profile-none.jpg'
                    response['ms'] = 'No hay ninguna foto a eliminar'
            else:
                response['status'] = 'warning'
                response['ruta'] = settings.STATIC_URL + 'Imagenes/profile-none.jpg'
                response['ms'] = 'No hay fotos para eliminar'
        else:
            response['status'] = 'danger'
            response['ruta'] = settings.STATIC_URL + 'Imagenes/profile-none.jpg'
            response['ms'] = 'Permiso denegado para hacer esta operacion'
    return HttpResponse(json.dumps(response), content_type='application/json')


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def crear_miembro(request):
    """
    Permite crear miembros para una iglesia.
    """

    if request.method == 'POST':
        form = NuevoMiembroForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('El miembro se ha creado correctamente'))
            return redirect('miembros:nuevo')
    else:
        form = NuevoMiembroForm()

    return render(request, 'miembros/miembro_form.html', {'form': form})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def listar_lideres(request, pk):
    """
    Permite a un administrador listar los lideres de la red escogida.

    :param pk:
        Pk de la red escogida.
    """

    red = get_object_or_404(Red, pk=pk)
    lideres = Miembro.objects.lideres_red(red).select_related(
        'usuario', 'grupo_lidera', 'grupo'
    ).prefetch_related('grupo__lideres', 'grupo__historiales')

    return render(request, 'miembros/lista_lideres.html', {'red': red, 'lideres': lideres})


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def trasladar(request, pk):
    """
    Permite a un administrador trasladar un miembro que no lidere grupo a que asista a otro grupo.
    """

    miembro = get_object_or_404(Miembro, pk=pk)
    if miembro.grupo_lidera:
        return redirect(reverse('sin_permiso'))

    if request.method == 'POST':
        form = TrasladarMiembroForm(data=request.POST)
        if form.is_valid():
            form.trasladar(miembro)
            return redirect('miembros:trasladar', pk)
    else:
        form = TrasladarMiembroForm()

    return render(request, 'miembros/trasladar.html', {'miembro': miembro, 'form': form})

@login_required
def discipulados(request, pk):
    miembro = get_object_or_404(Miembro.objects.filter(pk=pk).select_related('grupo_lidera'), pk=pk)
    return render(request, 'miembros/discipulados_perfil.html', {
        'miembro': miembro, 'discipulados': True, 'pk': pk
    })