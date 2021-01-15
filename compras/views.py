"""

    Fecha Inicio Desarrollo: 1 Agosto 2016

    Desarrollado por Ingeniarte Soft.

    Trazabilidad de las requisiciones

    los siguientes son los pasos que sigue la trazabilidad de las requisiciones:

        - Un Usuario de Consulta hace una requisicion

        - Inicialmente esa requisicion llega al jefe de el departamento de usuario y es este
        jefe quien determina que ruta tomara esta peticion, de aprobarla, la peticion de la
        requisicion llegará a un usuario de el área de compras; de lo contrario, esta requisicion
        será anulada

        - Una vez un usuario jefe de el departamento aprueba una requisicion, esta, entra en
        estado de proceso y es direccionada a los usuarios que pertenezcan al area de compras,
        los cuales son los encargados de hacer las cotizaciones correspondientes a cada detalle
        de la requisición, a su vez pueden agregar comentarios y archivos adjuntos para complementar
        su trabajo con respecto a la requisicion, tambien puede editar los precios de los items de
        la requisicion, de acuerdo a sus cotizaciones, este usuario no puede darle un estado de rechazo a
        una requisicion. Una vez el usuario de compras haya terminado su proceso, puede darle paso a
        un Director administrativo

        - Un usuario administrativo es un empleado que es jefe de departamento y ese departamento
        puede tener cualquier nombre empezado por 'adminis', se sabe que es jefe de ese departamento
        si tiene un area relacionada con ese departamento, este jefe de departamento es el encargado
        de dar el ultimo visto acerca de la requisicion y tiene la potestad de aprobar o rechazar dicha
        requisicion, al igual que cambiar sus valores y declarar cual será la forma de pago definitiva
        de cada item de la requisicion, definiendo asi el rumbo que deberá tomar la requisicion

        - En este punto, si la requisicion supera un monto establecido en la aplicacion por un administrador
        que en este caso es de 2'000.000, esta inmediatamente que el jefe administrativo la apruebe, pasa
        a el área de presidencia, en la cual el presidente es el encargado de decir si la requisicion avanzará
        de acuerdo a sus criterios, en caso de aceptar sigue su ciclo normal hacia el director financiero,
        de lo contrario acaba la requisicion

        - En caso de que el usuario administrativo o el presidente apruebe la requisicion esta llega a los usuarios
        de el Departamento de financiamiento haciendo una primera escala a el jefe o director de este
        departamento, el cual debe aclarar en la requisicion si hay presupuesto para satisfacerla,
        en caso de no haber presupuesto, debe notificarlo con una observacion y poniendo el estado
        de ´EN ESPERA´, en este estado, el jefe administrativo y el director financiero puede comentar
        a manera de pregunta respuesta una requisicion, hasta que el jefe financiero cambie el estado a ´SI´
        hay presupuesto

        - En este punto, la requisicion puede tomar dos caminos, de acuerdo a sus detalles, si la requisicion
        es de crédito, automaticamente pasa a el usuario solicitante de la requisicion, con el fin de que una
        vez este haya recibido lo que pidio, lo notifique y asi finalizar el proceso de la requisicion; tambien,
        si la requisicion es de tipo DEBITO(CHEQUE) o EFECTIVO, esta tiene un escalon mas que avanzar hacia el area
        de pagos

        - Cuando El Director de el departamento de financiacion ha dado el ´SI´ de que hay presupuesto
        para satisfacer una requisicion y la requisicion tiene articulos que seran pagados en EFECTIVO o CHEQUE,
        entonces, esta llega a un usuario encargado de hacer el pago el cual al entregar el dinero le da un estado
        de pago a la requisicion que viene dado a partir de otros tres posibles estados

        - Como paso final de la requisición, esta llega de vuelta al solicitante de la requisicion,
        el cual termina la requisicion una vez notifica que ha recibido todos los items de su requisición

        Last Updated: 30th September 2016


"""

# Django Packages
from django.http import Http404
from django.utils import timezone
from django.contrib import messages
from django.db import transaction, models
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext as _
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory, modelformset_factory
from django.contrib.auth.decorators import permission_required, login_required

# Third Apps
from waffle.decorators import waffle_switch

# Locale Apps
from .forms import (
    FormularioSolicitudRequisicion, FormularioDetalleRequisicion, FormularioAdjunto,
    FormularioRequisicionesCompras, FormularioObservacionHistorial, FormularioFechaPagoRequisicion,
    FormularioEstadoPago, FormularioEditarValoresDetallesRequisiciones,
    FormularioEditarValoresJefeAdministrativo, FormularioCumplirDetalleRequisicion,
    FormularioInformeTotalesAreaDerpartamento, FormularioProveedor
)
from .models import DetalleRequisicion, Requisicion, Adjunto, Historial, Proveedor
from organizacional.models import Empleado
from organizacional.decorators import login_empleado

__author__ = 'German Alzate'


@waffle_switch('compras')
@login_empleado
@transaction.atomic
def crear_requisicion(request):
    """
    Vista para la creacion de requisiciones en el modulo de compras, marca el inicio
    de la trazabilidad
    """
    try:
        # se obtiene el empleado
        empleado = request.user.empleado
    except:
        raise Http404

    # se crea el formset de los detalles de la requisicion
    DetalleRequisicionFormSet = inlineformset_factory(
        Requisicion, DetalleRequisicion, fk_name='requisicion',
        form=FormularioDetalleRequisicion, min_num=1, extra=4,
        validate_min=True, can_delete=False
    )

    # se crea el formset para los archivos adjuntos de la requisicion
    AdjuntoFormset = inlineformset_factory(
        Requisicion, Adjunto, fk_name='requisicion',
        form=FormularioAdjunto, min_num=0, extra=1,
        validate_min=True, can_delete=False
    )

    if request.method == 'POST':
        # se instancian los tres formularios
        form = FormularioSolicitudRequisicion(data=request.POST)
        # se crea una primera instancia de los formularios para que puedan ser validados
        formset_detalles = DetalleRequisicionFormSet(data=request.POST)
        formset_adjunto = AdjuntoFormset(request.POST, request.FILES)
        if form.is_valid():
            # se guarda la requisicion
            requisicion = form.save(commit=False)
            requisicion.empleado = empleado
            # se vuelven a instanciar los formularios para verificar que este todo válido
            formset_detalles = DetalleRequisicionFormSet(data=request.POST, instance=requisicion)
            formset_adjunto = AdjuntoFormset(request.POST, request.FILES, instance=requisicion)
            if formset_detalles.is_valid() and formset_adjunto.is_valid():
                # se crea la requisicion y se guardan los detalles y los adjuntos
                requisicion.save()
                formset_adjunto.save()
                formset_detalles.save()
                # se crea una url para hacer la redireccion
                url = """
                    <a class='alert-link' href='%s'>Ver Mis Requisiciones</a>
                    """ % reverse_lazy('compras:ver_requisiciones_empleado')
                # si el empleado es jefe_departamento pero no es administrativo se crea un historial
                if empleado.jefe_departamento and not empleado.is_jefe_administrativo \
                   and not empleado.is_jefe_financiero:
                    historial = requisicion.crear_historial(empleado=empleado, estado=Historial.APROBADA)
                    historial.save()
                    requisicion.estado = Requisicion.PROCESO
                    requisicion.save()
                messages.success(request, _("Se ha creado la requisicion con éxito" + url))
                return redirect('compras:crear_requisicion')
            else:
                messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))

    else:
        # se instancian los 3 formularios
        form = FormularioSolicitudRequisicion()
        formset_detalles = DetalleRequisicionFormSet()
        formset_adjunto = AdjuntoFormset()

    data = {'form': form, 'formset_detalles': formset_detalles, 'formset_adjunto': formset_adjunto}

    return render(request, 'compras/crear_requisicion.html', data)


@waffle_switch('compras')
@login_empleado
@transaction.atomic
def editar_requisicion(request, id_requisicion):
    """
    Vista para la edicion de requisiciones, siempre y cuando esta se encuentre en estado PENDIENTE,
    es decir, nadie puede editar una requisicion, solo el que la crea y solo mientras mas nadie
    haya hecho algo con esa misma requisicion, al momento de apsar a otra area deja de ser editable
    """
    try:
        # se obtiene la requisicion
        requisicion = Requisicion.objects.get(id=id_requisicion)
        if requisicion.estado != Requisicion.PENDIENTE:
            raise Http404
    except Requisicion.DoesNotExist:
        raise Http404
    # si el empleado no tiene los permisos se redirecciona a la pagina de sin permisos
    # si el empleado no fue quien realizó la requisicion
    empleado = requisicion.empleado
    try:
        if empleado != request.user.empleado:
            return redirect('sin_permiso')
    except Empleado.DoesNotExist:
        raise Http404

    # se crean los modelos de los formularios
    DetalleRequisicionFormSet = modelformset_factory(
        DetalleRequisicion, form=FormularioDetalleRequisicion,
        min_num=1, extra=0, validate_min=True, can_delete=True
    )

    AdjuntoFormset = modelformset_factory(
        Adjunto, form=FormularioAdjunto, min_num=0, extra=1,
        validate_min=False, can_delete=True
    )

    if request.method == 'POST':
        # se instancian los formularios de el POST
        form = FormularioSolicitudRequisicion(data=request.POST, instance=requisicion)
        # se les pone un prefijo a los formularios para que todo pueda trabajar bien
        formset_detalles = DetalleRequisicionFormSet(
            prefix='detallerequisicion_set',
            queryset=requisicion.detallerequisicion_set.all()
        )
        formset_adjunto = AdjuntoFormset(
            prefix='adjunto_set',
            queryset=requisicion.adjunto_set.all()
        )
        if form.is_valid():
            # si el formulario es valido se vuelven a instanciar los formularios [FORMSETS]
            formset_detalles = DetalleRequisicionFormSet(
                data=request.POST, prefix='detallerequisicion_set',
                queryset=requisicion.detallerequisicion_set.all()
            )
            formset_adjunto = AdjuntoFormset(
                data=request.POST, files=request.FILES, prefix='adjunto_set',
                queryset=requisicion.adjunto_set.all()
            )
            if formset_adjunto.is_valid() and formset_detalles.is_valid():
                # si todo está válido
                url = """
                    <a class='alert-link' href='%s'>Ver Mis Requisiciones</a>
                    """ % reverse_lazy('compras:ver_requisiciones_empleado')
                requisicion = form.save()
                # se guarda la requisicion y sus campos relacionados
                for form_adjunto in formset_adjunto:
                    if form_adjunto.cleaned_data.get('DELETE', False) and hasattr(form_adjunto.instance, 'pk'):
                        if form_adjunto.instance.id is not None or form_adjunto.instance.pk is not None:
                            form_adjunto.instance.delete()
                        continue
                    form_adjunto.instance.requisicion = requisicion
                    if not form_adjunto.cleaned_data.get('archivo', False):
                        continue
                    form_adjunto.save()

                for form_detalle in formset_detalles:
                    if form_detalle.cleaned_data.get('DELETE', False) and hasattr(form_detalle.instance, 'pk'):
                        if form_detalle.instance.id is not None or form_detalle.instance.pk is not None:
                            form_detalle.instance.delete()
                        continue
                    form_detalle.instance.requisicion = requisicion
                    if not form_detalle.cleaned_data.get('descripcion', False):
                        continue
                    form_detalle.save()
                # formset_detalles.save()
                # formset_adjunto.save()
                messages.success(request, _("Se ha editado la requisicion con éxito " + url))
                return redirect(reverse('compras:editar_requisicion', args=(id_requisicion, )))
            else:
                messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))

    else:
        # se instancian los formularios para el GET
        form = FormularioSolicitudRequisicion(instance=requisicion)
        formset_detalles = DetalleRequisicionFormSet(
            prefix='detallerequisicion_set', queryset=requisicion.detallerequisicion_set.all()
        )
        formset_adjunto = AdjuntoFormset(
            prefix='adjunto_set', queryset=requisicion.adjunto_set.all()
        )

    data = {
        'requisicion': requisicion, 'formset_detalles': formset_detalles,
        'formset_adjunto': formset_adjunto, 'form': form
    }

    return render(request, 'compras/crear_requisicion.html', data)


@waffle_switch('compras')
@login_empleado('is_compras')
def crear_proveedor(request):
    """
    Vista para la creación de proveedores en el sistema de compras, la cual solo puede
    ser creada por un usuario administrador o de compras
    """

    try:
        empleado = request.user.empleado
        if not empleado.is_jefe_administrativo:  # and (not empleado.is_compras):
            return redirect('sin_permiso')
    except:
        if not request.user.is_superuser:
            raise Http404

    if request.method == 'POST':
        form = FormularioProveedor(data=request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, _('Se Ha Creado el Proveedor Exitosamente'))
            return redirect(reverse('compras:crear_proveedor'))
        else:
            messages.error(request, _('Ha ocurrido un error al enviar el formulario'))
    else:
        form = FormularioProveedor()

    data = {'form': form}

    return render(request, 'compras/crear_proveedor.html', data)


@waffle_switch('compras')
@login_required
def editar_proveedor(request, id_proveedor):
    """
    Vista para la edición de el proveedor
    """

    try:
        empleado = request.user.empleado
        if not empleado.is_jefe_administrativo and (not empleado.is_compras):
            return redirect('sin_permiso')
    except:
        if not request.user.is_superuser:
            raise Http404

    proveedor = get_object_or_404(Proveedor, pk=id_proveedor)

    if request.method == 'POST':
        form = FormularioProveedor(data=request.POST, instance=proveedor)

        if form.is_valid():
            form.save()
            messages.success(request, _('Se Ha Editado el Proveedor Exitosamente'))
            return redirect(reverse('compras:editar_proveedor', args=(proveedor.id, )))
        else:
            messages.error(request, _('Ha ocurrido un error al enviar el formulario'))
    else:
        form = FormularioProveedor(instance=proveedor)

    data = {'form': form, 'proveedor': proveedor}

    return render(request, 'compras/crear_proveedor.html', data)


@waffle_switch('compras')
@login_required
def listar_proveedores(request):
    """
    Vista para la lista de proveedores
    """

    try:
        empleado = request.user.empleado
        if not empleado.is_jefe_administrativo and (not empleado.is_compras):
            return redirect('sin_permiso')
    except:
        if not request.user.is_superuser:
            raise Http404

    proveedores = Proveedor.objects.all().prefetch_related('requisiciones')

    return render(request, 'compras/listar_proveedores.html', {'proveedores': proveedores})


@waffle_switch('compras')
@login_empleado
def ver_requisiciones_empleado(request):
    """
    Vista para la vista de las requisiciones hechas por el empleado de la sesion
    actual, donde se puede ver la trazabilidad de la requisicion en ese instante
    """

    try:
        # se sacan las requisiciones de el empleado de la sesion
        empleado = request.user.empleado
    except:
        raise Http404

    # se ordenan las requisiciones y se envian
    requisiciones = empleado.requisicion_set.all().order_by(
        '-fecha_ingreso'
    ).prefetch_related('detallerequisicion_set')

    data = {'requisiciones': requisiciones, 'CLICK': request.GET.get('check', False)}

    return render(request, 'compras/ver_requisiciones_empleado.html', data)


@waffle_switch('compras')
@login_empleado('jefe_departamento')
def ver_requisiciones_jefe_departamento(request):
    """
    Vista para ver las requisiciones que se han hecho a un departamento,
    son las que hacen empleados comunes y tienen que ser aprobadas por un jefe
    de departamento
    """
    try:
        empleado = request.user.empleado
    except:
        raise Http404

    # se obtienen las requisiciones de los subalternos al jefe de departamento
    requisiciones = Requisicion.objects.filter(
        empleado__areas__departamento__in=request.user.empleado.areas.departamentos()
    ).exclude(estado=Requisicion.ANULADA).order_by('-fecha_ingreso')

    # se crea la variable para pasar los datos a la vista
    data = {}

    if request.method == 'POST':
        # se crea la instancia de el formulario para los comentarios
        form = FormularioRequisicionesCompras(data=request.POST)
        if form.is_valid():
            # si todo está valido se obtiene la requisicion a partir de id de el formulario
            requisicion = Requisicion.objects.get(id=form.cleaned_data['id_requisicion'])
            if 'aprobar' in request.POST:
                # si se aprueba se crea el historial con su respectivo comentario
                if form.cleaned_data['observacion'] != '':
                    historial = requisicion.crear_historial(
                        empleado=empleado, estado=Historial.APROBADA,
                        observacion=form.cleaned_data['observacion']
                    )
                # si no tiene comentarios
                else:
                    historial = requisicion.crear_historial(
                        empleado=empleado, estado=Historial.APROBADA
                    )
                mensaje = 'aprobado'
                requisicion.estado = Requisicion.PROCESO
            elif 'rechazar' in request.POST:
                # si se rechaza la requisicion la observacion es obligatoria
                historial = requisicion.crear_historial(
                    empleado=empleado, estado=Historial.RECHAZADA,
                    observacion=form.cleaned_data['observacion']
                )
                mensaje = 'rechazado'
                requisicion.estado = Requisicion.ANULADA
            # en este punto debe llegar siempre un historial o tirará un error
            requisicion.save()
            historial.save()
            messages.success(
                request,
                _("Se ha {} la requisicion No.{} exitosamente").format(mensaje, requisicion.id)
            )
            return redirect('compras:ver_requisiciones_jefe_departamento')
        else:
            # se crea una variable con el id de la requisicion para el front
            data['CLICK'] = form.cleaned_data['id_requisicion']
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
    else:
        # se instancia el formulario en el GET
        form = FormularioRequisicionesCompras()
    # se crean las variables para los templates
    data['requisiciones'] = requisiciones
    data['form'] = form

    return render(request, 'compras/ver_requisiciones_jefe_departamento.html', data)


@waffle_switch('compras')
@login_empleado('is_compras')
def ver_requisiciones_compras(request):
    """
    Vista para ver las requisiciones que han llegado al area de compras, luego de ser
    aprobadas por un usuario jefe de departamento
    """

    try:
        # se obtiene el usuario a partir de la peticion
        empleado = request.user.empleado
    except:
        raise Http404

    data = {}

    # se obtiene el queryset de requisiciones aprobadas por jefe de departamento
    requisiciones = Requisicion.objects.aprobadas_jefe_departamento().order_by(
        '-fecha_ingreso').prefetch_related('historial_set')

    if request.method == 'POST':
        # se instancia el formulario
        form = FormularioRequisicionesCompras(data=request.POST)
        if form.is_valid():
            # se obtiene la requisicion a partir de el formulario
            requisicion = Requisicion.objects.get(id=form.cleaned_data['id_requisicion'])
            # siempre se debe aprobar, de lo contrario es invalido
            if 'aprobar' in request.POST:
                # se crea el historial de acuerdo a si hay observaciones o no
                if 'observacion' in form.cleaned_data:
                    historial = requisicion.crear_historial(
                        empleado=empleado, estado=Historial.APROBADA,
                        observacion=form.cleaned_data['observacion']
                    )
                else:
                    historial = requisicion.crear_historial(empleado=empleado, estado=Historial.APROBADA)
                mensaje = 'aprobado'
                historial.save()
                messages.success(
                    request,
                    _("Se ha {} la requisición No.{} con exito".format(mensaje, requisicion.id))
                )
                return redirect('compras:ver_requisiciones_compras')
            else:
                # si es invalido se envia el mensaje de error
                messages.error(request, _("Ha hecho una peticion inválida"))
        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
    else:
        # se instancia el formulario de el GET
        form = FormularioRequisicionesCompras()
        check = request.GET.get('check', None)
        if check is not None:
            data['CLICK'] = check

    data['requisiciones'] = requisiciones
    data['form'] = form

    return render(request, 'compras/ver_requisiciones_compras.html', data)


@waffle_switch('compras')
@login_empleado('is_compras')
def adjuntar_archivos_requisicion(request, id_requisicion):
    """
    Vista para adjuntar archivos a una requisicion, solo disponible para usuarios
    de el area de compras
    """

    # se obtiene el usuario
    try:
        empleado = request.user.empleado
    except:
        raise Http404

    # se obtiene la requisicion
    requisicion = get_object_or_404(Requisicion, pk=id_requisicion)

    # deja entrar siempre y cuando la solicitud no este anulada o terminada
    if requisicion.is_anulada or requisicion.estado == Requisicion.TERMINADA or \
       Requisicion.DATA_SET['compras'] != requisicion.get_rastreo():
        raise Http404

    # inicializa variable para saber si instnciar el formulario o no
    _historial_nuevo = False

    # se crea un formulario para los detalles de la requisicion
    DetalleRequisicionFormSet = modelformset_factory(
        DetalleRequisicion, form=FormularioEditarValoresDetallesRequisiciones,
        min_num=requisicion.detallerequisicion_set.count(), extra=0, validate_min=True,
    )

    # se crea el formset que manejará los formularios de documentos adjuntos
    AdjuntoFormset = modelformset_factory(
        Adjunto, form=FormularioAdjunto, min_num=0, extra=1,
        validate_min=False, can_delete=True
    )

    if request.method == 'POST':
        # se instancia el formulario de detalles de requisicion
        formset_detalles = DetalleRequisicionFormSet(
            data=request.POST,
            prefix='detallerequisicion_set',
            queryset=requisicion.detallerequisicion_set.all()
        )
        # si la requisicion en su ultimo historial fue hecho por un usuario del area de compras
        if Requisicion.DATA_SET['administrativo'] == requisicion.get_rastreo():
            # se crea el formulario instanciado
            form_historial = FormularioObservacionHistorial(
                data=request.POST, instance=requisicion.historial_set.last()
            )
        else:
            # se crea un formulario nuevo
            form_historial = FormularioObservacionHistorial(data=request.POST)
            # se asigna true a la variable para indicar que es un formulario sin instancia
            _historial_nuevo = True

        # se instancia el formset
        formset_adjunto = AdjuntoFormset(
            data=request.POST, files=request.FILES,
            queryset=requisicion.adjunto_set.all(), prefix='adjunto_set'
        )

        # si todo es valido
        if formset_adjunto.is_valid() and form_historial.is_valid() and formset_detalles.is_valid():
            url = """
                <a href='%s' class='alert-link'>Volver a la lista de Requisiciones</a>
                """ % reverse_lazy('compras:ver_requisiciones_compras')
            # ciclo encargado de borrar los documentos que seran eliminados y agregar los nuevos documentos
            for form_adjunto in formset_adjunto:
                # si el formulario tiene el DELETE en el post y si la instancia ya fue creada alguna vez
                if form_adjunto.cleaned_data.get('DELETE', False) and hasattr(form_adjunto.instance, 'pk'):
                    # si todo esta bien con el pk y id
                    if form_adjunto.instance.id is not None or form_adjunto.instance.pk is not None:
                        # se borra el documento que se pidio desde la vista
                        form_adjunto.instance.delete()
                    continue
                # si no, crea el documento y le asigna la requisicion
                form_adjunto.instance.requisicion = requisicion
                # si no tiene archivo no lo guarda
                if not form_adjunto.cleaned_data.get('archivo', False):
                    continue
                # de el caso contrario guarda el formulario con el nuevo archivo
                form_adjunto.save()

            historial = form_historial.save(commit=False)
            # Si es nuevo y tiene alguna observacion
            # si no tiene observacion tiene la opcion de darle en aceptar desde la vista de lista
            if _historial_nuevo and historial.observacion != '':
                # se crea el hitorial
                historial.empleado = empleado
                historial.requisicion = requisicion
                historial.estado = Historial.APROBADA

            # siempre y cuando sea un historial completo se guarda
            if hasattr(historial, 'requisicion'):
                historial.save()

            # se guarda el formset de detalles
            formset_detalles.save()

            messages.success(
                request,
                _("Se ha editado la requisicion No.{} exitosamente ".format(requisicion.id) + url)
            )
            if Requisicion.DATA_SET['compras'] == requisicion.get_rastreo():
                return redirect(reverse('compras:adjuntar_archivos_requisicion', args=(requisicion.id, )))
            return redirect(reverse('compras:ver_requisiciones_compras'))

        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))

    else:
        # if requisicion.historial_set.last().observacion != '':
        # se verifica quien fue el ultimo en hacer algo con la requisicion para instanciar o no el formulario
        if Requisicion.DATA_SET['administrativo'] == requisicion.get_rastreo():
            form_historial = FormularioObservacionHistorial(
                instance=requisicion.historial_set.last()
            )
        # si no, no se instancia el formulario
        else:
            form_historial = FormularioObservacionHistorial()
        # se instancia el formulario de archivos adjuntos
        formset_adjunto = AdjuntoFormset(queryset=requisicion.adjunto_set.all(), prefix='adjunto_set')
        # se instancia el formset de los detalles de requisiciones
        formset_detalles = DetalleRequisicionFormSet(
            prefix='detallerequisicion_set',
            queryset=requisicion.detallerequisicion_set.all()
        )

    data = {
        'formset_adjunto': formset_adjunto, 'form': form_historial,
        'requisicion': requisicion, 'formset_detalles': formset_detalles
    }

    return render(request, 'compras/adjuntar_archivos_requisicion.html', data)


@waffle_switch('compras')
@login_empleado('is_jefe_administrativo')
def ver_requisiciones_jefe_administrativo(request):
    """
    Vista que lista las requisiciones que fueron aprobadas por los usuarios de compras
    y que se encuentran para que el jefe administrativo pueda aprobarlas o rechazarlas
    """

    # se sacan las requisiciones aprobadas por compras, y se ordenan por fecha de ingreso
    requisiciones = Requisicion.objects.aprobadas_compras().distinct().order_by('-fecha_ingreso')
    try:
        empleado = request.user.empleado
    except:
        raise Http404

    data = {'requisiciones': requisiciones}

    # si la peticion es POST
    if request.method == 'POST':
        # se crea el formulario
        form = FormularioRequisicionesCompras(data=request.POST)
        if form.is_valid():
            # se busca la requisicion que apunta el formulario
            requisicion = Requisicion.objects.get(id=form.cleaned_data['id_requisicion'])
            # si se aprueba
            if 'aprobar' in request.POST:
                # se verifica que no existan detalles en la requisicion sin forma de pago
                if requisicion.detallerequisicion_set.filter(forma_pago='').exists():
                    # si existe, entonces, crea un error en el formulario
                    form.add_error(
                        'observacion', _('No se puede aprobar la requisicion si no tiene una forma de pago definida')
                    )
                    # envia el formulario de vuelta
                    data['CLICK'] = form.cleaned_data['id_requisicion']
                    messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
                    data['form'] = form
                    # envia los datos de vuelta
                    return render(request, 'compras/ver_requisiciones_jefe_administrativo.html', data)
                else:
                    # de lo contrario, crea los historiales adecuadamente
                    if 'observacion' in form.cleaned_data:
                        historial = requisicion.crear_historial(
                            empleado=empleado, estado=Historial.APROBADA,
                            observacion=form.cleaned_data['observacion']
                        )
                    else:
                        historial = requisicion.crear_historial(empleado=empleado, estado=Historial.APROBADA)
                mensaje = 'aprobado'
            elif 'rechazar' in request.POST:
                # rechaza la requisicion
                historial = requisicion.crear_historial(
                    empleado=empleado, estado=Historial.RECHAZADA,
                    observacion=form.cleaned_data['observacion']
                )
                requisicion.estado = Requisicion.ANULADA
                requisicion.save()
                mensaje = 'rechazado'
            # guarda el historial
            historial.save()
            messages.success(
                request,
                _("Se ha {} la requisición No.{} con exito".format(mensaje, requisicion.id))
            )
            return redirect('compras:ver_requisiciones_jefe_administrativo')
        else:
            data['CLICK'] = form.cleaned_data['id_requisicion']
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
    else:
        form = FormularioRequisicionesCompras()
        check = request.GET.get('check', None)
        if check is not None:
            data['CLICK'] = check

    data['form'] = form

    return render(request, 'compras/ver_requisiciones_jefe_administrativo.html', data)


@waffle_switch('compras')
@login_empleado('is_jefe_administrativo')
def editar_valores_jefe_administrativo(request, id_requisicion):
    """
    Vista para poder editar los valores y la forma de pago de los detalles de una requisicion
    solo se puede hacer mientras la requisicion esté en el area de el jefe administrativo
    """
    try:
        requisicion = get_object_or_404(Requisicion, pk=id_requisicion)
        empleado = request.user.empleado
        if Requisicion.DATA_SET['administrativo'] != requisicion.get_rastreo():
            raise Http404
    except:
        raise Http404

    # se crea un formulario para los detalles de la requisicion
    DetalleRequisicionFormSet = modelformset_factory(
        DetalleRequisicion, form=FormularioEditarValoresJefeAdministrativo,
        min_num=requisicion.detallerequisicion_set.count(), extra=0, validate_min=True,
    )

    if request.method == 'POST':
        URL = """
            <a href="%s" class="alert-link">VOLVER A LA LISTA DE REQUISICIONES</a>
        """ % reverse_lazy('compras:ver_requisiciones_jefe_administrativo')

        formset_detalles = DetalleRequisicionFormSet(
            data=request.POST,
            prefix='detallerequisicion_set',
            queryset=requisicion.detallerequisicion_set.all()
        )

        if formset_detalles.is_valid():
            formset_detalles.save()
            messages.success(
                request,
                _("Se ha editado la requisición NO.{} exitosamente ".format(requisicion.id) + URL)
            )
            return redirect(
                reverse('compras:editar_valores_jefe_administrativo', args=(requisicion.id, ))
            )
        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
    else:
        formset_detalles = DetalleRequisicionFormSet(
            prefix='detallerequisicion_set',
            queryset=requisicion.detallerequisicion_set.all()
        )

    data = {'requisicion': requisicion, 'formset_detalles': formset_detalles}
    return render(request, 'compras/editar_valores_jefe_administrativo.html', data)


@waffle_switch('compras')
@login_empleado('is_jefe_financiero')
def ver_requisiciones_financiero(request):
    """
    Vista para ver las requisiciones que han llegado al sector financiero
    """
    try:
        empleado = request.user.empleado
        # if not empleado.is_jefe_financiero:
        #     raise Http404
    except Empleado.DoesNotExist:
        raise Http404

    requisiciones = Requisicion.objects.aprobadas_jefe_administrativo().distinct().order_by('-fecha_ingreso')
    data = {'requisiciones': requisiciones}

    if request.method == 'POST':
        pass
    else:
        data['CLICK'] = request.GET.get('check', False)

    return render(request, 'compras/ver_requisiciones_financiero.html', data)


@waffle_switch('compras')
@login_empleado('is_jefe_financiero')
@transaction.atomic
def pre_pago_requisicion(request, id_requisicion):
    """
    Vista para darle a las requisiciones un pre-pago, indicando el dia que se debe pagar la factura
    y la forma de pago, antes de pasar a un usuario encargado de el pago
    """

    requisicion = get_object_or_404(Requisicion, pk=id_requisicion)
    try:
        empleado = request.user.empleado
        _accepted = [Requisicion.DATA_SET['financiero'], Requisicion.DATA_SET['espera_presupuesto']]
        if not empleado.is_jefe_financiero or \
           requisicion.get_rastreo() not in _accepted or requisicion.fecha_pago:
            raise Http404
    except Empleado.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = FormularioFechaPagoRequisicion(data=request.POST, instance=requisicion)

        if form.is_valid():
            requisicion = form.save()
            if 'observacion' in form.cleaned_data:
                historial = requisicion.crear_historial(
                    empleado=empleado, estado=Historial.APROBADA, observacion=form.cleaned_data['observacion']
                )
            else:
                historial = requisicion.crear_historial(empleado=empleado, estado=Historial.APROBADA)
            historial.save()
            messages.success(
                request,
                _("Se ha modificado la requisicion NO.{} exitosamente").format(requisicion.id)
            )
            return redirect('compras:ver_requisiciones_financiero')
        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
    else:
        form = FormularioFechaPagoRequisicion(instance=requisicion)

    data = {'requisicion': requisicion, 'form': form}

    return render(request, 'compras/pre_pago_requisicion.html', data)


@waffle_switch('compras')
@login_empleado('is_usuario_pago')
def ver_requisiciones_usuario_pago(request):
    """
    Vista para listar las requisiciones que han aprobado los jefes de el departamento
    financiero
    """

    try:
        empleado = request.user.empleado
    except:
        raise Http404

    requisiciones = Requisicion.objects.aprobadas_jefe_financiero().order_by('-fecha_ingreso')

    data = {'requisiciones': requisiciones}

    return render(request, 'compras/ver_requisiciones_usuario_pago.html', data)


@waffle_switch('compras')
@login_empleado
def pagar_requisicion(request, id_requisicion):
    """
    Vista con la que acaba el proceso de trazabilidad, en la cual se le pone un estado
    de pago a la requisicion y se le da el estado de terminada, hecha por un usuario
    encargado de los pagos
    """

    try:
        empleado = request.user.empleado
    except:
        raise Http404

    requisicion = get_object_or_404(Requisicion, pk=id_requisicion)

    if Requisicion.DATA_SET['pago'] != requisicion.get_rastreo():
        raise Http404

    if request.method == 'POST':
        form = FormularioEstadoPago(data=request.POST, instance=requisicion)

        if form.is_valid():
            requisicion = form.save()
            # requisicion.estado = Requisicion.TERMINADA
            # requisicion.save()
            if requisicion.estado_pago:
                historial = requisicion.crear_historial(empleado=empleado, estado=Historial.APROBADA)
                historial.save()

            messages.success(
                request,
                _(
                    "Se ha aprobado exitosamente la requisición No.{}".format(
                        requisicion.id
                    )
                )
            )
            return redirect('compras:ver_requisiciones_usuario_pago')

        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))

    else:
        form = FormularioEstadoPago(instance=requisicion)

    data = {
        'form': form,
        'requisicion': requisicion
    }

    return render(request, 'compras/pagar_requisicion.html', data)


@waffle_switch('compras')
@permission_required('organizacional.es_presidente', login_url='sin_permiso')
def ver_requisiciones_presidencia(request):
    """
    Vista para ver las requisiciones que han alcanzado cierto punto de tope en su total
    y tienen que ser aprobadas por presidencia
    """
    try:
        empleado = request.user.empleado
    except:
        raise Http404

    requisiciones = Requisicion.objects.en_presidencia().order_by('-fecha_ingreso')

    data = {'requisiciones': requisiciones}

    if request.method == 'POST':
        # se crea la instancia de el formulario para los comentarios
        form = FormularioRequisicionesCompras(data=request.POST)
        if form.is_valid():
            # si todo está valido se obtiene la requisicion a partir de id de el formulario
            requisicion = Requisicion.objects.get(id=form.cleaned_data['id_requisicion'])
            if 'aprobar' in request.POST:
                # si se aprueba se crea el historial con su respectivo comentario
                if form.cleaned_data['observacion'] != '':
                    historial = requisicion.crear_historial(
                        empleado=empleado, estado=Historial.APROBADA,
                        observacion=form.cleaned_data['observacion']
                    )
                # si no tiene comentarios
                else:
                    historial = requisicion.crear_historial(
                        empleado=empleado, estado=Historial.APROBADA
                    )
                mensaje = 'aprobado'
            elif 'rechazar' in request.POST:
                # si se rechaza la requisicion la observacion es obligatoria
                historial = requisicion.crear_historial(
                    empleado=empleado, estado=Historial.RECHAZADA,
                    observacion=form.cleaned_data['observacion']
                )
                mensaje = 'rechazado'
                requisicion.estado = Requisicion.ANULADA
            # en este punto debe llegar siempre un historial o tirará un error
            requisicion.save()
            historial.save()
            messages.success(
                request,
                _("Se ha {} la requisicion No.{} exitosamente").format(mensaje, requisicion.id)
            )
            return redirect('compras:ver_requisiciones_presidencia')
        else:
            # se crea una variable con el id de la requisicion para el front
            data['CLICK'] = form.cleaned_data['id_requisicion']
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
    else:
        # se instancia el formulario en el GET
        form = FormularioRequisicionesCompras()
    data['form'] = form

    return render(request, 'compras/ver_requisiciones_presidencia.html', data)


@waffle_switch('compras')
@login_required
def aprobar_requisiciones_empleado(request, id_requisicion):
    """
    Vista que usa el usuario empleado digitador de la requisicion para poder aprobar los items
    individualmente de la requisición que ha solicitado, una vez estos hayan sido aprobados
    """
    requisicion = get_object_or_404(Requisicion, pk=id_requisicion)
    # HACER MODIFICACION PORQUE SI PUEDE ENTRAR CON LA CONDICION DE QUE TENGA ALGO EN CREDITO
    try:
        empleado = request.user.empleado
        if empleado != requisicion.empleado:
            raise Http404
        _accepted = [Requisicion.DATA_SET['solicitante'], Requisicion.DATA_SET['pago']]
        if requisicion.get_rastreo() not in _accepted:
            raise Http404
        elif requisicion.get_rastreo() == _accepted[1]:
            if not requisicion.detallerequisicion_set.filter(forma_pago=DetalleRequisicion.CREDITO):
                raise Http404
    except:
        raise Http404

    data = {}

    # Se crea el formset para los detalles de la requisicion
    DetalleRequisicionFormSet = modelformset_factory(
        DetalleRequisicion, form=FormularioCumplirDetalleRequisicion,
        min_num=requisicion.detallerequisicion_set.count(), extra=0,
        validate_min=True, can_delete=False
    )

    if request.method == 'POST':
        if requisicion.get_rastreo() == Requisicion.DATA_SET['solicitante']:
            queryset = requisicion.detallerequisicion_set.all()
        else:
            queryset = requisicion.detallerequisicion_set.filter(forma_pago=DetalleRequisicion.CREDITO)
        form = DetalleRequisicionFormSet(data=request.POST, prefix='detallerequisicion_set', queryset=queryset)

        if form.is_valid():
            form.save()
            if not requisicion.detallerequisicion_set.filter(cumplida=False):
                historial = requisicion.crear_historial(estado=Historial.APROBADA, empleado=empleado)
                historial.save()
                requisicion.estado = Requisicion.TERMINADA
                requisicion.fecha_termina = timezone.now().date()
                requisicion.save()
                messages.success(
                    request, _('Ha culminado el proceso de la requisición NO.{} exitosamente'.format(requisicion.id))
                )
                return redirect(reverse('compras:ver_requisiciones_empleado'))
            messages.success(request, _('Se ha editado correctamente el estado de la requisición'))
            return redirect(reverse('compras:aprobar_requisiciones_empleado', args=(requisicion.id, )))
        else:
            messages.error(request, _('Ha ocurrido un error al enviar el formulario'))
    else:
        if requisicion.get_rastreo() == Requisicion.DATA_SET['solicitante']:
            queryset = requisicion.detallerequisicion_set.all()
        else:
            queryset = requisicion.detallerequisicion_set.filter(forma_pago=DetalleRequisicion.CREDITO)
        form = DetalleRequisicionFormSet(prefix='detallerequisicion_set', queryset=queryset)

    data['formset_detalles'] = form
    data['requisicion'] = requisicion

    return render(request, 'compras/aprobar_requisiciones_empleado.html', data)


@waffle_switch('compras')
@login_empleado('is_jefe_administrativo')
def informes_totales_area_departamento(request):
    """
    Informe para ver los totales agrupados de acuerdo a una fecha, un área o departamento
    de las requisiciones
    """

    data = {}

    if request.method == 'POST':
        form = FormularioInformeTotalesAreaDerpartamento(data=request.POST)

        if form.is_valid():
            fecha_inicial = form.cleaned_data['fecha_inicial']
            fecha_final = form.cleaned_data['fecha_final']

            query = Requisicion.objects.filter(
                estado=Requisicion.TERMINADA,
                fecha_termina__range=(fecha_inicial, fecha_final)
            ).select_related('empleado')  # .prefetch_related('empleado__areas__departamento')
            _data = {}
            for requisicion in query:
                if requisicion.empleado.areas.first().departamento.nombre not in _data:
                    _data[requisicion.empleado.areas.first().departamento.nombre] = requisicion.get_total()
                else:
                    _data[requisicion.empleado.areas.first().departamento.nombre] += requisicion.get_total()

            data['requisiciones'] = _data
            if len(_data) == 0:
                messages.warning(request, _('No se han encontrado resultados para ese rango de fecha'))
        else:
            messages.error(request, _('Ha ocurrido un error al enviar el mensaje'))

    else:
        form = FormularioInformeTotalesAreaDerpartamento()

    data['form'] = form

    return render(request, 'compras/informes_totales_area_departamento.html', data)


@waffle_switch('compras')
@login_empleado('is_jefe_financiero')
def imprimir_requisicion(request, id_requisicion):
    """
    Vista para imprimir el detalle de una requisicion
    """

    empleado = get_object_or_404(Empleado, usuario=request.user)
    requisicion = get_object_or_404(Requisicion, id=id_requisicion)

    if not empleado.is_jefe_financiero or requisicion.get_rastreo() not in [
        Requisicion.DATA_SET['financiero'], Requisicion.DATA_SET['espera_presupuesto']
    ]:
        return redirect('sin_permiso')

    data = {'requisicion': requisicion}

    return render(request, 'compras/imprimir_requisicion.html', data)
