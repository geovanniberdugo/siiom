from django.apps import AppConfig


class GestionDocumentalConfig(AppConfig):
    name = 'gestion_documental'
    verbose_name = 'SGD Application'

    def ready(self):
        import gestion_documental.signals
