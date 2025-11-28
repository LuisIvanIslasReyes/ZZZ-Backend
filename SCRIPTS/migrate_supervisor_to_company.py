"""
Script para migrar la lógica de supervisores.

Nueva lógica: Supervisores = Empresa
- Cada empresa debe tener SOLO UN supervisor activo
- Si hay múltiples supervisores para una empresa, se desactivan los demás
- Todos los empleados de una empresa se asignan automáticamente al supervisor activo

Ejecutar desde la raíz del proyecto:
    python SCRIPTS/migrate_supervisor_to_company.py
"""

import os
import sys
import django

# Configurar el entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser
from apps.companies.models import Company
from django.db import transaction


def migrate_supervisors():
    """
    Migra la lógica de supervisores para que cada empresa tenga solo un supervisor activo.
    """
    print("=" * 80)
    print("MIGRACIÓN: SUPERVISOR = EMPRESA")
    print("=" * 80)
    
    companies = Company.objects.all()
    
    if not companies.exists():
        print("\n⚠️  No hay empresas registradas en el sistema.")
        return
    
    print(f"\n📊 Total de empresas: {companies.count()}")
    
    total_supervisors_deactivated = 0
    total_employees_reassigned = 0
    
    with transaction.atomic():
        for company in companies:
            print(f"\n{'='*80}")
            print(f"🏢 Procesando empresa: {company.name}")
            print(f"{'='*80}")
            
            # Obtener todos los supervisores de esta empresa
            supervisors = CustomUser.objects.filter(
                company=company,
                role='supervisor'
            ).order_by('-is_active', '-created_at')  # Priorizar activos y más antiguos
            
            supervisor_count = supervisors.count()
            print(f"   Supervisores encontrados: {supervisor_count}")
            
            if supervisor_count == 0:
                print(f"   ⚠️  ADVERTENCIA: Esta empresa no tiene supervisores.")
                print(f"   💡 Considera crear una cuenta de supervisor para esta empresa.")
                continue
            
            # Mantener solo el primer supervisor activo
            active_supervisor = supervisors.first()
            
            if supervisor_count == 1:
                print(f"   ✅ Esta empresa ya tiene solo 1 supervisor: {active_supervisor.email}")
                if not active_supervisor.is_active:
                    print(f"   ⚠️  El supervisor está inactivo. Considera activarlo.")
            else:
                # Hay múltiples supervisores - desactivar los demás
                print(f"   🔄 Múltiples supervisores detectados. Manteniendo: {active_supervisor.email}")
                
                for idx, supervisor in enumerate(supervisors):
                    if idx == 0:
                        # Este es el supervisor que mantenemos activo
                        if not supervisor.is_active:
                            supervisor.is_active = True
                            supervisor.save()
                            print(f"      ✅ Activado supervisor principal: {supervisor.email}")
                        else:
                            print(f"      ✅ Supervisor principal activo: {supervisor.email}")
                    else:
                        # Desactivar supervisores adicionales
                        if supervisor.is_active:
                            supervisor.is_active = False
                            supervisor.save()
                            total_supervisors_deactivated += 1
                            print(f"      ❌ Desactivado supervisor duplicado: {supervisor.email}")
                        else:
                            print(f"      ⚪ Supervisor ya inactivo: {supervisor.email}")
            
            # Reasignar TODOS los empleados de la empresa al supervisor activo
            employees = CustomUser.objects.filter(
                company=company,
                role='employee'
            )
            
            employee_count = employees.count()
            print(f"\n   👥 Empleados en esta empresa: {employee_count}")
            
            if employee_count > 0 and active_supervisor.is_active:
                reassigned = 0
                for employee in employees:
                    if employee.supervisor != active_supervisor:
                        old_supervisor = employee.supervisor
                        employee.supervisor = active_supervisor
                        employee.save()
                        reassigned += 1
                        if old_supervisor:
                            print(f"      🔄 Reasignado: {employee.email} (de {old_supervisor.email} a {active_supervisor.email})")
                        else:
                            print(f"      ➕ Asignado: {employee.email} a {active_supervisor.email}")
                
                total_employees_reassigned += reassigned
                if reassigned > 0:
                    print(f"   ✅ Total reasignados en esta empresa: {reassigned}")
                else:
                    print(f"   ✅ Todos los empleados ya estaban correctamente asignados")
    
    print(f"\n{'='*80}")
    print("📊 RESUMEN DE LA MIGRACIÓN")
    print(f"{'='*80}")
    print(f"✅ Supervisores desactivados (duplicados): {total_supervisors_deactivated}")
    print(f"✅ Empleados reasignados: {total_employees_reassigned}")
    print(f"\n{'='*80}")
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print(f"{'='*80}\n")
    
    # Mostrar resumen final por empresa
    print("\n📋 ESTADO FINAL POR EMPRESA:")
    print(f"{'='*80}")
    for company in companies:
        active_supervisor = CustomUser.objects.filter(
            company=company,
            role='supervisor',
            is_active=True
        ).first()
        
        inactive_supervisors = CustomUser.objects.filter(
            company=company,
            role='supervisor',
            is_active=False
        ).count()
        
        employees = CustomUser.objects.filter(
            company=company,
            role='employee'
        ).count()
        
        print(f"\n🏢 {company.name}")
        if active_supervisor:
            print(f"   👤 Supervisor activo: {active_supervisor.email}")
        else:
            print(f"   ⚠️  Sin supervisor activo")
        
        if inactive_supervisors > 0:
            print(f"   ⚪ Supervisores inactivos: {inactive_supervisors}")
        
        print(f"   👥 Empleados: {employees}")
    
    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    try:
        migrate_supervisors()
    except Exception as e:
        print(f"\n❌ ERROR durante la migración: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
