from django.urls import re_path
from . import views, api

app_name = 'encuentros'
urlpatterns = [
    re_path(r'^nuevo/$', views.crear_encuentro, name="crear_encuetro"),
    re_path(r'^encuentros/$', views.listar_encuentros, name="listar_encuentros"),
    re_path(r'^agregar_encontrista/(?P<id_encuentro>\d+)/$', views.agregar_encontrista, name="agregar_encontrista"),
    re_path(r'^editar_encuentro/(?P<id_encuentro>\d+)/$', views.editar_encuentro, name="editar_encuentro"),
    re_path(r'^listar_encontristas/(?P<id_encuentro>\d+)/$', views.listar_encontristas, name="listar_encontristas"),
    re_path(r'^editar_encontrista/(?P<id_encontrista>\d+)/$', views.editar_encontrista, name="editar_encontrista"),
    re_path(r'^borrar_encontrista/(?P<id_encontrista>\d+)/$', views.borrar_encontrista, name="borrar_encontrista"),
    re_path(r'^asistencia_encuentro/(?P<id_encuentro>\d+)/$', views.asistencia_encuentro, name="asistencia_encuentro"),

    re_path(r'^obtener_grupos/$', api.obtener_grupos, name="obtener_grupos"),
    re_path(
        r'^obtener_coordinadores_tesoreros/$',
        api.obtener_coordinadores_tesoreros,
        name="obtener_coordinadores_tesoreros"
    ),
]
