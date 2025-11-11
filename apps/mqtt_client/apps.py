from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class MqttClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mqtt_client'
    
    def ready(self):
        """
        Se ejecuta cuando Django está listo.
        Inicia el cliente MQTT automáticamente.
        """
        # Solo iniciar en el proceso principal (no en workers de recarga)
        import sys
        if 'runserver' not in sys.argv:
            return
            
        try:
            from .client import mqtt_client
            logger.info("🚀 Iniciando cliente MQTT desde AppConfig...")
            mqtt_client.start()
        except Exception as e:
            logger.error(f"❌ Error al iniciar MQTT en AppConfig: {e}")
