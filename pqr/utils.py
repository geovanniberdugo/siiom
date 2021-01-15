# Django Package
from django.conf import settings
from django.urls import reverse_lazy
from django.core.mail import send_mail

# Locale
# from common.decorators import concurrente

# Python Package
import re


# CONSTANTS
def get_sender():
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'SIIOM <noreply@siiom.net>')


def dias_to_horas(dia):
    """
    :returns:
        La cantidad de horas de acuerdo a el numero de dias dados.
    """

    if isinstance(dia, int):
        return dia * 24
    raise TypeError("variable 'dia' must be a int instance, %(var)s instance" % {'var': type(dia)})


def enviar_email_success(request, caso):
    """
    Envia un email a el responsable de el caso, cuando todo este correcto
    """

    mensaje = """
        ¡Hola!\n
        En nuestra casa estamos para servirle. Hemos recibido su solicitud, estaremos dando una pronta respuesta.\n
        Tenga en cuenta que su número de solicitud es: %(id_caso)d\n
        Para consultas respecto a esta solicitud, puede llamar al %(telefono)d o escribir a %(email)s\n
        Dios le bendiga.
    """

    send_mail(
        'Hemos Recibido su solicitud exitosamente',
        mensaje % {'telefono': 3688932, 'id_caso': caso.id, 'email': 'informacion@icasadelrey.org'},
        get_sender(),
        ('{}'.format(caso.email), ),
        fail_silently=False
    )


def enviar_email_invitacion(request, caso, empleado, mensaje):
    """
    Envia un email a un invitado.
    """

    msj = """
        %(mensaje_from_form)s\n\n

        Por favor dirigete a http://%(domain)s/%(link)s para colaborar
    """

    data = {
        'mensaje_from_form': mensaje, 'domain': request.META['HTTP_HOST'],
        'link': reverse_lazy('pqr:ver_bitacora_caso', args=(caso.id, ))
    }

    send_mail(
        'Ha Sido invitado a Colaborar en un Caso de PQR',
        msj % data,
        get_sender(),
        ('{}'.format(empleado.usuario.email), ),
        fail_silently=False
    )


def format_string_to_ascii(string):
    """Retorna un string legible para ASCII"""

    splitted = string.split('.')

    REPLACES = (
        ('á', 'a'),
        ('é', 'e'),
        ('í', 'i'),
        ('ó', 'o'),
        ('ú', 'u'),
        ('à', 'a'),
        ('è', 'e'),
        ('ì', 'i'),
        ('ò', 'o'),
        ('ù', 'u'),
        ('ñ', 'n'),
        (' ', '_'),
    )

    match = re.compile(r'[a-zA-ZñÑáÁéÉíÍóÓúÚ\s0-9_]')
    for _str in splitted:
        _string = ''.join(match.findall(_str))
        for x in REPLACES:
            _string = _string.replace(x[0], x[1])
            _string = _string.replace(x[0].upper(), x[1].upper())
        splitted[splitted.index(_str)] = _string
    return '.'.join(splitted)
