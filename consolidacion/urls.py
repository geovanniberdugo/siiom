from django.urls import re_path
from . import views

app_name = 'consolidacion'
urlpatterns = [
    re_path(r'^asignar_grupo_visitas/$', views.asignar_grupo_visitas, name="asignar_grupo_visitas"),
    re_path(r'^visitas/nueva/$', views.CrearVisitaView.as_view(), name="crear_visita"),
    re_path(r'^visitas/editar/(?P<pk>\d+)/$', views.EditarVisitaView.as_view(), name="editar_visita"),
    re_path(r'^api/visitas/asignar/$', views.asignar_grupo_visitas_ajax, name="asignar_grupo_visitas_ajax"),
]
