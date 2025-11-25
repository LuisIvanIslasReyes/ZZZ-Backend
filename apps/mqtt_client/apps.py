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
        import os
        import sys
        
        # Evitar que se ejecute en el proceso de recarga automática
        if os.environ.get('RUN_MAIN') != 'true':
            return
            
        # Solo iniciar si estamos ejecutando el servidor
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            try:
                from .client import mqtt_client
                mqtt_client.start()
            except Exception as e:
                logger.error(f"❌ Error al iniciar MQTT: {e}")
