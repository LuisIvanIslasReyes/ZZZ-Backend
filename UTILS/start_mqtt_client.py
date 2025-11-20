"""
Script para iniciar el cliente MQTT manualmente y verificar la conexión
"""
import os
import sys
import django
import time

# Añadir el directorio raíz del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.mqtt_client.client import mqtt_client

print("=" * 60)
print("INICIANDO CLIENTE MQTT MANUALMENTE")
print("=" * 60)

print("\n🔄 Iniciando cliente MQTT...")
mqtt_client.start()

print("\n✅ Cliente iniciado. Esperando mensajes...")
print("📡 Suscrito a: devices/+/sensors")
print("\nVerifica que el simulador ESP32 esté corriendo.")
print("Presiona Ctrl+C para detener\n")

try:
    # Esperar un poco para ver si se conecta
    time.sleep(3)
    
    if mqtt_client.connected:
        print("✅ CONEXIÓN EXITOSA")
    else:
        print("❌ NO SE PUDO CONECTAR")
    
    # Mantener el script corriendo
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\n🛑 Deteniendo cliente MQTT...")
    mqtt_client.stop()
    print("✅ Cliente detenido")
