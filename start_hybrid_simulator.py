"""
Script para iniciar un simulador híbrido que usa:
- BPM reales del ESP32 (XD58C)
- SpO2, acelerómetro y otras métricas simuladas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser
from apps.analytics.simulator_manager import simulator_manager

def start_hybrid_simulator():
    """Inicia un simulador híbrido para Germán Garmendia"""
    
    print("=" * 70)
    print("🔧 INICIANDO SIMULADOR HÍBRIDO")
    print("=" * 70)
    
    # Buscar empleado
    try:
        employee = CustomUser.objects.get(email='orrantia@gmail.com', role='employee')
        print(f"✅ Empleado encontrado: {employee.get_full_name()}")
    except CustomUser.DoesNotExist:
        print("❌ Error: Empleado 'orrantia@gmail.com' no encontrado")
        return
    
    # Verificar si ya tiene un simulador activo
    active_sims = simulator_manager.get_active_sessions()
    employee_sim = [sim for sim in active_sims if sim.employee_id == employee.id]
    if employee_sim:
        print("⚠️  Ya existe un simulador activo para este empleado")
        response = input("¿Detener el simulador existente? (s/n): ")
        if response.lower() == 's':
            for sim in employee_sim:
                simulator_manager.stop_simulator(sim.id)
                print(f"✅ Simulador {sim.id} detenido")
        else:
            return
    
    # Crear sesión de simulador
    from apps.analytics.simulator_models import SimulatorSession
    
    try:
        # Crear sesión en BD
        session = SimulatorSession.objects.create(
            employee=employee,
            device_id='ESP32-001',
            fatigue_profile='normal',
            base_heart_rate=70,
        )
        
        # Iniciar el simulador
        simulator_manager.start_simulator(session.id)
        
        print(f"\n✅ Simulador híbrido creado exitosamente")
        print(f"   ID de sesión: {session.id}")
        print(f"   Device ID: {session.device_id}")
        print(f"   Empleado: {employee.get_full_name()}")
        print(f"   Modo: Híbrido (datos simulados)")
        print("\n" + "=" * 70)
        print("💡 El simulador generará:")
        print("   • Todas las métricas para el modelo ML")
        print("   • El dashboard mostrará BPM reales del ESP32")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error al crear simulador: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    start_hybrid_simulator()
