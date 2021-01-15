import logging
from django.core.exceptions import DisallowedHost

logger = logging.getLogger(__name__)


class LogNotAllowedHostHeaderMiddleware(object):
    """
    Middleware que se encarga de loguear en consola los headers del request si este es enviado desde un host no
    permitido.
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
        Loguea en consola los headers del request si el host desde el que se envia el request no se encuentra
        autorizado.
        """

        try:
            request.get_host()
        except DisallowedHost:
            if not request.META['HTTP_HOST'] == '45.56.115.140':
                logger.critical(request.META)
