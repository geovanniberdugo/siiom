from django import forms
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField

from . import models, forms
from miembros.models import Miembro
from common.forms import ArrayFieldSelectMultiple


class ArrayFieldListFilter(admin.SimpleListFilter):
    """Filtro por días"""

    title = 'Días'
    parameter_name = 'dia'

    def lookups(self, request, model_admin):
        # keywords = models.Curso.objects.values_list('dia', flat=True)
        keywords = models.Curso.DIAS_SEMANA
        keywords = sorted(set(keywords))
        return keywords

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value:
            queryset = queryset.filter(dia__contains=[lookup_value])
        return queryset


class CursoAdmin(admin.ModelAdmin):
    list_filter = (ArrayFieldListFilter, )

    formfield_overrides = {
        ArrayField: {'widget': ArrayFieldSelectMultiple},
    }

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "profesor":
            kwargs["queryset"] = Miembro.objects.maestros()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        kwargs['widgets'] = {
            'dia': ArrayFieldSelectMultiple(
                choices=models.Curso.DIAS_SEMANA, attrs={'class': 'selectpicker'})
        }
        return super().get_form(request, obj=obj, **kwargs)


admin.site.register(models.Salon)
admin.site.register(models.Abono)
admin.site.register(models.Modulo)
admin.site.register(models.Sesion)
admin.site.register(models.Materia)
admin.site.register(models.Matricula)
admin.site.register(models.Estudiante)
admin.site.register(models.Curso, CursoAdmin)
