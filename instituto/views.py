from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, ListView, TemplateView, FormView

from waffle.decorators import waffle_switch

from common.mixins import ViewMessagesMixin, WaffleSwitchMixin
from . import models, forms

__author__ = 'German Alzate'


class MateriaCreateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, CreateView):
    """CreateView for materias."""

    model = models.Materia
    form_class = forms.MateriaForm
    success_url = reverse_lazy('instituto:crear-materia')
    template_name = 'instituto/crear_materia.html'
    waffle_switch = 'instituto'
    message_success = _('Se ha creado la materia con exito')


class MateriaUpdateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, UpdateView):
    """UpdateView for MateriaUpdateView."""

    model = models.Materia
    form_class = forms.MateriaForm
    template_name = 'instituto/crear_materia.html'
    waffle_switch = 'instituto'
    message_success = _('Se ha editado la materia con exito')

    def form_valid(self, form):
        self.success_url = reverse_lazy('instituto:editar-materia', args=(form.instance.id, ))
        return super().form_valid(form)


class MateriaListView(WaffleSwitchMixin, LoginRequiredMixin, ListView):
    """ListView for Materia."""

    model = models.Materia
    querset = models.Materia.objects.all()
    template_name = 'instituto/materias.html'
    waffle_switch = 'instituto'


class ModuloCreateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, CreateView):
    """CreateView for modulos."""

    model = models.Modulo
    form_class = forms.ModuloForm
    template_name = 'instituto/crear_modulo.html'
    materia_pk_url_kwarg = 'materia_pk'
    waffle_switch = 'instituto'
    message_success = _('Se ha creado el módulo con exito')

    def dispatch(self, request, *args, **kwargs):
        self.materia = get_object_or_404(models.Materia, pk=self.kwargs.get(self.materia_pk_url_kwarg))
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs['materia'] = self.materia
        return form_kwargs

    def get_context_data(self, **kwargs):
        kwargs['materia'] = self.materia
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse_lazy('instituto:crear-modulo', args=(self.materia.id, ))


class ModuloUpdateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, UpdateView):
    """UpdateView for modulos."""

    model = models.Modulo
    form_class = forms.ModuloForm
    template_name = 'instituto/crear_modulo.html'
    waffle_switch = 'instituto'
    message_success = _('Se ha editado el módulo con exito')

    def form_valid(self, form):
        self.success_url = reverse_lazy('instituto:editar-modulo', args=(form.instance.id, ))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['materia'] = self.get_object().materia
        return super().get_context_data(**kwargs)


class ModuloListView(WaffleSwitchMixin, LoginRequiredMixin, ListView):
    """ListView for Modulo."""

    model = models.Modulo
    template_name = 'instituto/modulos.html'
    materia_pk_url_kwarg = 'materia_pk'
    waffle_switch = 'instituto'

    def dispatch(self, request, *args, **kwargs):
        self.materia = get_object_or_404(models.Materia, pk=self.kwargs.get(self.materia_pk_url_kwarg))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        self.queryset = self.model.objects.filter(materia_id=self.materia.id)
        return super().get_queryset(*args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['materia'] = self.materia
        return super().get_context_data(**kwargs)


class SesionCreateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, CreateView):
    """CreateView for sesiones."""

    model = models.Sesion
    form_class = forms.SesionForm
    success_url = reverse_lazy('instituto:crear-sesion')
    template_name = 'instituto/crear_sesion.html'
    modulo_pk_url_kwarg = 'modulo_pk'
    waffle_switch = 'instituto'
    message_success = _('Se ha creado la sesión con exito')

    def dispatch(self, request, *args, **kwargs):
        self.modulo = get_object_or_404(models.Modulo, pk=self.kwargs.get(self.modulo_pk_url_kwarg))
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs['modulo'] = self.modulo
        return form_kwargs

    def get_context_data(self, **kwargs):
        kwargs['modulo'] = self.modulo
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse_lazy('instituto:crear-sesion', args=(self.modulo.id, ))


class SesionUpdateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, UpdateView):
    """UpdateView for sesiones."""

    model = models.Sesion
    form_class = forms.SesionForm
    template_name = 'instituto/crear_sesion.html'
    waffle_switch = 'instituto'
    message_success = _('Se ha editado la sesión con exito')

    def form_valid(self, form):
        self.success_url = reverse_lazy('instituto:editar-sesion', args=(form.instance.id, ))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        kwargs['modulo'] = self.get_object().modulo
        return super().get_context_data(**kwargs)


class SesionListView(WaffleSwitchMixin, LoginRequiredMixin, ListView):
    """ListView for Sesion."""

    model = models.Sesion
    template_name = 'instituto/sesiones.html'
    modulo_pk_url_kwarg = 'modulo_pk'
    waffle_switch = 'instituto'

    def dispatch(self, request, *args, **kwargs):
        self.modulo = get_object_or_404(models.Modulo, pk=self.kwargs.get(self.modulo_pk_url_kwarg))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        self.queryset = self.model.objects.filter(modulo_id=self.modulo.id)
        return super().get_queryset(*args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['modulo'] = self.modulo
        return super().get_context_data(**kwargs)


class SalonCreateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, CreateView):
    """CreateView for salones."""

    model = models.Salon
    form_class = forms.SalonForm
    success_url = reverse_lazy('instituto:crear-salon')
    template_name = 'instituto/crear_salon.html'
    waffle_switch = 'instituto'
    message_success = _('Se ha creado el salón con exito')


class SalonUpdateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, UpdateView):
    """UpdateView for salones."""

    model = models.Salon
    form_class = forms.SalonForm
    template_name = 'instituto/crear_salon.html'
    waffle_switch = 'instituto'
    message_success = _('Se ha editado la salón con exito')

    def form_valid(self, form):
        self.success_url = reverse_lazy('instituto:editar-sesion', args=(form.instance.id, ))
        return super().form_valid(form)


class SalonListView(WaffleSwitchMixin, LoginRequiredMixin, ListView):
    """ListView for Salon."""

    model = models.Salon
    template_name = 'instituto/salones.html'
    waffle_switch = 'instituto'


class CursoCreateView(WaffleSwitchMixin, LoginRequiredMixin, ViewMessagesMixin, CreateView):
    """CreateView for cursos."""

    model = models.Curso
    form_class = forms.CursoForm
    success_url = reverse_lazy('instituto:crear-curso')
    template_name = 'instituto/crear_curso.html'
    waffle_switch = 'instituto'
    message_success = _('Se ha creado el curso con éxito')

    def form_valid(self, form):
        form.instance.estado = models.Curso.ABIERTO
        return super().form_valid(form)


def lista_estudiantes_sesion(request):
    from django.shortcuts import render
    return render(request, 'lista_estudiantes_sesion.html', {})


@waffle_switch('instituto')
@permission_required('miembros.es_administrador', raise_exception=True)
def reporte_instituto(request):

    if request.method == 'POST':
        form = forms.ReporteInstitutoForm(data=request.POST)
        if form.is_valid():
            excel = form.get_excel()
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=reporte.xlsx'
            response.write(excel.read())
            return response

    else:
        form = forms.ReporteInstitutoForm()
    return render(request, 'instituto/reporte_instituto.html', {'form': form})


class SeguimientoEstudiantesView(WaffleSwitchMixin, LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Permite ingresar las notas y asistencia de los estudiantes de un curso."""
    
    waffle_switch = 'instituto'
    form_class = forms.SeguimientoEstudianteForm
    permission_required = 'instituto.add_seguimiento'
    template_name = 'instituto/seguimiento_estudiantes.html'