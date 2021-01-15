from rest_framework import serializers
from rest_flex_fields import FlexFieldsModelSerializer

from . import models


class MateriaSerializer(serializers.ModelSerializer):
    """Serializer para Materia."""

    class Meta:
        model = models.Materia
        fields = ['id', 'nombre', 'dependencia', 'grupos_minimo', ]


class SalonSerializer(serializers.ModelSerializer):
    """Serializer para Salon."""

    class Meta:
        model = models.Salon
        fields = ['id', 'capacidad', 'nombre', ]


class CursoSerializer(FlexFieldsModelSerializer):
    """Serializer para Curso."""

    class Meta:
        model = models.Curso
        fields = [
            'id', 'precio', 'fecha_inicio', 'fecha_fin',
            'hora_inicio', 'hora_fin', 'materia', 'salon', 'estado',
            'dia', 'profesor', 'color'
        ]

    expandable_fields = {
        'materia': (MateriaSerializer, {'source': 'materia'})
    }


class CursoEventoSerializer(serializers.Serializer):
    """
    Serializer para eventos, este serializer es usado para validar
    los eventos de fullcalendar
    """

    start = serializers.DateField()
    end = serializers.DateField()
    dias = serializers.ListField(required=False, child=serializers.CharField(max_length=1))
    start_hour = serializers.TimeField(required=False)
    end_hour = serializers.TimeField(required=False)

    def validate_dias(self, value):
        booleans = [False, True]
        if not all(booleans[x in [y[0] for y in models.Curso.DIAS_SEMANA]] for x in value):
            raise serializers.ValidationError('Uno de los días seleccionados, no fueron reconocidos.')
        return value

    def validate(self, data):
        validate_data = super().validate(data)

        if validate_data['start'] > validate_data['end']:
            raise serializers.ValidationError('Fecha inicial no puede ser mayor a la final.')

        start_hour = validate_data.get('start_hour', None) or None
        end_hour = validate_data.get('end_hour', None) or None

        if start_hour is not None and end_hour is not None:
            if start_hour > end_hour:
                raise serializers.ValidationError('Hora inicial no puede ser mayor a la hora final.')
        elif start_hour is not None or end_hour is not None:
            raise serializers.ValidationError('Asegurese de digitar una hora de inicio y una hora de fin.')
        return validate_data
