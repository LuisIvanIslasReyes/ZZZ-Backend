"""
Script de prueba para crear un dispositivo directamente.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser
from apps.devices.models import Device

def create_device_test():
    """Crear un dispositivo de prueba."""
    try:
        # Obtener el empleado
        employee = CustomUser.objects.get(email='empleado8@gmail.com')
        print(f"✅ Empleado encontrado: {employee.get_full_name()}")
        
        # Verificar datos necesarios
        print(f"   - Empresa: {employee.company.name if employee.company else 'N/A'}")
        print(f"   - Supervisor: {employee.supervisor.get_full_name() if employee.supervisor else 'N/A'}")
        
        if not employee.supervisor:
            print("❌ ERROR: El empleado no tiene supervisor asignado")
            return
        
        if not employee.company:
            print("❌ ERROR: El empleado no tiene empresa asignada")
            return
        
        # Verificar si ya tiene dispositivo
        existing = Device.objects.filter(employee=employee).first()
        if existing:
            print(f"⚠️  El empleado ya tiene un dispositivo: {existing.device_identifier}")
            return
        
        # Crear el dispositivo
        device_id = "ESP32-02"
        
        # Verificar que el device_id no exista
        if Device.objects.filter(device_identifier=device_id).exists():
            print(f"❌ ERROR: Ya existe un dispositivo con ID {device_id}")
            return
        
        print(f"\n🔨 Creando dispositivo {device_id}...")
        
        device = Device.objects.create(
            device_identifier=device_id,
            employee=employee,
            supervisor=employee.supervisor,
            company=employee.company,
            is_active=True
        )
        
        print(f"✅ Dispositivo creado exitosamente!")
        print(f"   - ID: {device.device_identifier}")
        print(f"   - Empleado: {device.employee.get_full_name()}")
        print(f"   - Supervisor: {device.supervisor.get_full_name()}")
        print(f"   - Empresa: {device.company.name}")
        print(f"   - Activo: {device.is_active}")
        
    except CustomUser.DoesNotExist:
        print("❌ ERROR: No se encontró el empleado")
    except Exception as e:
        print(f"❌ ERROR al crear dispositivo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_device_test()
