from django.contrib import admin

from .models import PalabraClave, TipoDocumento, Registro, Documento, SolicitudRegistro

admin.site.register(PalabraClave)
admin.site.register(TipoDocumento)
admin.site.register(Registro)
admin.site.register(Documento)
admin.site.register(SolicitudRegistro)
