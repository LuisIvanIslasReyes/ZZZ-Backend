"""
Script para verificar por qué falla la creación de dispositivos
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser
from apps.devices.models import Device

print("=" * 80)
print("ANÁLISIS DE CREACIÓN DE DISPOSITIVOS")
print("=" * 80)

# Verificar empleado Brian Bautista
print("\n1. Verificando empleado Brian Bautista (empleado8@gmail.com):")
try:
    brian = CustomUser.objects.get(email='empleado8@gmail.com')
    print(f"   ✓ Empleado encontrado: {brian.get_full_name()}")
    print(f"   - Role: {brian.role}")
    print(f"   - Company: {brian.company}")
    print(f"   - Supervisor: {brian.supervisor}")
    
    # Verificar si ya tiene dispositivo
    existing_device = Device.objects.filter(employee=brian).first()
    if existing_device:
        print(f"   ⚠️  YA TIENE DISPOSITIVO ASIGNADO: {existing_device.device_identifier}")
    else:
        print(f"   ✓ No tiene dispositivo asignado")
except CustomUser.DoesNotExist:
    print("   ✗ Empleado NO encontrado")

# Verificar dispositivo ESP32-02
print("\n2. Verificando dispositivo ESP32-02:")
existing_esp32_02 = Device.objects.filter(device_identifier='ESP32-02').first()
if existing_esp32_02:
    print(f"   ⚠️  DISPOSITIVO YA EXISTE")
    print(f"   - Asignado a: {existing_esp32_02.employee.get_full_name()}")
    print(f"   - Email: {existing_esp32_02.employee.email}")
else:
    print(f"   ✓ Dispositivo ESP32-02 está disponible")

# Listar todos los supervisores
print("\n3. Supervisores en el sistema:")
supervisors = CustomUser.objects.filter(role='supervisor')
for sup in supervisors:
    print(f"   - {sup.email} (Company: {sup.company})")

# Listar todos los empleados
print("\n4. Empleados en el sistema:")
employees = CustomUser.objects.filter(role='employee')
for emp in employees:
    has_device = '✓' if hasattr(emp, 'device') else '✗'
    print(f"   {has_device} {emp.email} - {emp.get_full_name()} (Company: {emp.company}, Supervisor: {emp.supervisor})")

# Listar todos los dispositivos
print("\n5. Dispositivos existentes:")
devices = Device.objects.all()
if devices:
    for dev in devices:
        print(f"   - {dev.device_identifier} → {dev.employee.get_full_name()} ({dev.employee.email})")
else:
    print("   No hay dispositivos creados")

print("\n" + "=" * 80)
print("DIAGNÓSTICO:")
print("=" * 80)

# Diagnóstico específico para Brian
try:
    brian = CustomUser.objects.get(email='empleado8@gmail.com')
    existing_device = Device.objects.filter(employee=brian).first()
    
    if existing_device:
        print(f"❌ PROBLEMA: El empleado {brian.get_full_name()} YA tiene asignado el dispositivo {existing_device.device_identifier}")
        print(f"   SOLUCIÓN: Primero debes eliminar o reasignar el dispositivo existente")
    elif not brian.company:
        print(f"❌ PROBLEMA: El empleado {brian.get_full_name()} NO pertenece a ninguna empresa")
        print(f"   SOLUCIÓN: Asigna una empresa al empleado")
    elif not brian.supervisor:
        print(f"❌ PROBLEMA: El empleado {brian.get_full_name()} NO tiene supervisor asignado")
        print(f"   SOLUCIÓN: Asigna un supervisor al empleado")
    else:
        print(f"✓ El empleado {brian.get_full_name()} está listo para tener un dispositivo asignado")
        print(f"  - Company: {brian.company}")
        print(f"  - Supervisor: {brian.supervisor}")
        
except CustomUser.DoesNotExist:
    print("❌ PROBLEMA: No se encuentra el empleado empleado8@gmail.com")

print("=" * 80)
