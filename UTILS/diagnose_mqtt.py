"""
Script para verificar el estado completo del sistema MQTT
"""
import subprocess
import socket

print("=" * 60)
print("DIAGNÓSTICO DEL SISTEMA MQTT")
print("=" * 60)

# 1. Verificar si Mosquitto está corriendo
print("\n1️⃣  VERIFICANDO MOSQUITTO...")
try:
    result = subprocess.run(
        ['sc', 'query', 'mosquitto'],
        capture_output=True,
        text=True,
        shell=True
    )
    if 'RUNNING' in result.stdout:
        print("   ✅ Mosquitto está corriendo")
    else:
        print("   ❌ Mosquitto NO está corriendo")
        print("   Ejecuta: net start mosquitto (como Administrador)")
except Exception as e:
    print(f"   ❌ Error al verificar Mosquitto: {e}")

# 2. Verificar si el puerto 1883 está abierto
print("\n2️⃣  VERIFICANDO PUERTO 1883...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 1883))
    if result == 0:
        print("   ✅ Puerto 1883 está abierto")
    else:
        print("   ❌ Puerto 1883 NO está accesible")
    sock.close()
except Exception as e:
    print(f"   ❌ Error al verificar puerto: {e}")

# 3. Verificar Django
print("\n3️⃣  VERIFICANDO DJANGO...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 8000))
    if result == 0:
        print("   ✅ Django está corriendo en puerto 8000")
    else:
        print("   ❌ Django NO está corriendo")
        print("   Ejecuta: python manage.py runserver")
    sock.close()
except Exception as e:
    print(f"   ❌ Error al verificar Django: {e}")

# 4. Verificar datos en BD
print("\n4️⃣  VERIFICANDO BASE DE DATOS...")
try:
    import os
    import sys
    import django
    
    # Añadir el directorio raíz del proyecto al path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    from apps.sensors.models import SensorData
    from apps.devices.models import Device
    
    device = Device.objects.filter(device_identifier='ESP32-001').first()
    if device:
        print(f"   ✅ Dispositivo ESP32-001 encontrado")
        print(f"   📱 Asignado a: {device.employee.email}")
        print(f"   🔄 Última conexión: {device.last_connection or 'Nunca'}")
        
        data_count = SensorData.objects.filter(device=device).count()
        print(f"   📊 Datos de sensores: {data_count}")
        
        if data_count > 0:
            last_data = SensorData.objects.filter(device=device).order_by('-timestamp').first()
            print(f"   ⏰ Último dato: {last_data.timestamp}")
            print(f"   💓 HR: {last_data.heart_rate} BPM")
            print(f"   🫁 SpO2: {last_data.spo2}%")
    else:
        print("   ❌ Dispositivo ESP32-001 no encontrado")
        
except Exception as e:
    print(f"   ❌ Error al verificar BD: {e}")

print("\n" + "=" * 60)
print("RESUMEN:")
print("=" * 60)
print("\nSi todos los checks están en ✅, el sistema debería funcionar.")
print("Si falta alguno, revisa los pasos indicados.")
print("\nPara iniciar el simulador:")
print("  python SCRIPTS\\esp32_simulator.py")
print("\nDevice ID: ESP32-001")
print("Broker: localhost")
print("Puerto: 1883")
print("=" * 60)
