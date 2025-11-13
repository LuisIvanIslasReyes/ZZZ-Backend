import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser
from apps.devices.models import Device

print("=" * 80)
print("CONFIGURACIÓN DE DATOS DE PRUEBA - MQTT")
print("=" * 80)

# 1. Obtener admin
admin = CustomUser.objects.filter(role='admin').first()
if not admin:
    print("❌ No hay admin en el sistema. Ejecuta create_superuser.py primero")
    exit(1)

print(f"✅ Admin encontrado: {admin.email}")

# 2. Crear o obtener supervisor
supervisor, created = CustomUser.objects.get_or_create(
    email='supervisor@test.com',
    defaults={
        'first_name': 'Test',
        'last_name': 'Supervisor',
        'role': 'supervisor',
        'admin_id': admin
    }
)

if created:
    supervisor.set_password('test123')
    supervisor.save()
    print(f"✅ Supervisor creado: {supervisor.email}")
else:
    print(f"✅ Supervisor existente: {supervisor.email}")

# 3. Crear o obtener empleado
employee, created = CustomUser.objects.get_or_create(
    email='employee@test.com',
    defaults={
        'first_name': 'Juan',
        'last_name': 'Test',
        'role': 'employee',
        'supervisor_id': supervisor
    }
)

if created:
    employee.set_password('test123')
    employee.save()
    print(f"✅ Empleado creado: {employee.email}")
else:
    print(f"✅ Empleado existente: {employee.email}")

# 4. Crear o obtener dispositivo ESP32-001
device, created = Device.objects.get_or_create(
    device_identifier='ESP32-001',
    defaults={
        'employee': employee,
        'supervisor': supervisor,
        'is_active': True
    }
)

if created:
    print(f"✅ Dispositivo creado: {device.device_identifier}")
else:
    print(f"✅ Dispositivo existente: {device.device_identifier}")

print()
print("=" * 80)
print("✅ CONFIGURACIÓN COMPLETADA")
print("=" * 80)
print()
print("📊 DATOS DE PRUEBA:")
print(f"   Supervisor: {supervisor.email} / test123")
print(f"   Empleado: {employee.email} / test123")
print(f"   Dispositivo: {device.device_identifier}")
print()
print("🚀 Ahora puedes:")
print("   1. Iniciar el servidor Django: python manage.py runserver")
print("   2. Ejecutar el simulador ESP32: python esp32_simulator.py")
print("      - Device ID: ESP32-001")
print("      - Broker: localhost")
print("      - Puerto: 1883")
print()
print("=" * 80)
