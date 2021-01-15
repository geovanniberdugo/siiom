'''
Created on Apr 1, 2011

@author: Migue
'''
# Django imports
from django.contrib import admin
from import_export import resources
from treebeard.admin import TreeAdmin
from import_export.admin import ImportExportModelAdmin
from miembros import models as miembros_models
from .models import (
    Red, Grupo, ReunionGAR, ReunionDiscipulado, Predica, AsistenciaDiscipulado, HistorialEstado, Enseñanza
)

class RedResource(resources.ModelResource):

    class Meta:
        model = Red

@admin.register(Red)
class GrupoAdmin(ImportExportModelAdmin):
    resource_class = RedResource

class LiderInline(admin.TabularInline):
    model = miembros_models.Miembro
    verbose_name_plural = 'Lideres'
    fk_name = 'grupo_lidera'
    verbose_name = 'Lider'
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "grupo":
            kwargs["queryset"] = Grupo.objects.prefetch_related('lideres').all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class GrupoResource(resources.ModelResource):

    class Meta:
        model = Grupo

@admin.register(Grupo)
class GrupoAdmin(ImportExportModelAdmin):
    resource_class = GrupoResource
    search_fields = ['nombre', 'direccion', 'lideres__nombre', 'lideres__cedula']
    list_display = ('__str__', 'get_estado_display', 'red')
    list_filter = ('red', 'historiales__estado')
    list_select_related = ('red', )
    inlines = [LiderInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('lideres')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Grupo.objects.prefetch_related('lideres').all()        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class GrupoTree(Grupo):
    class Meta:
        proxy = True


@admin.register(GrupoTree)
class GrupoTreeAdmin(TreeAdmin):
    pass


@admin.register(ReunionGAR)
class ReunionGARAdmin(admin.ModelAdmin):
    search_fields = ['grupo__nombre']


class AsistenciaDiscipuladoInline(admin.TabularInline):
    model = AsistenciaDiscipulado
    verbose_name = 'Asistencia'
    verbose_name_plural = 'Asistencia'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'miembro', 'reunion', 'reunion__grupo'
        )

    def get_formset(self, request, obj=None, **kwargs):
        self.parent = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'miembro':
            if self.parent:
                qs = self.parent.grupo.discipulos
            else:
                qs = miembros_models.Miembro.objects.lideres()
            kwargs['queryset'] = qs.order_by('nombre', 'primer_apellido')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(ReunionDiscipulado)
class ReunionDiscipuladoAdmin(admin.ModelAdmin):
    inlines = [AsistenciaDiscipuladoInline]
    list_display = ('id', 'grupo', 'predica', 'fecha')
    list_filter = ('predica', )
    search_fields = ['grupo__lideres__nombre', 'grupo__lideres__primer_apellido']
    readonly_fields = ('fecha', )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('grupo__historiales', 'grupo__lideres')
    
    def get_form(self, request, obj=None, **kwargs):
        self.obj = obj
        return super().get_form(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'grupo':
            qs = Grupo.objects.pueden_reportar_discipulado().prefetch_related('lideres')
            if self.obj:
                qs = qs | Grupo.objects.filter(id=self.obj.grupo_id)
            kwargs['queryset'] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    search_fields = ['grupo__lideres__nombre', 'grupo__lideres__primer_apellido', 'grupo__lideres__cedula']
    readonly_fields = ('fecha', )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('grupo__lideres')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'grupo':
            kwargs['queryset'] = Grupo._objects.prefetch_related('lideres')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Predica)
admin.site.register(Enseñanza)
