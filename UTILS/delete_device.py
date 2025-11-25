"""
Script para eliminar un dispositivo.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.devices.models import Device

def delete_device(device_id):
    """Eliminar un dispositivo."""
    try:
        device = Device.objects.get(device_identifier=device_id)
        print(f"🔍 Dispositivo encontrado:")
        print(f"   - ID: {device.device_identifier}")
        print(f"   - Empleado: {device.employee.get_full_name()}")
        print(f"   - Supervisor: {device.supervisor.get_full_name()}")
        
        device.delete()
        print(f"\n✅ Dispositivo {device_id} eliminado exitosamente!")
        
    except Device.DoesNotExist:
        print(f"❌ No se encontró el dispositivo {device_id}")
    except Exception as e:
        print(f"❌ ERROR al eliminar dispositivo: {str(e)}")

if __name__ == '__main__':
    delete_device('ESP32-02')
