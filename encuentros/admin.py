from django.contrib import admin
from .models import Encontrista, Encuentro


class EncuentroAdmin(admin.ModelAdmin):
    list_display = ('fecha_inicial', 'fecha_final', 'hotel', 'coordinador', 'tesorero')
    list_editable = ('fecha_final', 'hotel', 'coordinador', 'tesorero')
    list_filter = ('grupos__red', )
    search_field = ('coordinador', 'hotel', 'direccion')


class EncontristaAdmin(admin.ModelAdmin):
    list_display = ('identificacion', 'primer_nombre', 'primer_apellido', 'talla', 'grupo', 'genero')
    list_editable = ('primer_nombre', 'primer_apellido', 'talla', 'genero')
    list_filter = ('primer_nombre', 'primer_apellido', 'talla', 'genero')
    search_field = ('identificacion', 'primer_nombre', 'primer_apellido', 'talla', 'grupo', 'genero')


admin.site.register(Encuentro, EncuentroAdmin)
admin.site.register(Encontrista, EncontristaAdmin)
