# -*- coding: utf-8 -*-

# Django Package
from django.db.models.signals import post_delete
from django.dispatch import receiver

# Locale Apps
from .models import Adjunto

# Python Package
import os

__author__ = 'German Alzate'


@receiver(signal=post_delete, sender=Adjunto)
def model_post_delete(sender, **kwargs):
    instance = kwargs['instance']

    if os.path.exists(instance.archivo._get_path()) and os.path.isfile(instance.archivo._get_path()):
        os.remove(instance.archivo._get_path())
