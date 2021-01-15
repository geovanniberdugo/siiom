from django.urls import re_path
from . import api

app_name = 'common'
urlpatterns = [
    re_path(r'^api/buscar_miembro/(?P<pk>\d+)/$', api.busqueda_miembro_api, name="busqueda_miembro_api"),
    re_path(r'^api/buscar_grupo/(?P<pk>\d+)/$', api.busqueda_grupo_api, name="busqueda_grupo_api"),
]
