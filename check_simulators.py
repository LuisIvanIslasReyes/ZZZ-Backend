"""Script para verificar simuladores activos."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.analytics.simulator_models import SimulatorSession
from apps.analytics.simulator_manager import simulator_manager
from django.utils import timezone

print("=" * 70)
print("📊 ESTADO DE SIMULADORES")
print("=" * 70)

# Simuladores en BD
all_sessions = SimulatorSession.objects.all()
running = SimulatorSession.objects.filter(status='running')
stopped = SimulatorSession.objects.filter(status='stopped')
error = SimulatorSession.objects.filter(status='error')

print(f"\n🗄️  Base de Datos:")
print(f"   Total: {all_sessions.count()}")
print(f"   Running: {running.count()}")
print(f"   Stopped: {stopped.count()}")
print(f"   Error: {error.count()}")

print(f"\n📋 Sesiones RUNNING en BD (con datos actualizados):")
for s in running:
    duration = timezone.now() - s.started_at
    minutes = int(duration.total_seconds() / 60)
    
    print(f"\n   ┌─ {s.device_id} ({s.employee.get_full_name()})")
    print(f"   │  💓 Fatiga: {s.current_fatigue:.1f}%")
    print(f"   │  🏃 Actividad: {s.activity_mode}")
    print(f"   │  📤 Mensajes: {s.messages_sent}")
    print(f"   │  ⏱️  Duración: {minutes} minutos")
    print(f"   │  🕐 Última actualización: {s.updated_at.strftime('%H:%M:%S')}")
    print(f"   └{'─' * 65}")

# Simuladores en memoria
active_ids = simulator_manager.get_active_sessions()
print(f"\n💾 Simuladores activos en memoria: {len(active_ids)}")

if len(active_ids) > 0:
    print("\n⚡ Stats en TIEMPO REAL (desde memoria):")
    for session_id in active_ids:
        stats = simulator_manager.get_simulator_stats(session_id)
        if stats:
            accel = stats.get('acceleration', {})
            print(f"\n   🔴 Session ID {session_id} - {stats.get('device_id', 'N/A')}")
            print(f"      ❤️  Heart Rate: {stats.get('heart_rate', 0)} bpm")
            print(f"      🫁 SpO2: {stats.get('spo2', 0)}%")
            print(f"      💤 Fatiga: {stats.get('fatigue_level', 0):.1f}%")
            print(f"      🏃 Actividad: {stats.get('activity_mode', 'N/A')}")
            print(f"      📤 Mensajes: {stats.get('messages_sent', 0)}")
            if accel:
                print(f"      📊 Aceleración: X={accel.get('x', 0):.2f}, Y={accel.get('y', 0):.2f}, Z={accel.get('z', 0):.2f}")
else:
    print("   ⚠️  No hay simuladores en memoria (crear uno desde el frontend)")

print("\n" + "=" * 70)
