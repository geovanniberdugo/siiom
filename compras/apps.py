from django.apps import AppConfig


class ComprasConfig(AppConfig):
    name = 'compras'
    verbose_name = 'Compras'

    def ready(self):
        import compras.signals
