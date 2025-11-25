"""
Script para crear usuarios de prueba completos
Ejecutar desde el directorio del backend: python SCRIPTS/create_test_users.py
"""
import os
import sys
import django

# Configurar el path y Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser

def create_test_users():
    print("=" * 70)
    print("CREANDO USUARIOS DE PRUEBA")
    print("=" * 70)
    
    # 1. Crear Admin
    try:
        admin, created = CustomUser.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'Principal',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'department': 'Administración',
                'position': 'Administrador del Sistema'
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            print(f"✅ Admin creado: {admin.email}")
        else:
            print(f"⚠️  Admin ya existe: {admin.email}")
    except Exception as e:
        print(f"❌ Error al crear Admin: {e}")
        return
    
    # 2. Crear Supervisor
    try:
        supervisor, created = CustomUser.objects.get_or_create(
            email='supervisor@example.com',
            defaults={
                'first_name': 'Juan',
                'last_name': 'Supervisor',
                'role': 'supervisor',
                'is_active': True,
                'department': 'Producción',
                'position': 'Supervisor de Planta',
                'phone': '+52 123 456 7890'
            }
        )
        if created:
            supervisor.set_password('super123')
            supervisor.save()
            print(f"✅ Supervisor creado: {supervisor.email}")
        else:
            # Actualizar admin si no está asignado
            if not supervisor.admin:
                supervisor.admin = admin
                supervisor.save()
            print(f"⚠️  Supervisor ya existe: {supervisor.email}")
    except Exception as e:
        print(f"❌ Error al crear Supervisor: {e}")
        return
    
    # 3. Crear Empleados
    employees_data = [
        {
            'email': 'employee1@example.com',
            'first_name': 'Carlos',
            'last_name': 'García',
            'department': 'Producción',
            'position': 'Operador de Máquina',
            'phone': '+52 123 456 7891'
        },
        {
            'email': 'employee2@example.com',
            'first_name': 'María',
            'last_name': 'López',
            'department': 'Producción',
            'position': 'Operador de Línea',
            'phone': '+52 123 456 7892'
        },
        {
            'email': 'employee3@example.com',
            'first_name': 'Pedro',
            'last_name': 'Martínez',
            'department': 'Producción',
            'position': 'Técnico de Mantenimiento',
            'phone': '+52 123 456 7893'
        },
        {
            'email': 'employee4@example.com',
            'first_name': 'Ana',
            'last_name': 'Rodríguez',
            'department': 'Producción',
            'position': 'Operador de Empaque',
            'phone': '+52 123 456 7894'
        },
    ]
    
    for emp_data in employees_data:
        try:
            employee, created = CustomUser.objects.get_or_create(
                email=emp_data['email'],
                defaults={
                    **emp_data,
                    'role': 'employee',
                    'is_active': True,
                    'supervisor': supervisor
                }
            )
            if created:
                employee.set_password('emp123')
                employee.save()
                print(f"✅ Empleado creado: {employee.email} - {employee.first_name} {employee.last_name}")
            else:
                # Actualizar supervisor si no está asignado
                if not employee.supervisor:
                    employee.supervisor = supervisor
                    employee.save()
                print(f"⚠️  Empleado ya existe: {employee.email}")
        except Exception as e:
            print(f"❌ Error al crear empleado {emp_data['email']}: {e}")
    
    # Resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE USUARIOS CREADOS")
    print("=" * 70)
    print(f"Total Admins:      {CustomUser.objects.filter(role='admin').count()}")
    print(f"Total Supervisores: {CustomUser.objects.filter(role='supervisor').count()}")
    print(f"Total Empleados:    {CustomUser.objects.filter(role='employee').count()}")
    
    print("\n" + "=" * 70)
    print("CREDENCIALES PARA INICIAR SESIÓN")
    print("=" * 70)
    print("\n📱 ADMIN:")
    print("   Email:    admin@example.com")
    print("   Password: admin123")
    
    print("\n👷 SUPERVISOR:")
    print("   Email:    supervisor@example.com")
    print("   Password: super123")
    
    print("\n👤 EMPLEADOS:")
    print("   Email:    employee1@example.com (y employee2, employee3, employee4)")
    print("   Password: emp123 (para todos)")
    
    print("\n" + "=" * 70)
    print("💡 TIP: Para ver los empleados, inicia sesión como ADMIN o SUPERVISOR")
    print("=" * 70)

if __name__ == '__main__':
    create_test_users()
