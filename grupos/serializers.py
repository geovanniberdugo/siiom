from rest_framework import serializers
from . import models

class AsistenciaDiscipuladoSerializer(serializers.ModelSerializer):
    """Serializer para AsistenciaDiscipulado."""

    class Meta:
        model = models.AsistenciaDiscipulado
        fields = ['id', 'miembro', 'asistencia', 'reunion']


class ReunionDiscipuladoSerializer(serializers.ModelSerializer):
    """Serializer para ReunionDiscipulado."""

    asistencia = AsistenciaDiscipuladoSerializer(many=True, read_only=True)

    class Meta:
        model = models.ReunionDiscipulado
        fields = ['id', 'grupo', 'predica', 'novedades', 'ofrenda', 'asistencia']