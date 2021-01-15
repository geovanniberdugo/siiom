from django.urls import re_path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views, api, forms
from grupos.views import editar_horario_reunion_grupo

app_name = 'miembros'
urlpatterns = [
    re_path(r'^$', views.miembro_inicio, name="miembro_inicio"),
    re_path(r'^perfil/(?P<pk>\d*)/$', views.editar_perfil_miembro, name="editar_perfil"),
    re_path(r'^grupo/(?P<pk>\d*)/$', editar_horario_reunion_grupo, name="editar_grupo"),
    re_path(r'^asignar_grupo/(\d+)/$', views.asignar_grupo, name="asignar_grupo"),
    re_path(r'^crear_zona/$', views.crear_zona, name="crear_zona"),
    re_path(r'^editar_zona/(?P<pk>\d+)/$', views.editar_zona, name="editar_zona"),
    re_path(r'^listar_zonas/$', views.listar_zonas, name="listar_zonas"),
    re_path(r'^barrios/(\d+)/$', views.barrios_zona, name="barrios"),
    re_path(r'^crear_barrio/(\d+)/$', views.crear_barrio, name="crear_barrio"),
    re_path(r'^editar_barrio/(?P<id>\d+)/(?P<pk>\d+)/$', views.editar_barrio, name="editar_barrio"),
    re_path(r'^crear_tipo_miembro/$', views.crear_tipo_miembro, name="crear_tipo_miembro"),
    re_path(r'^listar_tipo_miembro/$', views.listar_tipos_miembro, name="listar_tipo_miembro"),
    re_path(r'^editar_tipo_miembro/(?P<pk>\d+)/$', views.editar_tipo_miembro, name="editar_tipo_miembro"),
    re_path(r'^asignar_usuario/(\d+)/$', views.crear_usuario_miembro, name="asignar_usuario"),
    re_path(r'^eliminar_cambio_tipo/(\d+)/$', views.eliminar_cambio_tipo_miembro, name="eliminar_cambio_tipo"),
    re_path(r'^discipulos/(?P<pk>\d*)/$', views.ver_discipulos, name="ver_discipulos"),
    re_path(r'^informacion_iglesia/(?P<pk>\d*)/$', views.ver_informacion_miembro, name="ver_informacion"),
    re_path(r'^eliminar_foto_perfil/(?P<pk>\d*)/$', views.eliminar_foto_perfil, name="eliminar_foto"),

    re_path(r'^(?P<pk>\d*)/discipulados/$', views.discipulados, name="discipulados"),
    re_path(r'^nuevo/$', views.crear_miembro, name='nuevo'),
    re_path(r'^(?P<pk>\d+)/trasladar/$', views.trasladar, name='trasladar'),
    re_path(r'^redes/(?P<pk>\d+)/lideres/$', views.listar_lideres, name='listar_lideres'),
    re_path(
        r'^cambiar_contrasena/$', auth_views.PasswordChangeView.as_view(
            success_url=reverse_lazy('miembros:miembro_inicio'),
            template_name='miembros/cambiar_contrasena.html',
            form_class=forms.CambiarContrasenaForm,
        ),
        name="cambiar_contrasena"
    ),

    re_path(r'^api/admin/resetear_contrasena/$', api.resetear_contrasena, name='resetear_contrasena_api'),
    re_path(r'^api/desvincular_lider/(?P<pk>\d+)/$', api.desvincular_lider_grupo_api, name='desvincular_grupo_api'),
]
