"""Script para limpiar sesiones de simuladores en estado error."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.analytics.simulator_models import SimulatorSession
from django.utils import timezone

print("=" * 60)
print("🧹 LIMPIEZA DE SIMULADORES EN ERROR")
print("=" * 60)

# Mostrar estado actual
error_sessions = SimulatorSession.objects.filter(status='error')
print(f"\n❌ Sesiones en error: {error_sessions.count()}")

if error_sessions.count() > 0:
    print("\nDetalles:")
    for s in error_sessions:
        print(f"  • ID: {s.id}, Device: {s.device_id}, Employee: {s.employee.get_full_name()}")
        print(f"    Error: {s.error_message[:100] if s.error_message else 'Sin mensaje'}")
    
    response = input("\n¿Marcar todas como 'stopped'? (s/n): ")
    
    if response.lower() == 's':
        count = error_sessions.update(
            status='stopped',
            stopped_at=timezone.now()
        )
        print(f"\n✅ {count} sesiones actualizadas a 'stopped'")
    else:
        print("\n⚠️  Operación cancelada")
else:
    print("\n✅ No hay sesiones en error")

print("\n" + "=" * 60)
