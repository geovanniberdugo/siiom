import json
# Django Package
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic import ListView
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory, modelformset_factory
from django.contrib.auth.decorators import permission_required, login_required

# Third Apps
from waffle.decorators import waffle_switch
from braces.views import LoginRequiredMixin, GroupRequiredMixin

# Locale Apps
from organizacional.models import Area, Empleado
from common.decorators import POST, GET
from .models import (
    Registro, Documento, PalabraClave, TipoDocumento,
    SolicitudRegistro, SolicitudCustodiaDocumento
)
from .forms import (
    FormularioRegistroDocumento, FormularioDocumentos, FormularioCustodiaDocumento,
    FormularioBusquedaRegistro, TipoDocumentoForm, PalabraClaveForm, FormularioComentario,
    FormularioEditarRegistroDocumento, FormularioEdicionDocumentos
)


@waffle_switch('gestion_documental')
@permission_required('gestion_documental.add_registro')
@transaction.atomic
def ingresar_registro(request):
    """
    Vista de captura de datos para los registros del sistema de gestión.
    """

    # Define FormSet
    DocumentosFormSet = inlineformset_factory(
        Registro, Documento, fk_name='registro', form=FormularioDocumentos,
        min_num=1, extra=0, validate_min=True, can_delete=False
    )

    if request.method == 'POST':
        form = FormularioRegistroDocumento(data=request.POST)

        if form.is_valid():
            registro = form.save(commit=False)
            form_documentos = DocumentosFormSet(request.POST, request.FILES, instance=registro)
            # Si ambos documentos son validos
            if form_documentos.is_valid():
                registro.save()
                # Se extraen las palabras que vienen del formulario y se separan por coma en una lista
                palabras = form.cleaned_data['palabras'].split(',')
                # Se buscan las palabras recursivamente
                for palabra in palabras:
                    # Se busca, si no existe la palabra se crea
                    if palabra != '':
                        palabra_clave, created = PalabraClave.objects.get_or_create(
                            nombre__iexact=palabra, defaults={'nombre': palabra}
                        )

                        if palabra_clave not in registro.palabras_claves.all():
                            registro.palabras_claves.add(palabra_clave)
                # se guarda el registro
                registro.save()
                # Se guardan los documentos
                form_documentos.save()
                messages.success(request, _("Se ha creado el registro exitosamente"))
                # Todo Correcto
                return redirect('sgd:ingresar_registro')
            else:
                # Error en el formulario de documentos
                messages.error(request, _("Por favor verifique los documentos enviados"))
        else:
            # Error en el primer formulario del registro general
            form_documentos = DocumentosFormSet(queryset=Documento.objects.none(), data=request.POST)
            form_documentos.is_valid()
            messages.error(request, _("Se han encontrado errores en el formulario"))
    else:
        form = FormularioRegistroDocumento()
        form_documentos = DocumentosFormSet(queryset=Documento.objects.none())

    data = {'form': form, 'form_documentos': form_documentos}

    return render(request, 'gestion_documental/ingresar_registro.html', data)


@waffle_switch('gestion_documental')
@permission_required('organizacional.es_administrador_sgd')
@transaction.atomic
def editar_registro(request, id_registro):
    """
    Vista de edición de registros
    """
    # se obtiene el registro
    registro = get_object_or_404(Registro, pk=id_registro)
    # se crea el formset de los documentos
    DocumentosFormSet = modelformset_factory(
        Documento, form=FormularioEdicionDocumentos,
        min_num=1, extra=0, validate_min=True, can_delete=True
    )

    if request.method == 'POST':
        # se instancian los dos formularios
        form = FormularioEditarRegistroDocumento(data=request.POST, instance=registro)
        form_documentos = DocumentosFormSet(request.POST, request.FILES)
        # si ammbos son validos
        if form.is_valid() and form_documentos.is_valid():
            registro = form.save(commit=False)
            # formset = form_documentos.save(commit=False)
            # se sacan las palabras que tiene actualmente el registro
            _palabras_anteriores = [x.nombre for x in registro.palabras_claves.all()]
            # se sacan las palabras que vienen del formulario
            palabras = form.cleaned_data['palabras'].split(',')
            # Se buscan las palabras recursivamente
            for palabra in palabras:
                # si no esta en la de palabras anteriores hace lo siguiente
                if palabra not in _palabras_anteriores:
                    # Se busca, si no existe la palabra se crea
                    if palabra != '':
                        palabra_clave, created = PalabraClave.objects.get_or_create(
                            nombre__iexact=palabra, defaults={'nombre': palabra}
                        )
                        if palabra_clave not in registro.palabras_claves.all():
                            registro.palabras_claves.add(palabra_clave)
            # si hay palabras anteriores
            if _palabras_anteriores:
                # se crea un set de palabras que sobran para luego eliminar las que no se usan
                eliminar = set(_palabras_anteriores) - set(palabras)
                if eliminar:
                    # Funciona asi:
                    # tienes una lista 'a' y una 'b':
                    # a = [1,2,3]
                    # b = [2,3,4]
                    # c = set(a) - set(b)
                    # entonces c = [1]
                    # solo las palabras a eliminar
                    for palabra in eliminar:
                        palabra_clave = PalabraClave.objects.get(nombre__iexact=palabra)
                        registro.palabras_claves.remove(palabra_clave)
            registro.modificado_por = request.user.empleado
            registro.ultima_modificacion = timezone.datetime.now().date()
            registro.save()
            for form_b in form_documentos:
                if form_b.cleaned_data.get('DELETE', False) and hasattr(form_b.instance, 'pk'):
                    if form_b.instance.id is not None or form_b.instance.pk is not None:
                        form_b.instance.delete()
                    continue
                form_b.instance.registro = registro
                if not form_b.cleaned_data.get('archivo', False) \
                   or not form_b.cleaned_data.get('tipo_documento', False):
                    continue
                form_b.save()
            messages.success(request, _("Se ha editado correctamente el registro"))
            return redirect(reverse('sgd:editar_registro', args=(registro.id, )))
        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
    else:
        form = FormularioEditarRegistroDocumento(instance=registro)
        form_documentos = DocumentosFormSet(queryset=registro.documentos.all())

    data = {'form': form, 'registro': registro, 'form_documentos': form_documentos}

    return render(request, 'gestion_documental/editar_registro.html', data)


@login_required
@csrf_exempt
@GET
def palabras_claves_json(request):
    """
    Vista que devuelve una lista con los nombres de las palabras claves para typeahead.js
    """

    palabras = PalabraClave.objects.all()
    response = [p.nombre for p in palabras]

    return HttpResponse(json.dumps(response), content_type="application/javascript")


@login_required
@csrf_exempt
@POST
def area_tipo_documento_json(request):
    """
    Retorna los tipos de documentos pertenecientes a cada area
    """

    if request.method == 'POST':
        area = get_object_or_404(Area, pk=request.POST['id_area'])
        response = [{'id': tipo.id, 'tipo': tipo.nombre} for tipo in area.tipos_documento.all()]

        return HttpResponse(json.dumps(response), content_type="application/json")


@login_required
@csrf_exempt
@POST
def empleado_area_json(request):
    """
    Retorna las areas en la que pertenece cada empleado
    """

    if request.method == 'POST':
        empleado = get_object_or_404(Empleado, pk=request.POST['id_solicitante'])
        response = [{'id': area.id, 'tipo': area.nombre} for area in empleado.areas.all()]

        return HttpResponse(json.dumps(response), content_type="application/json")


@waffle_switch('gestion_documental')
@login_required
def busqueda_registros(request):
    """
    Vista para realizar la busqueda de registros
    """

    data = {}
    empleado = get_object_or_404(Empleado, usuario=request.user)

    if request.method == 'POST':
        if 'solicitar_registro' in request.POST and 'solicitud' in request.POST:
            id_registro = request.POST['solicitud']
            registro = Registro.objects.get(id=id_registro)
            solicitud = SolicitudRegistro()
            solicitud.registro = registro
            solicitud.usuario_solicita = request.user.empleado
            solicitud.estado = SolicitudRegistro.PENDIENTE
            solicitud.save()

            return redirect('sgd:busqueda_registros')

        else:
            form = FormularioBusquedaRegistro(data=request.POST, empleado=empleado)

            if form.is_valid():
                tipo_documento = form.cleaned_data['tipo_documento']
                fecha_inicial = form.cleaned_data['fecha_inicial']
                fecha_final = form.cleaned_data['fecha_final']
                # Las palabras claves que vienen del formulario ya vienen en una lista
                palabras_claves = form.cleaned_data['palabras_claves']
                # Se dividen las palabras de la descripcion para hacer una mejor busqueda individual
                descripcion = form.cleaned_data['descripcion'].split(' ')

                # se buscan los registros en base a la fecha y al tipo de documento principalmente
                registros = Registro.objects.filter(
                    fecha__range=(fecha_inicial, fecha_final),
                    documentos__tipo_documento=tipo_documento,
                )

                # si hay palabras claves se filtran por las palabras claves
                if palabras_claves:
                    registros = registros.filter(palabras_claves__in=palabras_claves)

                # queries = [Q(descripcion__icontains=descript) for descript in descripcion]

                # este seria el filtro por descripcion
                string_to_eval = ""
                link = "Q(descripcion__icontains='%s')"
                pipe = " | "

                # El siguiente ciclo se hace para enviar un queryset con "OR" de otro mododo
                # Quedaria sentencias para queries de " AND "

                # Ciclo para crear los querysets a partir de strings que luego seran evaluados
                for x in range(len(descripcion)):
                    # cuando llegue al final del ciclo no agregara el pipe " | "
                    if x == len(descripcion) - 1:
                        string_to_eval += (link % descripcion[x])
                    # Mientras este en rango se agrega el pipe en la cadena para formar el " OR "
                    else:
                        string_to_eval += (link % descripcion[x]) + pipe

                # registros = registros.filter(*queries)
                # Se evaluan los registros y se hace el filtro
                registros = registros.filter(eval(string_to_eval)).distinct()

                # se añaden los registros a los datos que seran enviados a la vista,
                # que estan previamente cargados
                data['registros'] = registros.prefetch_related('documentos')

                messages.success(request, _("Se han encontrado %d resultados") % registros.count())
            else:
                # Ocurrieron errores
                messages.error(request, _("Ha ocurrido un error al enviar el formulario"))
    else:
        form = FormularioBusquedaRegistro(empleado=empleado)

    # se empaqueta el formulario
    data['form'] = form

    return render(request, 'gestion_documental/busqueda_registros.html', data)


class TipoDocumentoCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    """CreateView for TipoDocumentoCreateView"""
    model = TipoDocumento
    form_class = TipoDocumentoForm
    # fields = ['nombre', 'codigo']
    success_url = reverse_lazy('sgd:crear_tipo_documento')
    template_name = 'gestion_documental/crear_tipo_documento.html'
    group_required = ['Administrador SGD']

    def form_valid(self, form):
        messages.success(self.request, _("Se ha creado exitosamente el Tipo de Documento"))
        return super(TipoDocumentoCreateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Ha ocurrido un error al enviar el formulario"))
        return super(TipoDocumentoCreateView, self).form_invalid(form)

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        context['accion'] = 'Crear'
        # context['tipo'] = 'Area'
        return self.response_class(
            request=self.request,
            template=self.get_template_names(),
            context=context,
            **response_kwargs
        )


class TipoDocumentoUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    """UpdateView for TipoDocumentoUpdateView"""
    model = TipoDocumento
    form_class = TipoDocumentoForm
    # success_url = reverse_lazy('organizacional:editar_Departamento')
    template_name = 'gestion_documental/crear_tipo_documento.html'
    group_required = ['Administrador SGD']

    def form_valid(self, form):
        messages.success(self.request, _("Se ha editado exitosamente el Área"))
        self.success_url = reverse_lazy('sgd:editar_tipo_documento', args=(form.instance.id, ))
        return super(TipoDocumentoUpdateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Ha ocurrido un error al enviar el formulario"))
        return super(TipoDocumentoUpdateView, self).form_invalid(form)

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        context['accion'] = _('Editar')
        return self.response_class(
            request=self.request,
            template=self.get_template_names(),
            context=context,
            **response_kwargs
        )


class ListaTipoDocumentosView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """Devuelve una lista de areas ingresadas en el sistema."""
    model = TipoDocumento
    template_name = 'gestion_documental/listar_tipo_documentos.html'
    group_required = ['Administrador SGD']


class PalabraClaveCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    """CreateView for PalabraClaveCreateView"""
    model = PalabraClave
    form_class = PalabraClaveForm
    # fields = ['nombre', 'codigo']
    success_url = reverse_lazy('sgd:crear_palabra_clave')
    template_name = 'gestion_documental/crear_palabra_clave.html'
    group_required = ['Administrador SGD']

    def form_valid(self, form):
        messages.success(self.request, _("Se ha creado exitosamente la Palabra Clave"))
        return super(PalabraClaveCreateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Ha ocurrido un error al enviar el formulario"))
        return super(PalabraClaveCreateView, self).form_invalid(form)

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        context['accion'] = 'Crear'
        # context['tipo'] = 'Area'
        return self.response_class(
            request=self.request,
            template=self.get_template_names(),
            context=context,
            **response_kwargs
        )


class PalabraClaveUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    """UpdateView for PalabraClaveUpdateView"""
    model = PalabraClave
    form_class = PalabraClaveForm
    # success_url = reverse_lazy('organizacional:editar_Departamento')
    template_name = 'gestion_documental/crear_palabra_clave.html'
    group_required = ['Administrador SGD']

    def form_valid(self, form):
        messages.success(self.request, _("Se ha editado exitosamente el Área"))
        self.success_url = reverse_lazy('sgd:editar_palabra_clave', args=(form.instance.id, ))
        return super(PalabraClaveUpdateView, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Ha ocurrido un error al enviar el formulario"))
        return super(PalabraClaveUpdateView, self).form_invalid(form)

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        context['accion'] = _('Editar')
        return self.response_class(
            request=self.request,
            template=self.get_template_names(),
            context=context,
            **response_kwargs
        )


class ListaPalabrasClavesView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    """Devuelve una lista de areas ingresadas en el sistema."""
    model = PalabraClave
    template_name = 'gestion_documental/listar_palabras_claves.html'
    group_required = ['Administrador SGD']


@waffle_switch('gestion_documental')
@permission_required('gestion_documental.add_registro')
def lista_solicitudes(request):
    """
    Vista que le permite a un usuario digitador ver las solicitudes de
    registros/documentos fisicos
    """

    solicitudes = SolicitudRegistro.objects.ultimos_dos_meses()
    form = FormularioComentario()

    if request.method == 'POST':
        if 'cambia_estado_proceso' in request.POST:
            form = FormularioComentario(data=request.POST)
            id_solicitud = request.POST['solicitud']
            solicitud = get_object_or_404(SolicitudRegistro, pk=id_solicitud)
            solicitud.estado = SolicitudRegistro.ENTREGADO_DIGITADOR
            solicitud.usuario_autoriza = request.user.empleado
            if 'comentario' in request.POST:
                if form.is_valid():
                    solicitud.comentario = form.cleaned_data['comentario']
            solicitud.save()
            return redirect('sgd:lista_solicitudes')
        if 'cambia_estado_entregado' in request.POST:
            id_solicitud = request.POST['solicitud']
            solicitud = get_object_or_404(SolicitudRegistro, pk=id_solicitud)
            solicitud.estado = SolicitudRegistro.DEVUELTO_CONSULTA
            solicitud.fecha_devolucion = timezone.datetime.now().date()
            solicitud.usuario_autoriza = request.user.empleado
            solicitud.save()
            return redirect('sgd:lista_solicitudes')

    data = {'solicitudes': solicitudes, 'form': form}

    return render(request, 'gestion_documental/lista_solicitudes.html', data)


@waffle_switch('gestion_documental')
@permission_required('gestion_documental.add_registro')
def custodia_documentos(request):
    """
    Vista para recibir custodias de documentos
    """

    if request.method == 'POST':

        form = FormularioCustodiaDocumento(data=request.POST)
        if form.is_valid():
            custodia = form.save(commit=False)
            custodia.usuario_recibe = request.user.empleado
            custodia.save()
            messages.success(request, _("Se ha creado la solicitud de custodia de documentos satisfactoriamente"))
            return redirect(reverse('sgd:custodia_documentos'))
        else:
            messages.error(request, _("Ha ocurrido un error al enviar el formulario"))

    else:
        form = FormularioCustodiaDocumento()

    data = {'form': form}

    return render(request, 'gestion_documental/custodia_documentos.html', data)


@waffle_switch('gestion_documental')
@permission_required('gestion_documental.add_registro')
def lista_custodias_documentos(request):
    """
    Listado de las custodias de documentos
    """

    if request.method == 'POST':
        if 'finalizar' in request.POST:
            id_custodia = request.POST.get('id_custodia', None)
            if id_custodia:
                custodia_documento = get_object_or_404(SolicitudCustodiaDocumento, pk=id_custodia)
                if custodia_documento.estado == SolicitudCustodiaDocumento.PROCESO:
                    custodia_documento.estado = SolicitudCustodiaDocumento.REALIZADO
                elif custodia_documento.estado == SolicitudCustodiaDocumento.PENDIENTE:
                    custodia_documento.estado = SolicitudCustodiaDocumento.PROCESO
                custodia_documento.save()
            else:
                messages.error(request, _("Ha ocurrido un error inesperado"))

    custodias = SolicitudCustodiaDocumento.objects.all()[:30]

    data = {'custodias': custodias}

    return render(request, 'gestion_documental/lista_custodias.html', data)


@waffle_switch('gestion_documental')
@permission_required('gestion_documental.add_registro')
def historial_registros(request):
    """
    Vista que muestra el historial de todos los registros con sus documentos
    """
    registros = Registro.objects.all().select_related(
        'area__departamento'
    ).prefetch_related('documentos').order_by('-fecha')
    data = {'registros': registros}
    return render(request, 'gestion_documental/historial_registros.html', data)


@waffle_switch('gestion_documental')
@permission_required('organizacional.es_administrador_sgd')
@transaction.atomic
def eliminar_registro(request, id_registro):
    """
    Vista para el administrador que elimina los registros
    """
    registro = get_object_or_404(Registro, pk=id_registro)
    redirect_to = request.META.get('HTTP_REFERER', None)
    data = {'registro': registro, 'redirect': redirect_to}

    if request.method == 'POST':
        if 'eliminar' in request.POST:
            registro.delete()
            return redirect(reverse('sgd:busqueda_registros'))

    return render(request, 'gestion_documental/eliminar_registro.html', data)
