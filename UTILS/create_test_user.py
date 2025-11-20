"""
Script para crear un usuario de prueba en el backend Django
Ejecutar desde el directorio del backend: python create_test_user.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append('c:/Users/bauti/Downloads/respaldos/ZZZ-Backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatigue_detection.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Crear usuario admin de prueba
try:
    # Verificar si ya existe
    if User.objects.filter(username='admin').exists():
        print("❌ El usuario 'admin' ya existe")
        user = User.objects.get(username='admin')
        print(f"✅ Usuario existente: {user.username} - {user.email} - Role: {user.role}")
    else:
        # Crear nuevo usuario
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        print(f"✅ Usuario creado exitosamente:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Password: admin123")
        print(f"   Role: {user.role}")
        
except Exception as e:
    print(f"❌ Error al crear usuario: {e}")

# Crear usuarios adicionales (supervisor y employee)
try:
    if not User.objects.filter(username='supervisor').exists():
        supervisor = User.objects.create_user(
            username='supervisor',
            email='supervisor@example.com',
            password='super123',
            first_name='Supervisor',
            last_name='Test',
            role='supervisor',
            department='Producción'
        )
        print(f"\n✅ Supervisor creado: {supervisor.username} - Password: super123")
    
    if not User.objects.filter(username='employee').exists():
        employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='emp123',
            first_name='Empleado',
            last_name='Test',
            role='employee',
            department='Producción'
        )
        print(f"✅ Empleado creado: {employee.username} - Password: emp123")
        
except Exception as e:
    print(f"❌ Error al crear usuarios adicionales: {e}")

print("\n" + "="*60)
print("CREDENCIALES DE PRUEBA:")
print("="*60)
print("Admin:      admin / admin123")
print("Supervisor: supervisor / super123")
print("Employee:   employee / emp123")
print("="*60)
