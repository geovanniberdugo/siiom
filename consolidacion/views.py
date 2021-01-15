from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Visita
from .forms import VisitaForm, FormularioAsignarGrupoVisita
from common.forms import FormularioRangoFechas
from miembros.models import Miembro
from grupos.models import Grupo, Red

import json


class VisitasCBVMixin(object):
    """
    Base de clases para visitas
    """

    model = Visita

    def has_permission(self):
        is_agent = self.request.user.has_perm('miembros.es_agente')
        is_admin = self.request.user.has_perm('miembros.es_administrador')

        return is_agent or is_admin

    def form_invalid(self, form):
        messages.error(self.request, _("Ha ocurrido un error al enviar el formulario"))
        return super(VisitasCBVMixin, self).form_invalid(form)

    def form_valid(self, form):
        messages.success(self.request, _("Visita guardada con exito"))
        return super(VisitasCBVMixin, self).form_valid(form)


class CrearVisitaView(LoginRequiredMixin, VisitasCBVMixin, PermissionRequiredMixin, CreateView):
    """
    CBV para crear visitas
    """
    form_class = VisitaForm
    template_name = 'consolidacion/visita_form.html'
    success_url = reverse_lazy('consolidacion:crear_visita')


class EditarVisitaView(LoginRequiredMixin, VisitasCBVMixin, PermissionRequiredMixin, UpdateView):
    """
    CBV para editar Visitas
    """
    form_class = VisitaForm
    template_name = 'consolidacion/visita_form.html'

    def form_valid(self, form):
        self.success_url = reverse_lazy('consolidacion:editar_visita', args=(form.instance.id,))
        return super(EditarVisita, self).form_valid(form)


def asignar_grupo_visitas_ajax(request):
    """
    Vista para asignar los grupos desde una llamada ajax
    """

    data = {}
    if request.method == 'POST':
        form = FormularioAsignarGrupoVisita(data=request.POST)

        if form.is_valid():
            grupo = form.cleaned_data.get('grupo')
            visita = form.cleaned_data.get('visita')

            visita.grupo = grupo
            visita.save()
            data = {
                'response_code': 200,
                'message': 'Visita Asignada a grupo (%s) exitosamente' % grupo.get_nombre(),
                'id_visita': visita.id
            }
        else:
            if settings.DEBUG:
                print(form.errors)
            data = {
                'response_code': 401,
                'message': 'Ocurrieron errores al enviar el formulario'
            }
    else:
        data = {
            'response_code': 405,
            'message': 'INVALID REQUEST'
        }
    return HttpResponse(json.dumps(data), content_type='application/json')


@login_required
@permission_required('miembros.es_administrador', raise_exception=True)
def asignar_grupo_visitas(request):
    """
    Vista para asignar a las visitas a un grupo
    """

    data = {}

    if request.method == 'POST':
        if 'visita[]' in request.POST:
            response = {}
            _removed_ids = []
            try:
                visitas = request.POST.getlist('visita[]')
                for visita in visitas:
                    try:
                        _visita = Visita.objects.get(id=visita)
                        _visita.retirado = True
                        _visita.save()
                        _removed_ids.append(_visita.id)
                    except Exception as exception:
                        response['error'] = exception.__str__()
                        response['response_code'] = 401
                if 'error' not in response:
                    response['message'] = 'SUCCESS'
                    response['response_code'] = 200
                    response['removed_ids'] = _removed_ids
            except Exception as exception:
                if settings.DEBUG:
                    print(exception)
                response['error'] = exception.__str__()
                response['response_code'] = 502

            return HttpResponse(json.dumps(response), content_type='application/json')

        else:
            form = FormularioRangoFechas(data=request.POST)

            if form.is_valid():
                fecha_inicial = form.cleaned_data['fecha_inicial']
                fecha_final = form.cleaned_data['fecha_final']

                visitas = Visita.objects.filter(
                    fecha_ingreso__range=(fecha_inicial, fecha_final),
                    retirado=False
                ).exclude(grupo__isnull=False)

                grupos = Grupo.objects.prefetch_related('lideres').select_related('red').activos()

                if visitas.exists():
                    data['visitas'] = visitas
                    data['redes'] = Red.objects.all()
                    data['grupos'] = grupos
                    messages.success(
                        request,
                        _('Se muestran %d visitas para el rango de fechas escogido' % visitas.count())
                    )
                else:
                    messages.warning(request, _('No se encontraron resultados para el rango de fecha escogido'))
            else:
                messages.error(request, _('Ha ocurrido un error al enviar el formulario'))
    else:
        form = FormularioRangoFechas()

    data['form'] = form

    return render(request, 'consolidacion/asignar_grupo_visitas.html', data)
