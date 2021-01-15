from django.urls import re_path
from . import views, api

app_name = 'instituto'
urlpatterns = [
    # url(r'^/$', views.lista_estudiantes_sesion, name="a"),
    re_path(r'^materias/$', views.MateriaListView.as_view(), name='materias'),
    re_path(r'^materias/new/$', views.MateriaCreateView.as_view(), name='crear-materia'),
    re_path(r'^materias/(?P<pk>\d+)/$', views.MateriaUpdateView.as_view(), name='editar-materia'),
    re_path(r'^modulos/(?P<materia_pk>\d+)/$', views.ModuloListView.as_view(), name='modulos'),
    re_path(r'^modulos/(?P<materia_pk>\d+)/new/$', views.ModuloCreateView.as_view(), name='crear-modulo'),
    re_path(r'^modulos/(?P<pk>\d+)/edit/$', views.ModuloUpdateView.as_view(), name='editar-modulo'),
    re_path(r'^sesiones/(?P<modulo_pk>\d+)/$', views.SesionListView.as_view(), name='sesiones'),
    re_path(r'^sesiones/(?P<modulo_pk>\d+)/new/$', views.SesionCreateView.as_view(), name='crear-sesion'),
    re_path(r'^sesiones/(?P<pk>\d+)/edit/$', views.SesionUpdateView.as_view(), name='editar-sesion'),
    re_path(r'^salones/$', views.SalonListView.as_view(), name='salones'),
    re_path(r'^salones/new/$', views.SalonCreateView.as_view(), name='crear-salon'),
    re_path(r'^salones/(?P<pk>\d+)/edit/$', views.SalonUpdateView.as_view(), name='editar-salon'),
    re_path(r'^cursos/$', views.CursoCreateView.as_view(), name="crear-curso"),
    re_path(r'^reporte_instituto/$', views.reporte_instituto, name="reporte-instituto"),
    
    re_path(r'^seguimiento/$', views.SeguimientoEstudiantesView.as_view(), name='seguimiento-estudiantes'),
    
    
    re_path(r'^api/cursos/salon/(?P<pk>\d+)/$', api.curso_by_month, name="api-cursos-salon"),
    re_path(r'^api/cursos/salon/(?P<pk>\d+)/disponibilidad/$', api.verifica_disponibilidad_curso, name="api-disponibilidad-cursos-salon"),
]
