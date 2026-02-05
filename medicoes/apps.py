from django.apps import AppConfig


class MedicoesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medicoes'
    verbose_name = 'Medições Gravimétricas'
    def ready(self):
        """Importar signals quando o app está pronto"""
        from . import db_signals  # noqa