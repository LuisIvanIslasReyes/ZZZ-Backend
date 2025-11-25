from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class SensorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sensors'
    
    def ready(self):
        """
        Se ejecuta cuando Django termina de inicializarse.
        Inicia el scheduler de procesamiento automático.
        """
        # Evitar iniciar scheduler en comandos de gestión
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            try:
                from .scheduler import start_scheduler
                start_scheduler()
                logger.info("✅ Scheduler de procesamiento automático activado")
            except Exception as e:
                logger.error(f"❌ Error iniciando scheduler: {e}")

