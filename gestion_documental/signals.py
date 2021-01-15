# -*- coding: utf-8 -*-

# Django Package
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

# Locale Apps
from .models import Documento, Registro

# Python Package
import os

__author__ = 'German Alzate'


@receiver(signal=post_save, sender=Documento)
@receiver(signal=post_save, sender=Registro)
def model_save(sender, **kwargs):
    pass


@receiver(signal=post_delete, sender=Documento)
def model_post_delete(sender, **kwargs):
    instance = kwargs['instance']

    if not instance.is_image:
        from .utils import get_route, get_filenames, CARPETA_PDF_TO_IMAGE
        _ruta = get_route(instance.archivo)
        if _ruta is not None:  # Mientras el archivo aún exista
            ruta = _ruta + CARPETA_PDF_TO_IMAGE
            for file in get_filenames(instance.archivo):
                if os.path.exists(ruta + file) and os.path.isfile(ruta + file):
                    os.remove(ruta + file)
    if os.path.exists(instance.archivo.path) and os.path.isfile(instance.archivo.path):
        os.remove(instance.archivo.path)
