from django.urls import reverse
from django.utils.functional import SimpleLazyObject

from .models import Miembro


def get_miembro(request):
    if not hasattr(request, '_cache_miembro'):
        try:
            request._cache_miembro = Miembro.objects.get(usuario=request.user)
        except Miembro.DoesNotExist:
            return None
    return request._cache_miembro


class MiembroMiddleWare(object):
    """
    Middleware que se encarga de agregar el miembro al request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response is None:
            return self.get_response(request)
        return response

    def process_request(self, request):
        """
        Agrega al request el miembro si el usuario logueado es un miembro.
        """

        if not request.user.is_anonymous and not request.path.startswith(reverse('admin:index')):
            request.miembro = SimpleLazyObject(lambda: get_miembro(request))
