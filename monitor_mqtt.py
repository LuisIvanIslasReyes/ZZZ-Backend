"""
Script para verificar que los datos MQTT están llegando a la BD
"""
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sensors.models import SensorData
from apps.devices.models import Device

print("=" * 60)
print("VERIFICANDO DATOS DE SENSORES EN TIEMPO REAL")
print("=" * 60)

# Verificar dispositivo
device = Device.objects.filter(device_identifier='ESP32-001').first()
if not device:
    print("❌ Dispositivo ESP32-001 no encontrado")
    exit()

print(f"\n📱 Dispositivo: {device.device_identifier}")
print(f"👤 Empleado: {device.employee.get_full_name()}")
print(f"🔄 Última conexión: {device.last_connection or 'Nunca'}")

print("\n" + "=" * 60)
print("MONITOREANDO DATOS (Ctrl+C para detener)...")
print("=" * 60)

last_count = 0

try:
    while True:
        # Contar datos del dispositivo
        current_count = SensorData.objects.filter(device=device).count()
        
        if current_count > last_count:
            # Hay datos nuevos
            new_data = SensorData.objects.filter(device=device).order_by('-timestamp').first()
            print(f"\n✅ [{new_data.timestamp.strftime('%H:%M:%S')}] Nuevo dato recibido:")
            print(f"   💓 HR: {new_data.heart_rate:.1f} BPM")
            print(f"   🫁 SpO2: {new_data.spo2:.1f}%")
            print(f"   📊 Accel: X={new_data.accel_x:.2f}, Y={new_data.accel_y:.2f}, Z={new_data.accel_z:.2f}")
            print(f"   📈 Total datos: {current_count}")
            last_count = current_count
        else:
            print(".", end="", flush=True)
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\n✅ Monitoreo detenido")
    print(f"\nTotal de datos recibidos: {last_count}")
