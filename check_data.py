"""
Script para verificar usuarios y dispositivos en la BD
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser
from apps.devices.models import Device

print("=" * 60)
print("VERIFICANDO DATOS EN LA BASE DE DATOS")
print("=" * 60)

# Contar usuarios por rol
admins = CustomUser.objects.filter(role='admin')
supervisors = CustomUser.objects.filter(role='supervisor')
employees = CustomUser.objects.filter(role='employee')

print(f"\n📊 USUARIOS:")
print(f"  - Admins: {admins.count()}")
if admins.exists():
    for admin in admins:
        print(f"    • {admin.email}")

print(f"  - Supervisores: {supervisors.count()}")
if supervisors.exists():
    for sup in supervisors:
        print(f"    • {sup.email}")

print(f"  - Empleados: {employees.count()}")
if employees.exists():
    for emp in employees:
        print(f"    • {emp.email} (Supervisor: {emp.supervisor.email if emp.supervisor else 'N/A'})")

# Contar dispositivos
devices = Device.objects.all()
print(f"\n📱 DISPOSITIVOS: {devices.count()}")
if devices.exists():
    for dev in devices:
        print(f"  • {dev.device_identifier}")
        print(f"    - Empleado: {dev.employee.email}")
        print(f"    - Supervisor: {dev.supervisor.email}")
        print(f"    - Activo: {dev.is_active}")
        print(f"    - Última conexión: {dev.last_connection or 'Nunca'}")

# Verificar ESP32-001 específicamente
print(f"\n🔍 DISPOSITIVO ESP32-001:")
esp32 = Device.objects.filter(device_identifier='ESP32-001').first()
if esp32:
    print(f"  ✅ Existe")
    print(f"  - Asignado a: {esp32.employee.get_full_name()} ({esp32.employee.email})")
    print(f"  - Supervisor: {esp32.supervisor.get_full_name()} ({esp32.supervisor.email})")
    print(f"  - Estado: {'Activo' if esp32.is_active else 'Inactivo'}")
else:
    print(f"  ❌ No existe - Necesitas crearlo")

print("\n" + "=" * 60)
