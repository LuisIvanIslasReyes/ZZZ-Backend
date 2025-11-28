"""
Simulador de Dispositivo ESP32 con sensores de fatiga.
Genera datos realistas y los publica vía MQTT cada 5 segundos.
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import math
from datetime import datetime
import sys


class ESP32Simulator:
    """
    Simulador de dispositivo ESP32 con sensores:
    - Ritmo cardíaco (HR)
    - Oxigenación (SpO2)
    - Acelerómetro (3 ejes)
    """
    
    def __init__(self, device_id, broker='localhost', port=1883):
        self.device_id = device_id
        self.broker = broker
        self.port = port
        self.client = None
        self.connected = False
        
        # Estado del simulador
        self.time_offset = 0  # Para simular el paso del tiempo
        self.fatigue_level = 0  # 0-100 (0 = descansado, 100 = muy fatigado)
        self.activity_mode = 'resting'  # resting, light, moderate, heavy
        
        # Parámetros base
        self.base_hr = random.randint(60, 75)  # Ritmo cardíaco base
        self.base_spo2 = random.uniform(96, 99)  # SpO2 base
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback de conexión"""
        if rc == 0:
            print(f"✅ [{self.device_id}] Conectado al broker MQTT")
            self.connected = True
        else:
            print(f"❌ [{self.device_id}] Error de conexión: {rc}")
            self.connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback de desconexión"""
        print(f"⚠️  [{self.device_id}] Desconectado del broker")
        self.connected = False
    
    def on_publish(self, client, userdata, mid):
        """Callback cuando se publica un mensaje"""
        pass  # Silencioso para no llenar la consola
    
    def calculate_heart_rate(self):
        """
        Calcula ritmo cardíaco basado en actividad y fatiga.
        - Resting: 60-80 BPM
        - Light: 80-110 BPM
        - Moderate: 110-140 BPM
        - Heavy: 140-170 BPM
        + Variación por fatiga
        """
        activity_multipliers = {
            'resting': 1.0,
            'light': 1.3,
            'moderate': 1.7,
            'heavy': 2.2
        }
        
        multiplier = activity_multipliers.get(self.activity_mode, 1.0)
        
        # HR base según actividad
        hr = self.base_hr * multiplier
        
        # Añadir efecto de fatiga (HR más alto cuando hay fatiga)
        fatigue_increase = (self.fatigue_level / 100) * 20
        hr += fatigue_increase
        
        # Variabilidad natural (±5 BPM)
        hr += random.uniform(-5, 5)
        
        # Limitar a rangos realistas
        hr = max(50, min(200, hr))
        
        return round(hr, 1)
    
    def calculate_spo2(self):
        """
        Calcula saturación de oxígeno.
        Normal: 95-100%
        Desciende ligeramente con fatiga alta
        """
        spo2 = self.base_spo2
        
        # Descenso por fatiga
        if self.fatigue_level > 70:
            spo2 -= (self.fatigue_level - 70) / 10
        
        # Variabilidad natural (±0.5%)
        spo2 += random.uniform(-0.5, 0.5)
        
        # Limitar a rangos realistas
        spo2 = max(88, min(100, spo2))
        
        return round(spo2, 1)
    
    def calculate_acceleration(self):
        """
        Calcula aceleración en 3 ejes.
        Simula movimiento según nivel de actividad.
        """
        activity_amplitudes = {
            'resting': 0.1,    # Muy poco movimiento
            'light': 0.5,      # Movimiento moderado
            'moderate': 1.2,   # Movimiento considerable
            'heavy': 2.0       # Mucho movimiento
        }
        
        amplitude = activity_amplitudes.get(self.activity_mode, 0.1)
        
        # Generar movimiento "realista" con componentes senoidales
        t = self.time_offset / 10  # Escala de tiempo
        
        accel_x = amplitude * math.sin(t * 2.0) + random.uniform(-0.1, 0.1)
        accel_y = amplitude * math.cos(t * 1.5) + random.uniform(-0.1, 0.1)
        accel_z = 9.81 + amplitude * math.sin(t * 3.0) + random.uniform(-0.2, 0.2)  # Gravedad + movimiento
        
        return {
            'x': round(accel_x, 2),
            'y': round(accel_y, 2),
            'z': round(accel_z, 2)
        }
    
    def update_state(self):
        """
        Actualiza el estado del empleado simulado.
        Simula cambios en actividad y fatiga a lo largo del tiempo.
        """
        self.time_offset += 1
        
        # Cada ~2 minutos (24 lecturas * 5s = 120s), considerar cambio de actividad
        if self.time_offset % 24 == 0:
            activities = ['resting', 'light', 'moderate', 'heavy']
            weights = [0.3, 0.4, 0.2, 0.1]  # Más probable estar en reposo/light
            self.activity_mode = random.choices(activities, weights=weights)[0]
            print(f"🔄 [{self.device_id}] Cambio de actividad: {self.activity_mode}")
        
        # Cambio de fatiga según modo de actividad
        fatigue_changes = {
            'resting': -0.5,    # Recuperación en reposo (más rápida)
            'light': 0.1,       # Incremento lento
            'moderate': 0.3,    # Incremento moderado
            'heavy': 0.8        # Incremento rápido
        }
        
        self.fatigue_level += fatigue_changes.get(self.activity_mode, 0)
        self.fatigue_level = max(0, min(100, self.fatigue_level))  # Limitar 0-100
    
    def generate_sensor_data(self):
        """Genera datos de todos los sensores"""
        data = {
            'device_id': self.device_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'heart_rate': self.calculate_heart_rate(),
            'spo2': self.calculate_spo2(),
            'accel': self.calculate_acceleration()
        }
        return data
    
    def publish_data(self):
        """Publica datos al broker MQTT"""
        if not self.connected:
            print(f"⚠️  [{self.device_id}] No conectado, omitiendo publicación")
            return
        
        data = self.generate_sensor_data()
        topic = f"devices/{self.device_id}/sensors"
        payload = json.dumps(data)
        
        result = self.client.publish(topic, payload, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"📤 [{self.device_id}] HR:{data['heart_rate']} BPM | SpO2:{data['spo2']}% | "
                  f"Fatiga:{self.fatigue_level:.1f} | Actividad:{self.activity_mode}")
        else:
            print(f"❌ [{self.device_id}] Error al publicar")
    
    def start(self):
        """Inicia el simulador"""
        print(f"🚀 Iniciando simulador ESP32: {self.device_id}")
        print(f"📡 Broker: {self.broker}:{self.port}")
        print(f"📊 HR base: {self.base_hr} BPM | SpO2 base: {self.base_spo2}%")
        print("-" * 80)
        
        # Configurar cliente MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        # Conectar
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Esperar conexión
            time.sleep(2)
            
            if not self.connected:
                print(f"❌ No se pudo conectar al broker")
                return
            
            # Loop principal: publicar cada 5 segundos
            print("✅ Publicando datos cada 5 segundos (Ctrl+C para detener)...")
            print("-" * 80)
            
            while True:
                self.update_state()
                self.publish_data()
                time.sleep(5)
                
        except KeyboardInterrupt:
            print(f"\n🛑 [{self.device_id}] Deteniendo simulador...")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene el simulador"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print(f"✅ [{self.device_id}] Simulador detenido")


def main():
    """Función principal"""
    print("=" * 80)
    print("ESP32 SIMULATOR - Sistema de Detección de Fatiga")
    print("=" * 80)
    
    # Configuración
    device_id = input("Ingresa el ID del dispositivo (ej: ESP32-001): ").strip()
    if not device_id:
        device_id = "ESP32-001"
    
    broker = input("Broker MQTT [localhost]: ").strip()
    if not broker:
        broker = "localhost"
    
    port_input = input("Puerto [1883]: ").strip()
    port = int(port_input) if port_input else 1883
    
    print()
    
    # Crear y ejecutar simulador
    simulator = ESP32Simulator(device_id, broker, port)
    simulator.start()


if __name__ == "__main__":
    main()
