from rest_framework import serializers

from . import models


class MiembroSerializer(serializers.ModelSerializer):
    """Serializer para miembros."""

    class Meta:
        model = models.Miembro
        fields = (
            'id', 'nombre', 'primer_apellido', 'segundo_apellido', 'genero', 'celular', 'talla',
            'fecha_nacimiento', 'cedula', 'direccion', 'direccion', 'barrio', 'email', 'profesion',
            'estado_civil', 'estado',
        )
