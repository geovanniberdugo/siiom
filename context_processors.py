from contextlib import suppress
from django.conf import settings
from grupos.models import HistorialEstado


def siiom_context_processor(request):
    """
    Procesador de contextos para siiom.
    """

    data = {
        'GRUPO_ACTIVO': HistorialEstado.ACTIVO,
        'GRUPO_INACTIVO': HistorialEstado.INACTIVO,
        'GRUPO_SUSPENDIDO': HistorialEstado.SUSPENDIDO,
        'ANALYTICS': settings.ANALYTICS
    }

    if hasattr(request, 'miembro'):
        with suppress(Exception):
            miembro = request.miembro
            draw_mapa = False

            if miembro.grupo_lidera is not None:
                if miembro.grupo_lidera.get_position() is None:
                    draw_mapa = True

            data['draw_mapa'] = draw_mapa

    return data
