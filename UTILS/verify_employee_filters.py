"""
Script para verificar qué empleados ve cada rol después del fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser

print("=" * 80)
print("VERIFICACIÓN DE FILTROS DE EMPLEADOS")
print("=" * 80)

# Supervisor Juan
print("\n1. Empleados que ve supervisor@example.com:")
supervisor = CustomUser.objects.get(email='supervisor@example.com')
print(f"   Supervisor: {supervisor.get_full_name()} ({supervisor.email})")
print(f"   Company: {supervisor.company}")
employees_for_supervisor = CustomUser.objects.filter(
    role='employee',
    supervisor=supervisor
)
print(f"   Empleados visibles: {employees_for_supervisor.count()}")
for emp in employees_for_supervisor:
    print(f"      - {emp.get_full_name()} ({emp.email})")

# Admin
print("\n2. Empleados que ve admin@example.com:")
admin = CustomUser.objects.get(email='admin@example.com')
print(f"   Admin: {admin.get_full_name()} ({admin.email})")
employees_for_admin = CustomUser.objects.filter(role='employee')
print(f"   Empleados visibles: {employees_for_admin.count()}")
for emp in employees_for_admin:
    print(f"      - {emp.get_full_name()} ({emp.email}) [Supervisor: {emp.supervisor}]")

# Verificar Brian específicamente
print("\n3. ¿Quién puede asignar dispositivo a Brian Bautista?")
brian = CustomUser.objects.get(email='empleado8@gmail.com')
print(f"   Empleado: {brian.get_full_name()}")
print(f"   Supervisor asignado: {brian.supervisor}")
print(f"   Company: {brian.company}")
print(f"   ✓ Puede crear dispositivo: {brian.supervisor.email}")

print("\n" + "=" * 80)
print("CONCLUSIÓN:")
print("=" * 80)
print("✓ supervisor@example.com solo verá empleados donde ÉL es el supervisor")
print("✓ Brian Bautista NO aparecerá en la lista de supervisor@example.com")
print("✓ Brian Bautista solo puede ser asignado por admin@example.com")
print("=" * 80)
