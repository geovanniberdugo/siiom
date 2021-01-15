from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import permissions, generics, status
from rest_framework.decorators import api_view

from . import models, serializers
from common.mixins import WaffleSwitchMixin

from waffle.decorators import waffle_switch


class CursoListAPIView(WaffleSwitchMixin, generics.ListAPIView):
    queryset = models.Curso.objects.all()
    serializer_class = serializers.CursoSerializer
    waffle_switch = 'instituto'

    def get_queryset(self, *args, **kwargs):
        salon_id = self.kwargs.get('pk')
        return super().get_queryset(*args, **kwargs).filter(salon_id=salon_id)

    def get_serializer(self, *args, **kwargs):
        kwargs['expand'] = ['materia', ]
        return super().get_serializer(*args, **kwargs)


@api_view(['GET'])
@waffle_switch('instituto')
def curso_by_month(request, pk):
    """
    Retorna los cursos que tienen eventos en un rango de fecha específico.
    """
    salon = get_object_or_404(models.Salon, pk=pk)

    _serializer = serializers.CursoEventoSerializer(data=request.GET)
    if _serializer.is_valid():
        cursos = models.Curso.objects.filter(
            fecha_inicio__lte=_serializer.data['end'],
            fecha_fin__gte=_serializer.data['start'], salon=salon)
        serializer = serializers.CursoSerializer(cursos, many=True, expand=['materia', ])
        response = Response(serializer.data)
    else:
        response = Response(_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return response


@api_view(['GET'])
@waffle_switch('instituto')
def verifica_disponibilidad_curso(request, pk):
    """
    Verifica que un curso pueda añadirse en un horario disponible, y no tenga
    interferencia con otro curso
    """
    salon = get_object_or_404(models.Salon, pk=pk)

    serializer = serializers.CursoEventoSerializer(data=request.GET)

    if serializer.is_valid():
        cursos = models.Curso.objects.filter(
            salon_id=salon.id, dia__overlap=serializer.data['dias'],
            fecha_inicio__lte=serializer.data['end'], fecha_fin__gte=serializer.data['start'],
            hora_inicio__lte=serializer.data['end_hour'], hora_fin__gte=serializer.data['start_hour']
        )
        response = Response({'valid': not cursos.exists()})
    else:
        response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return response
