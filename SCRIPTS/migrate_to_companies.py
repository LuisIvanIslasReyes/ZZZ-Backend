"""
Script para migrar datos existentes al nuevo modelo con empresas.
Crea una empresa por defecto y asigna todos los supervisores y empleados existentes a ella.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.companies.models import Company
from apps.users.models import CustomUser
from apps.devices.models import Device
from django.db import transaction


def migrate_data():
    """
    Migrar datos existentes al nuevo modelo con empresas.
    """
    print("🚀 Iniciando migración de datos...")
    
    with transaction.atomic():
        # 1. Crear empresa por defecto
        print("\n📦 Creando empresa por defecto...")
        default_company, created = Company.objects.get_or_create(
            name="Empresa Demo",
            defaults={
                'contact_email': 'contacto@empresademo.com',
                'contact_phone': '+52 123 456 7890',
                'address': 'Dirección de ejemplo',
                'is_active': True,
                'max_employees': 100
            }
        )
        
        if created:
            print(f"✅ Empresa creada: {default_company.name}")
        else:
            print(f"ℹ️  Empresa ya existe: {default_company.name}")
        
        # 2. Asignar supervisores a la empresa
        print("\n👨‍💼 Asignando supervisores a la empresa...")
        supervisors = CustomUser.objects.filter(role='supervisor', company__isnull=True)
        supervisor_count = supervisors.count()
        
        if supervisor_count > 0:
            supervisors.update(company=default_company)
            print(f"✅ {supervisor_count} supervisores asignados a {default_company.name}")
        else:
            print("ℹ️  No hay supervisores sin empresa")
        
        # 3. Asignar empleados a la empresa
        print("\n👷 Asignando empleados a la empresa...")
        employees = CustomUser.objects.filter(role='employee', company__isnull=True)
        employee_count = employees.count()
        
        if employee_count > 0:
            employees.update(company=default_company)
            print(f"✅ {employee_count} empleados asignados a {default_company.name}")
        else:
            print("ℹ️  No hay empleados sin empresa")
        
        # 4. Asignar dispositivos a la empresa
        print("\n📱 Asignando dispositivos a la empresa...")
        devices = Device.objects.filter(company__isnull=True)
        device_count = devices.count()
        
        if device_count > 0:
            devices.update(company=default_company)
            print(f"✅ {device_count} dispositivos asignados a {default_company.name}")
        else:
            print("ℹ️  No hay dispositivos sin empresa")
        
        # 5. Mostrar resumen
        print("\n" + "="*50)
        print("📊 RESUMEN DE MIGRACIÓN")
        print("="*50)
        print(f"Empresa: {default_company.name}")
        print(f"  - Supervisores: {default_company.supervisor_count}")
        print(f"  - Empleados: {default_company.employee_count}")
        print(f"  - Dispositivos: {Device.objects.filter(company=default_company).count()}")
        print("="*50)
        
        # 6. Verificar integridad
        print("\n🔍 Verificando integridad de datos...")
        
        # Verificar que no haya supervisores sin empresa
        orphan_supervisors = CustomUser.objects.filter(role='supervisor', company__isnull=True).count()
        if orphan_supervisors > 0:
            print(f"⚠️  ADVERTENCIA: {orphan_supervisors} supervisores sin empresa")
        else:
            print("✅ Todos los supervisores tienen empresa asignada")
        
        # Verificar que no haya empleados sin empresa
        orphan_employees = CustomUser.objects.filter(role='employee', company__isnull=True).count()
        if orphan_employees > 0:
            print(f"⚠️  ADVERTENCIA: {orphan_employees} empleados sin empresa")
        else:
            print("✅ Todos los empleados tienen empresa asignada")
        
        # Verificar que no haya dispositivos sin empresa
        orphan_devices = Device.objects.filter(company__isnull=True).count()
        if orphan_devices > 0:
            print(f"⚠️  ADVERTENCIA: {orphan_devices} dispositivos sin empresa")
        else:
            print("✅ Todos los dispositivos tienen empresa asignada")
        
        print("\n✨ Migración completada exitosamente!")


if __name__ == '__main__':
    try:
        migrate_data()
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
