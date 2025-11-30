"""Script para monitorear simuladores en tiempo real."""
import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.analytics.simulator_models import SimulatorSession
from apps.analytics.simulator_manager import simulator_manager

print("=" * 70)
print("🔴 MONITOR DE SIMULADORES EN TIEMPO REAL")
print("=" * 70)
print("\nPresiona Ctrl+C para detener el monitoreo\n")

try:
    while True:
        # Limpiar pantalla (opcional)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 70)
        print(f"🔴 MONITOR EN VIVO - {time.strftime('%H:%M:%S')}")
        print("=" * 70)
        
        # Sesiones en BD
        running = SimulatorSession.objects.filter(status='running')
        
        print(f"\n📊 Simuladores RUNNING en BD: {running.count()}")
        
        for session in running:
            print(f"\n┌─ {session.device_id} ({session.employee.get_full_name()})")
            print(f"│  💓 Fatiga Actual: {session.current_fatigue:.1f}%")
            print(f"│  🏃 Actividad: {session.activity_mode}")
            print(f"│  📤 Mensajes enviados: {session.messages_sent}")
            print(f"│  ⏱️  Iniciado: {session.started_at.strftime('%H:%M:%S')}")
            
            # Stats en memoria
            stats = simulator_manager.get_simulator_stats(session.id)
            if stats:
                print(f"│  🔥 En memoria: ✅")
                print(f"│     • Fatiga: {stats.get('fatigue_level', 0):.1f}%")
                print(f"│     • HR: {stats.get('heart_rate', 0)} bpm")
                print(f"│     • SpO2: {stats.get('spo2', 0)}%")
                print(f"│     • Mensajes: {stats.get('messages_sent', 0)}")
            else:
                print(f"│  🔥 En memoria: ❌ (no encontrado)")
            
            print(f"└{'─' * 68}")
        
        # Simuladores en memoria
        active_ids = simulator_manager.get_active_sessions()
        print(f"\n💾 Total en memoria: {len(active_ids)}")
        if active_ids:
            print(f"   IDs activos: {active_ids}")
        
        print(f"\n⏱️  Siguiente actualización en 3 segundos...")
        print("   Presiona Ctrl+C para salir")
        
        time.sleep(3)
        
except KeyboardInterrupt:
    print("\n\n✅ Monitor detenido")
    print("=" * 70)
