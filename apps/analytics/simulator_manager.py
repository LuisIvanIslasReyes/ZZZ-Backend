"""
Gestor de múltiples simuladores ESP32 concurrentes.
Permite iniciar, detener y monitorear múltiples simuladores simultáneamente.
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import math
import threading
import logging
from datetime import datetime
from django.utils import timezone

from apps.analytics.simulator_models import SimulatorSession

logger = logging.getLogger(__name__)


class ESP32SimulatorThread:
    """
    Simulador individual de ESP32 que corre en un thread separado.
    """
    
    def __init__(self, session_id, config):
        self.session_id = session_id
        self.config = config
        self.device_id = config['device_id']
        self.running = False
        self.thread = None
        self.client = None
        
        # Estado del simulador
        self.time_offset = 0
        self.fatigue_level = config.get('initial_fatigue', 20.0)
        self.activity_mode = config.get('activity_mode', 'light')
        self.base_hr = config.get('base_heart_rate', 70)
        self.base_spo2 = config.get('base_spo2', 97.0)
        self.fatigue_rate = config.get('fatigue_rate', 0.5)
        
        # MQTT config
        self.broker = config.get('mqtt_broker', 'localhost')
        self.port = config.get('mqtt_port', 1883)
        self.publish_interval = config.get('publish_interval', 5)
        
        # Estadísticas
        self.messages_sent = 0
    
    def start(self):
        """Inicia el simulador en un thread separado."""
        if self.running:
            logger.warning(f"[{self.device_id}] Ya está en ejecución")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"✅ [{self.device_id}] Simulador iniciado")
        return True
    
    def stop(self):
        """Detiene el simulador."""
        logger.info(f"🛑 [{self.device_id}] Deteniendo simulador...")
        self.running = False
        
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info(f"✅ [{self.device_id}] Simulador detenido")
    
    def _run(self):
        """Loop principal del simulador."""
        try:
            # Conectar MQTT
            self.client = mqtt.Client(client_id=f"{self.device_id}_sim")
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            logger.info(f"[{self.device_id}] Conectando a {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Esperar conexión
            timeout = 10
            while not self.client.is_connected() and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            if not self.client.is_connected():
                raise Exception("No se pudo conectar al broker MQTT")
            
            # Loop de publicación
            while self.running:
                self._publish_sensor_data()
                self._update_state()
                time.sleep(self.publish_interval)
            
        except Exception as e:
            logger.error(f"❌ [{self.device_id}] Error: {e}")
            self._update_session_error(str(e))
        finally:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"✅ [{self.device_id}] Conectado al broker MQTT")
        else:
            logger.error(f"❌ [{self.device_id}] Error de conexión: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        logger.info(f"⚠️  [{self.device_id}] Desconectado del broker")
    
    def _publish_sensor_data(self):
        """Publica datos de sensores vía MQTT."""
        hr = self._calculate_heart_rate()
        spo2 = self._calculate_spo2()
        accel = self._calculate_acceleration()
        
        payload = {
            'device_id': self.device_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'heart_rate': hr,
            'spo2': spo2,
            'acceleration': accel,
            'fatigue_level': round(self.fatigue_level, 1),
            'activity': self.activity_mode
        }
        
        topic = f"devices/{self.device_id}/sensors"
        self.client.publish(topic, json.dumps(payload))
        self.messages_sent += 1
        
        # Actualizar BD cada 10 mensajes
        if self.messages_sent % 10 == 0:
            self._update_session_stats()
    
    def _calculate_heart_rate(self):
        """Calcula ritmo cardíaco basado en actividad y fatiga."""
        activity_multipliers = {
            'resting': 1.0,
            'light': 1.3,
            'moderate': 1.7,
            'heavy': 2.2
        }
        
        multiplier = activity_multipliers.get(self.activity_mode, 1.0)
        hr = self.base_hr * multiplier
        
        # Añadir efecto de fatiga
        fatigue_increase = (self.fatigue_level / 100) * 20
        hr += fatigue_increase
        
        # Variabilidad natural
        hr += random.uniform(-5, 5)
        
        return max(50, min(200, round(hr, 1)))
    
    def _calculate_spo2(self):
        """Calcula saturación de oxígeno."""
        spo2 = self.base_spo2
        
        # Descenso por fatiga alta
        if self.fatigue_level > 70:
            spo2 -= (self.fatigue_level - 70) / 10
        
        # Variabilidad natural
        spo2 += random.uniform(-0.5, 0.5)
        
        return max(88, min(100, round(spo2, 1)))
    
    def _calculate_acceleration(self):
        """Calcula aceleración en 3 ejes."""
        activity_amplitudes = {
            'resting': 0.1,
            'light': 0.5,
            'moderate': 1.2,
            'heavy': 2.0
        }
        
        amplitude = activity_amplitudes.get(self.activity_mode, 0.1)
        t = self.time_offset / 10
        
        accel_x = amplitude * math.sin(t * 2.0) + random.uniform(-0.1, 0.1)
        accel_y = amplitude * math.cos(t * 1.5) + random.uniform(-0.1, 0.1)
        accel_z = 9.81 + amplitude * math.sin(t * 3.0) + random.uniform(-0.2, 0.2)
        
        return {
            'x': round(accel_x, 2),
            'y': round(accel_y, 2),
            'z': round(accel_z, 2)
        }
    
    def _update_state(self):
        """Actualiza el estado del simulador."""
        self.time_offset += 1
        
        # Cambio de fatiga según modo de actividad
        fatigue_changes = {
            'resting': -0.3,    # Recuperación en reposo
            'light': 0.1,       # Incremento lento
            'moderate': 0.3,    # Incremento moderado
            'heavy': 0.8        # Incremento rápido
        }
        
        # Aplicar cambio de fatiga basado en actividad y fatigue_rate
        base_change = fatigue_changes.get(self.activity_mode, 0)
        # El fatigue_rate ajusta la velocidad general (multiplicador)
        fatigue_change = base_change * (self.fatigue_rate / 0.5)  # 0.5 es el valor base
        
        self.fatigue_level += fatigue_change / (60 / self.publish_interval)
        self.fatigue_level = max(0, min(100, self.fatigue_level))  # Limitar entre 0-100
        
        # Cambio aleatorio de actividad cada ~2 minutos
        if self.time_offset % (120 // self.publish_interval) == 0:
            activities = ['resting', 'light', 'moderate', 'heavy']
            weights = [0.3, 0.4, 0.2, 0.1]
            self.activity_mode = random.choices(activities, weights=weights)[0]
            logger.info(f"🔄 [{self.device_id}] Actividad: {self.activity_mode}, Fatiga: {self.fatigue_level:.1f}%")
    
    def _update_session_stats(self):
        """Actualiza estadísticas en la BD."""
        try:
            from apps.analytics.simulator_models import SimulatorSession
            session = SimulatorSession.objects.get(id=self.session_id)
            session.messages_sent = self.messages_sent
            session.current_fatigue = self.fatigue_level
            session.activity_mode = self.activity_mode
            session.save(update_fields=['messages_sent', 'current_fatigue', 'activity_mode', 'updated_at'])
        except Exception as e:
            logger.error(f"Error actualizando sesión {self.session_id}: {e}")
    
    def _update_session_error(self, error_msg):
        """Actualiza la sesión con mensaje de error."""
        try:
            from apps.analytics.simulator_models import SimulatorSession
            session = SimulatorSession.objects.get(id=self.session_id)
            session.status = 'error'
            session.error_message = error_msg
            session.stopped_at = timezone.now()
            session.save()
        except Exception as e:
            logger.error(f"Error actualizando error de sesión {self.session_id}: {e}")


class SimulatorManager:
    """
    Gestor de múltiples simuladores ESP32 concurrentes.
    Singleton para mantener control centralizado.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.simulators = {}  # session_id -> ESP32SimulatorThread
        self._initialized = True
        logger.info("✅ SimulatorManager inicializado")
    
    def start_simulator(self, session_id):
        """
        Inicia un simulador para una sesión.
        
        Args:
            session_id: ID de la sesión SimulatorSession
        
        Returns:
            bool: True si se inició correctamente
        """
        try:
            # Obtener configuración de la sesión
            session = SimulatorSession.objects.get(id=session_id)
            
            if session_id in self.simulators:
                logger.warning(f"Simulador para sesión {session_id} ya existe")
                return False
            
            # Crear y arrancar simulador
            config = session.get_config_dict()
            simulator = ESP32SimulatorThread(session_id, config)
            
            if simulator.start():
                self.simulators[session_id] = simulator
                
                # Actualizar estado en BD
                session.status = 'running'
                session.save(update_fields=['status', 'updated_at'])
                
                logger.info(f"✅ Simulador iniciado para sesión {session_id}")
                return True
            
            return False
            
        except SimulatorSession.DoesNotExist:
            logger.error(f"Sesión {session_id} no existe")
            return False
        except Exception as e:
            logger.error(f"Error iniciando simulador: {e}")
            return False
    
    def stop_simulator(self, session_id):
        """
        Detiene un simulador.
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            bool: True si se detuvo correctamente
        """
        if session_id not in self.simulators:
            logger.warning(f"Simulador para sesión {session_id} no existe")
            return False
        
        try:
            # Detener simulador
            simulator = self.simulators[session_id]
            simulator.stop()
            del self.simulators[session_id]
            
            # Actualizar estado en BD
            session = SimulatorSession.objects.get(id=session_id)
            session.status = 'stopped'
            session.stopped_at = timezone.now()
            session.messages_sent = simulator.messages_sent
            session.current_fatigue = simulator.fatigue_level
            session.save()
            
            logger.info(f"✅ Simulador detenido para sesión {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deteniendo simulador: {e}")
            return False
    
    def stop_all_simulators(self):
        """Detiene todos los simuladores activos."""
        logger.info("🛑 Deteniendo todos los simuladores...")
        session_ids = list(self.simulators.keys())
        
        for session_id in session_ids:
            self.stop_simulator(session_id)
        
        logger.info("✅ Todos los simuladores detenidos")
    
    def get_active_sessions(self):
        """Retorna IDs de sesiones activas."""
        return list(self.simulators.keys())
    
    def get_simulator_stats(self, session_id):
        """Obtiene estadísticas de un simulador."""
        if session_id not in self.simulators:
            return None
        
        simulator = self.simulators[session_id]
        return {
            'device_id': simulator.device_id,
            'running': simulator.running,
            'messages_sent': simulator.messages_sent,
            'current_fatigue': round(simulator.fatigue_level, 1),
            'activity_mode': simulator.activity_mode,
        }
    
    def update_simulator_config(self, session_id, config):
        """
        Actualiza configuración de un simulador en ejecución.
        
        Args:
            session_id: ID de la sesión
            config: Diccionario con nuevos parámetros
        """
        if session_id not in self.simulators:
            return False
        
        simulator = self.simulators[session_id]
        
        # Actualizar parámetros en caliente
        if 'activity_mode' in config:
            simulator.activity_mode = config['activity_mode']
        if 'fatigue_rate' in config:
            simulator.fatigue_rate = config['fatigue_rate']
        if 'fatigue_level' in config:
            simulator.fatigue_level = config['fatigue_level']
        
        logger.info(f"✅ Configuración actualizada para sesión {session_id}")
        return True


# Instancia global
simulator_manager = SimulatorManager()
