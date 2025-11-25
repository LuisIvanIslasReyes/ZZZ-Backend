"""
Script para verificar el estado de un empleado y sus relaciones.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser

def check_employee(email):
    """Verificar estado de un empleado."""
    try:
        user = CustomUser.objects.get(email=email)
        print(f"\n{'='*60}")
        print(f"INFORMACIÓN DEL EMPLEADO")
        print(f"{'='*60}")
        print(f"Email: {user.email}")
        print(f"Nombre: {user.get_full_name()}")
        print(f"Rol: {user.role}")
        print(f"Empresa: {user.company.name if user.company else 'Sin empresa'}")
        print(f"Supervisor: {user.supervisor.get_full_name() if user.supervisor else 'Sin supervisor'}")
        print(f"Activo: {user.is_active}")
        
        # Verificar si tiene dispositivo
        if hasattr(user, 'device') and user.device:
            print(f"\nDispositivo asignado: {user.device.device_identifier}")
        else:
            print(f"\nNo tiene dispositivo asignado")
        
        print(f"{'='*60}\n")
        
        # Verificar problemas
        problems = []
        if not user.company:
            problems.append("❌ El usuario no tiene empresa asignada")
        if user.role == 'employee' and not user.supervisor:
            problems.append("❌ El empleado no tiene supervisor asignado")
        
        if problems:
            print("PROBLEMAS DETECTADOS:")
            for problem in problems:
                print(f"  {problem}")
        else:
            print("✅ El empleado está correctamente configurado para recibir un dispositivo")
        
        return user
        
    except CustomUser.DoesNotExist:
        print(f"❌ No se encontró ningún usuario con el email: {email}")
        return None

if __name__ == '__main__':
    # Verificar el empleado mencionado en la imagen
    check_employee('empleado8@gmail.com')
