import paho.mqtt.client as mqtt
import json
import logging
from django.conf import settings
from django.utils import timezone
from apps.devices.models import Device
from apps.sensors.models import SensorData

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    Cliente MQTT para recibir datos de dispositivos ESP32.
    Se suscribe al topic 'devices/+/sensors' y procesa mensajes JSON.
    """
    
    def __init__(self):
        self.client = None
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker MQTT"""
        if rc == 0:
            self.connected = True
            client.subscribe("devices/+/sensors")
            logger.info("✅ MQTT conectado y suscrito")
        else:
            logger.error(f"❌ Error de conexión MQTT. Código: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        logger.warning(f"⚠️  Desconectado del broker MQTT. Código: {rc}")
        self.connected = False
        
    def on_message(self, client, userdata, msg):
        """
        Callback cuando llega un mensaje.
        Formato esperado del mensaje JSON:
        {
            "device_id": "ESP32-001",
            "timestamp": "2025-11-10T14:30:00Z",
            "heart_rate": 75.5,
            "spo2": 98.2,
            "accel": {
                "x": 0.12,
                "y": -0.05,
                "z": 9.81
            }
        }
        """
        try:
            # Decodificar mensaje
            payload = json.loads(msg.payload.decode())
            device_id = payload.get('device_id')
            
            logger.debug(f"📥 Mensaje recibido de {device_id}")
            
            # Buscar el dispositivo en la BD
            try:
                device = Device.objects.get(device_identifier=device_id, is_active=True)
            except Device.DoesNotExist:
                logger.warning(f"⚠️  Dispositivo no encontrado o inactivo: {device_id}")
                return
            
            # Parsear timestamp
            timestamp_str = payload.get('timestamp')
            if timestamp_str:
                from dateutil import parser as date_parser
                timestamp = date_parser.parse(timestamp_str)
            else:
                timestamp = timezone.now()
            
            # Extraer datos de sensores
            heart_rate = payload.get('heart_rate')
            spo2 = payload.get('spo2')
            accel = payload.get('accel', {})
            accel_x = accel.get('x', 0.0)
            accel_y = accel.get('y', 0.0)
            accel_z = accel.get('z', 0.0)
            
            # Validar datos mínimos
            if heart_rate is None or spo2 is None:
                logger.warning(f"⚠️  Datos incompletos de {device_id}")
                return
            
            # Guardar en la base de datos
            sensor_data = SensorData.objects.create(
                device=device,
                timestamp=timestamp,
                heart_rate=heart_rate,
                spo2=spo2,
                accel_x=accel_x,
                accel_y=accel_y,
                accel_z=accel_z
            )
            
            # Actualizar última conexión del dispositivo
            device.last_connection = timestamp
            device.save(update_fields=['last_connection'])
            
            # Log más silencioso - solo debug
            logger.debug(f"✅ {device_id}: HR={heart_rate} SpO2={spo2}%")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error JSON: {e}")
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}", exc_info=True)
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback cuando se completa la suscripción"""
        pass  # Silencioso
    
    def start(self):
        """Iniciar cliente MQTT"""
        try:
            # Crear cliente MQTT
            self.client = mqtt.Client()
            
            # Configurar callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            
            # Configurar credenciales si existen
            mqtt_username = getattr(settings, 'MQTT_USERNAME', None)
            mqtt_password = getattr(settings, 'MQTT_PASSWORD', None)
            if mqtt_username and mqtt_password:
                self.client.username_pw_set(mqtt_username, mqtt_password)
            
            # Conectar al broker
            broker = getattr(settings, 'MQTT_BROKER', 'localhost')
            port = getattr(settings, 'MQTT_PORT', 1883)
            keepalive = getattr(settings, 'MQTT_KEEPALIVE', 60)
            
            logger.info(f"🚀 Cliente MQTT iniciando ({broker}:{port})...")
            self.client.connect(broker, port, keepalive)
            
            # Iniciar loop en segundo plano
            self.client.loop_start()
            
        except Exception as e:
            logger.error(f"❌ Error al iniciar cliente MQTT: {e}", exc_info=True)
    
    def stop(self):
        """Detener cliente MQTT"""
        if self.client:
            logger.info("🛑 Deteniendo cliente MQTT...")
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("✅ Cliente MQTT detenido")


# Instancia global del cliente MQTT
mqtt_client = MQTTClient()
