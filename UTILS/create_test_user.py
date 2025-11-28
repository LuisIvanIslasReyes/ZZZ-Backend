"""
Script para crear un usuario de prueba en el backend Django
Ejecutar desde el directorio del backend: python create_test_user.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append('c:/Users/bauti/Downloads/respaldos/ZZZ-Backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()

# Crear empresa de prueba
try:
    company, created = Company.objects.get_or_create(
        name='Empresa Demo',
        defaults={
            'address': 'Av. Principal 123',
            'phone': '+52 123 456 7890',
            'industry_type': 'Manufactura',
            'size': 'medium',
            'contact_person': 'Juan Pérez'
        }
    )
    if created:
        print(f"✅ Empresa creada: {company.name}")
    else:
        print(f"ℹ️  Empresa existente: {company.name}")
except Exception as e:
    print(f"❌ Error al crear empresa: {e}")
    company = None

# Crear usuario admin de prueba
try:
    if User.objects.filter(email='admin@zzz.com').exists():
        print("ℹ️  El usuario admin@zzz.com ya existe")
        user = User.objects.get(email='admin@zzz.com')
        print(f"✅ Usuario existente: {user.email} - Role: {user.role}")
    else:
        user = User.objects.create_user(
            email='admin@zzz.com',
            password='cualquiera',
            first_name='Admin',
            last_name='Sistema',
            role='admin',
            is_active=True
        )
        print(f"✅ Admin creado exitosamente:")
        print(f"   Email: {user.email}")
        print(f"   Password: cualquiera")
        print(f"   Role: {user.role}")
        
except Exception as e:
    print(f"❌ Error al crear admin: {e}")

# Crear supervisor (cuenta de empresa)
try:
    if not User.objects.filter(email='supervisor@demo.com').exists() and company:
        supervisor = User.objects.create_user(
            email='supervisor@demo.com',
            password='supervisor123',
            first_name='Supervisor',
            last_name='Demo',
            role='supervisor',
            company=company,
            department='Administración',
            is_active=True
        )
        print(f"\n✅ Supervisor creado: {supervisor.email} - Password: supervisor123")
    else:
        print(f"\nℹ️  Supervisor ya existe o no hay empresa")
        
except Exception as e:
    print(f"❌ Error al crear supervisor: {e}")

# Crear empleado de prueba
try:
    supervisor_user = User.objects.filter(email='supervisor@demo.com').first()
    if not User.objects.filter(email='empleado@demo.com').exists() and company and supervisor_user:
        employee = User.objects.create_user(
            email='empleado@demo.com',
            password='empleado123',
            first_name='Juan',
            last_name='Trabajador',
            role='employee',
            company=company,
            supervisor=supervisor_user,
            department='Producción',
            position='Operador',
            is_active=True
        )
        print(f"✅ Empleado creado: {employee.email} - Password: empleado123")
    else:
        print(f"ℹ️  Empleado ya existe o faltan datos")
        
except Exception as e:
    print(f"❌ Error al crear empleado: {e}")

print("\n" + "="*60)
print("CREDENCIALES DE PRUEBA:")
print("="*60)
print("Admin:      admin@zzz.com / cualquiera")
print("Supervisor: supervisor@demo.com / supervisor123")
print("Empleado:   empleado@demo.com / empleado123")
print("="*60)
