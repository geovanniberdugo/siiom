from django.test import SimpleTestCase
from django.conf import settings


class SendMailTest(SimpleTestCase):
    """Pruebas unitarias para la utilidad de envio de emails."""

    def test_emails_enviados_con_DEFAULT_EMAIL_setting(self):
        """Prueba que se envien los emails con el setting DEFAULT_FROM_EMAIL."""

        from django.core import mail
        from ..utils import send_mail

        send_mail('probando email', 'probando que el email se envie desde DEFAULT_FROM_EMAIL', ['s@s.com'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
