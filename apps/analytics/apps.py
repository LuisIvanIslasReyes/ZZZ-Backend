from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    
    def ready(self):
        """
        Inicia servicios automáticos cuando Django arranca.
        """
        import sys
        
        # Solo iniciar en el proceso principal (no en migraciones, shell, etc.)
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            try:
                from apps.analytics.ml_scheduler import start_ml_scheduler
                
                # Iniciar scheduler de análisis ML
                start_ml_scheduler()
                
                logger.info("✅ Analytics App: Servicios automáticos iniciados")
                
            except Exception as e:
                logger.error(f"❌ Error iniciando servicios de analytics: {e}")
