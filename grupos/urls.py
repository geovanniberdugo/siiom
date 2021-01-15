from django.urls import re_path
from . import views, api

app_name = 'grupos'
urlpatterns = [
    re_path(r'^listar_predicas/$', views.listar_predicas, name="listar_predicas"),
    re_path(r'^crear_predica/$', views.crear_predica, name="crear_predica"),
    re_path(r'^editar_predica/(?P<pk>\d+)/$', views.editar_predica, name="editar_predica"),
    re_path(r'^ver_reportes/$', views.ver_reportes_grupo, name="reportes_grupo"),
    re_path(r'^editar_reporte/(?P<pk>\d+)/$', views.editar_runion_grupo, name="editar_reporte"),
    re_path(r'^ensenanzas/', views.EnseñanzasListView.as_view(), name="ensenanza_listado"),

    re_path(r'^raiz/$', views.grupo_raiz, name='raiz'),
    re_path(r'^redes/$', views.listar_redes, name='redes_listar'),
    re_path(r'^redes/nueva/$', views.crear_red, name='red_nueva'),
    re_path(r'^(?P<pk>\d+)/$', views.detalle_grupo, name='detalle'),
    re_path(r'^(?P<pk>\d+)/editar/$', views.editar_grupo, name='editar'),
    re_path(r'^redes/(?P<pk>\d+)/$', views.editar_red, name='red_editar'),
    re_path(r'^redes/(?P<pk>\d+)/nuevo/$', views.crear_grupo, name='nuevo'),
    re_path(r'^organigrama/$', views.organigrama_grupos, name='organigrama'),
    re_path(r'^(?P<pk>\d+)/trasladar/$', views.trasladar, name='trasladar'),
    re_path(r'^archivar/$', views.archivar_grupo, name='archivar'),
    re_path(r'^redes/(?P<pk>\d+)/grupos/$', views.listar_grupos, name='listar'),
    re_path(r'^trasladar_lideres/$', views.trasladar_lideres, name='trasladar_lideres'),
    re_path(r'^sin_confirmar_ofrenda_GAR/$', views.sin_confirmar_ofrenda_GAR, name='sin_confirmar_ofrenda_GAR'),
    re_path(r'^reportar_reunion_discipulado/$', views.reportar_reunion_discipulado, name="reportar_reunion_discipulado"),
    re_path(r'^reportar_reunion_grupo_admin/$', views.reportar_reunion_grupo_admin, name="reportar_reunion_grupo_admin"),
    re_path(r'^reportar_reunion_grupo/$', views.reportar_reunion_grupo, name="reportar_reunion_grupo"),
    re_path(r'^(?P<pk>\d+)/confirmar_ofrenda_GAR/$', views.confirmar_ofrenda_GAR, name='confirmar_ofrenda_GAR'),
    re_path(
        r'^sin_confirmar_ofrenda_discipulado/$', views.sin_confirmar_ofrenda_discipulado,
        name='sin_confirmar_ofrenda_discipulado'
    ),
    re_path(
        r'^(?P<pk>\d+)/confirmar_ofrenda_discipulado/$', views.confirmar_ofrenda_discipulado,
        name='confirmar_ofrenda_discipulado'
    ),
    re_path(
        r'^reportar_reunion_discipulado_admin/$', views.admin_reportar_reunion_discipulado,
        name='admin_reportar_reunion_discipulado'
    ),

    re_path(r'^api/set_position_grupo/(?P<id_grupo>\d+)/$', views.set_position_grupo, name="posicion_grupo"),
    re_path(r'^api/(?P<pk>\d+)/lideres/$', api.lideres_grupo, name='lideres_api'),
    re_path(r'^api/(?P<pk>\d+)/miembros/$', api.discipulos_miembros_grupo, name='discipulos_miembros_api'),
    re_path(r'^api/(?P<pk>\d+)/discipulos/$', api.discipulos_grupo, name='discipulos_api'),
    re_path(r'^api/(?P<grupo>\d+)/(?P<predica>\d+)/reunion-discipulado/$', api.reunion_discipulado, name='reunion_discipulado_api'),
    re_path(r'^api/(?P<pk>\d+)/email/$', api.mail_missing_gar_envelopes_to_report, name='mail_missing_gar_envelopes_to_report_api'),
]
