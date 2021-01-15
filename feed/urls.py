from django.urls import re_path
from . import views

app_name = 'feed'
urlpatterns = [
    re_path(r'^feed/$', views.nuevo_caso, name="feed"),
]