from django.urls import re_path
from . import views

app_name = 'organizacional'
urlpatterns = [
    re_path(r'^areas_departamento_json/$', views.areas_departamento_json, name="areas_departamento_json"),
    re_path(r'^crear_area/$', views.AreaCreateView.as_view(), name="crear_area"),
    re_path(r'^editar_area/(?P<pk>\d+)/$', views.AreaUpdateView.as_view(), name="editar_area"),
    re_path(r'^listar_areas/$', views.ListaAreasView.as_view(), name="listar_areas"),
    re_path(r'^crear_departamento/$', views.DepartamentoCreateView.as_view(), name="crear_departamento"),
    re_path(r'^editar_departamento/(?P<pk>\d+)/$', views.DepartamentoUpdateView.as_view(), name="editar_departamento"),
    re_path(r'^listar_departamentos/$', views.ListaDepartamentosView.as_view(), name="listar_departamentos"),
    re_path(r'^editar_empleado/(?P<id_empleado>\d+)/$', views.editar_empleado, name="editar_empleado"),
    re_path(r'^empleados/$', views.listar_empleados, name="empleados_listar"),
    re_path(r'^empleados/nuevo/$', views.crear_empleado, name="empleado_nuevo"),
]
