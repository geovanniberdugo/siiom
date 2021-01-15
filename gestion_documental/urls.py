from django.urls import re_path
from . import views

app_name = 'gestion_documental'
urlpatterns = [
    re_path(r'^ingresar_registro/$', views.ingresar_registro, name="ingresar_registro"),
    re_path(r'^busqueda_registros/$', views.busqueda_registros, name="busqueda_registros"),
    re_path(r'^palabras_claves_json/$', views.palabras_claves_json, name="palabras_claves_json"),
    re_path(r'^area_tipo_documento_json/$', views.area_tipo_documento_json, name="area_tipo_documento_json"),
    re_path(r'^empleado_area_json/$', views.empleado_area_json, name="empleado_area_json"),
    re_path(r'^crear_tipo_documento/$', views.TipoDocumentoCreateView.as_view(), name="crear_tipo_documento"),
    re_path(r'^editar_tipo_documento/(?P<pk>\d+)/$', views.TipoDocumentoUpdateView.as_view(), name="editar_tipo_documento"),
    re_path(r'^crear_palabra_clave/$', views.PalabraClaveCreateView.as_view(), name="crear_palabra_clave"),
    re_path(r'^editar_palabra_clave/(?P<pk>\d+)/$', views.PalabraClaveUpdateView.as_view(), name="editar_palabra_clave"),
    re_path(r'^listar_tipo_documentos/$', views.ListaTipoDocumentosView.as_view(), name="listar_tipo_documentos"),
    re_path(r'^listar_palabras_claves/$', views.ListaPalabrasClavesView.as_view(), name="listar_palabras_claves"),
    re_path(r'^listado_solicitudes/$', views.lista_solicitudes, name="lista_solicitudes"),
    re_path(r'^custodia_documentos/$', views.custodia_documentos, name="custodia_documentos"),
    re_path(r'^lista_custodia_documentos/$', views.lista_custodias_documentos, name="lista_custodias_documentos"),
    re_path(r'^historial_registros/$', views.historial_registros, name="historial_registros"),
    re_path(r'^editar_registro/(?P<id_registro>\d+)/$', views.editar_registro, name="editar_registro"),
    re_path(r'^eliminar_registro/(?P<id_registro>\d+)/$', views.eliminar_registro, name="eliminar_registro"),
]
