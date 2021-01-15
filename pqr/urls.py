from django.urls import re_path
from . import views, api

app_name = 'pqr'
urlpatterns = [
    re_path(r'^$', views.nuevo_caso, name="nuevo_caso"),
    re_path(r'^sc/$', views.nuevo_caso_servicio_cliente, name="nuevo_caso_servicio_cliente"),
    re_path(r'^casos/$', views.ver_casos_servicio_cliente, name="ver_casos_servicio_cliente"),
    re_path(r'^caso/(?P<id_caso>\d+)/$', views.ver_bitacora_caso, name="ver_bitacora_caso"),
    re_path(r'^editar/(?P<id_caso>\d+)/$', views.editar_caso, name="editar_caso"),
    re_path(r'^casos/empleado/$', views.ver_casos_empleado, name="ver_casos_empleado"),
    re_path(r'^casos/comercial/$', views.ver_casos_jefe_comercial, name="ver_casos_jefe_comercial"),
    re_path(r'^casos/presidencia/$', views.ver_casos_presidencia, name="ver_casos_presidencia"),
    re_path(r'^download/file/(?P<id_documento>\d+)/$', views.descargar_archivos, name="descargar_archivos"),
    re_path(r'^upload/file/(?P<id_caso>\d+)/$', views.subir_archivo_como_bitacora, name="subir_archivo_como_bitacora"),
    re_path(r'^api/empleados/(?P<id_caso>\d+)/$', api.empleados_nombres_views, name="empleados_nombres_views_api"),
]
