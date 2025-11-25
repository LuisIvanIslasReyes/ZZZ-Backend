"""
Listar usuarios del sistema.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser

def list_users():
    """Listar todos los usuarios."""
    print("\n" + "="*60)
    print("USUARIOS EN EL SISTEMA")
    print("="*60)
    
    users = CustomUser.objects.all().order_by('role', 'email')
    
    for user in users:
        print(f"\n{user.role.upper()}: {user.email}")
        print(f"  Nombre: {user.get_full_name()}")
        print(f"  Empresa: {user.company.name if user.company else 'N/A'}")
        if user.role == 'employee':
            print(f"  Supervisor: {user.supervisor.get_full_name() if user.supervisor else 'N/A'}")
    
    print("\n" + "="*60)
    print(f"Total: {users.count()} usuarios")
    print("="*60)

if __name__ == '__main__':
    list_users()
