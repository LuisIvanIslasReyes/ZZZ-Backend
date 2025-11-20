"""
Script para crear el dispositivo ESP32-001 para pruebas con MQTT
"""
import os
import sys
import django

# Añadir el directorio raíz del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser
from apps.devices.models import Device

print("=" * 60)
print("CREANDO DISPOSITIVO ESP32-001")
print("=" * 60)

# Buscar un supervisor
supervisor = CustomUser.objects.filter(role='supervisor').first()
if not supervisor:
    print("❌ No hay supervisores en la BD. Creando uno...")
    admin = CustomUser.objects.filter(role='admin').first()
    supervisor = CustomUser.objects.create_user(
        email='supervisor_mqtt@test.com',
        password='test123',
        first_name='Supervisor',
        last_name='MQTT',
        role='supervisor',
        admin=admin
    )
    print(f"✅ Supervisor creado: {supervisor.email}")
else:
    print(f"✅ Usando supervisor existente: {supervisor.email}")

# Buscar un empleado del supervisor que NO tenga dispositivo
employees_without_device = CustomUser.objects.filter(
    role='employee', 
    supervisor=supervisor,
    device__isnull=True
)

if employees_without_device.exists():
    employee = employees_without_device.first()
    print(f"✅ Usando empleado sin dispositivo: {employee.email}")
else:
    print("❌ Todos los empleados ya tienen dispositivo. Creando uno nuevo...")
    employee = CustomUser.objects.create_user(
        email='employee_mqtt@test.com',
        password='test123',
        first_name='Empleado',
        last_name='MQTT',
        role='employee',
        supervisor=supervisor
    )
    print(f"✅ Empleado creado: {employee.email}")

# Verificar si ESP32-001 ya existe
existing = Device.objects.filter(device_identifier='ESP32-001').first()
if existing:
    print(f"\n⚠️  El dispositivo ESP32-001 ya existe!")
    print(f"  - Asignado a: {existing.employee.email}")
    print(f"  - Supervisor: {existing.supervisor.email}")
    response = input("\n¿Quieres eliminarlo y crear uno nuevo? (s/n): ")
    if response.lower() == 's':
        existing.delete()
        print("✅ Dispositivo anterior eliminado")
    else:
        print("❌ Operación cancelada")
        exit()

# Crear dispositivo ESP32-001
try:
    device = Device.objects.create(
        device_identifier='ESP32-001',
        employee=employee,
        supervisor=supervisor,
        company=employee.company,
        is_active=True
    )
    print(f"\n✅ DISPOSITIVO CREADO EXITOSAMENTE")
    print(f"  📱 ID: {device.device_identifier}")
    print(f"  👤 Empleado: {device.employee.get_full_name()} ({device.employee.email})")
    print(f"  👔 Supervisor: {device.supervisor.get_full_name()} ({device.supervisor.email})")
    print(f"  🏢 Empresa: {device.company.name if device.company else 'N/A'}")
    print(f"  ✅ Activo: {device.is_active}")
    
    print("\n" + "=" * 60)
    print("LISTO PARA USAR CON EL SIMULADOR ESP32")
    print("=" * 60)
    print("\nPuedes ejecutar el simulador con:")
    print("  python SCRIPTS\\esp32_simulator.py")
    print("\nY usar estas credenciales:")
    print(f"  Device ID: ESP32-001")
    print(f"  Broker: localhost")
    print(f"  Puerto: 1883")
    
except Exception as e:
    print(f"\n❌ Error al crear dispositivo: {e}")
    import traceback
    traceback.print_exc()
