"""
Script para registrar el dispositivo ESP32-001 físico en la base de datos.
Ejecutar: python manage.py shell < register_esp32_device.py
"""

from apps.devices.models import Device
from apps.users.models import User
from apps.companies.models import Company

# Configuración del dispositivo físico
DEVICE_ID = "ESP32-001"
EMPLOYEE_EMAIL = "german.garmendia@zero.com"  # Cambiar por el email del empleado real

print("=" * 60)
print("REGISTRANDO DISPOSITIVO ESP32 FÍSICO")
print("=" * 60)

try:
    # 1. Buscar el empleado
    employee = User.objects.get(email=EMPLOYEE_EMAIL, role='employee')
    print(f"✓ Empleado encontrado: {employee.get_full_name()}")
    
    # 2. Obtener supervisor del empleado
    supervisor = employee.supervisor
    if not supervisor:
        print("✗ ERROR: El empleado no tiene supervisor asignado")
        exit(1)
    print(f"✓ Supervisor: {supervisor.get_full_name()}")
    
    # 3. Obtener empresa
    company = employee.company
    if not company:
        print("✗ ERROR: El empleado no tiene empresa asignada")
        exit(1)
    print(f"✓ Empresa: {company.name}")
    
    # 4. Verificar si el dispositivo ya existe
    existing_device = Device.objects.filter(device_identifier=DEVICE_ID).first()
    if existing_device:
        print(f"⚠  El dispositivo {DEVICE_ID} ya existe")
        print(f"   Asignado a: {existing_device.employee.get_full_name()}")
        
        # Actualizar asignación si es necesario
        if existing_device.employee != employee:
            existing_device.employee = employee
            existing_device.supervisor = supervisor
            existing_device.company = company
            existing_device.is_active = True
            existing_device.save()
            print(f"✓ Dispositivo reasignado a {employee.get_full_name()}")
        else:
            print("✓ Dispositivo ya está correctamente asignado")
    else:
        # 5. Crear nuevo dispositivo
        device = Device.objects.create(
            device_identifier=DEVICE_ID,
            employee=employee,
            supervisor=supervisor,
            company=company,
            is_active=True
        )
        print(f"✓ Dispositivo {DEVICE_ID} creado exitosamente")
    
    print("\n" + "=" * 60)
    print("RESUMEN DEL DISPOSITIVO")
    print("=" * 60)
    device = Device.objects.get(device_identifier=DEVICE_ID)
    print(f"ID del dispositivo: {device.device_identifier}")
    print(f"Empleado:           {device.employee.get_full_name()}")
    print(f"Email:              {device.employee.email}")
    print(f"Supervisor:         {device.supervisor.get_full_name()}")
    print(f"Empresa:            {device.company.name}")
    print(f"Estado:             {'Activo' if device.is_active else 'Inactivo'}")
    print(f"Última conexión:    {device.last_connection or 'Nunca'}")
    print("=" * 60)
    print("\n✅ DISPOSITIVO LISTO PARA RECIBIR DATOS VÍA MQTT")
    print(f"   Topic: devices/{DEVICE_ID}/sensors")
    print("=" * 60)
    
except User.DoesNotExist:
    print(f"✗ ERROR: No se encontró el empleado con email: {EMPLOYEE_EMAIL}")
    print("   Verifica que el usuario existe y tiene rol 'employee'")
except Exception as e:
    print(f"✗ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
