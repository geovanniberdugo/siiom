from django.urls import re_path
from . import views

app_name = 'reportes'
urlpatterns = [
    re_path(r'^estadistico_reunionesDiscipulado/$',
        views.estadistico_reuniones_discipulado, name="estadistico_reuniones_discipulado"),
    re_path(r'^estadistico_totalizado_reunionesGAR/$',
        views.estadistico_totalizado_reuniones_gar, name="estadistico_totalizado_reuniones_grupo"),
    re_path(r'^confirmar_ofrenda_grupos_red/$', views.confirmar_ofrenda_grupos_red, name="confirmar_ofrenda_grupos_red"),
    
    
    re_path(r'^estadistico_reuniones_gar/$', views.reporte_estadistico_reuniones_gar, name="estadistico_reuniones_gar"),
    re_path(r'^estadistico_reunion_discipulado/$', views.estadistico_reunion_discipulado, name="estadistico_reunion_discipulado"),
    re_path(r'^reporte_d12_excel/$', views.reporte_asistencia_discipulado_excel, name="reporte_asistencia_discipulado_excel"),
]
