"""
Management command para probar el sistema de simuladores completo.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.analytics.simulator_models import SimulatorSession
from apps.analytics.simulator_manager import simulator_manager
from apps.analytics.ml_scheduler import ml_scheduler
import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Prueba el sistema completo de simuladores con ML en tiempo real'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Duración de la prueba en segundos (default: 60)'
        )
    
    def handle(self, *args, **options):
        duration = options['duration']
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🚀 PRUEBA DEL SISTEMA COMPLETO DE SIMULADORES'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # 1. Verificar empleados
        self.stdout.write('\n📋 1. Verificando empleados...')
        employees = User.objects.filter(role='employee', is_active=True)
        self.stdout.write(f'   ✅ {employees.count()} empleados disponibles')
        
        if employees.count() < 2:
            self.stdout.write(self.style.ERROR('   ❌ Se necesitan al menos 2 empleados'))
            return
        
        # 2. Crear sesiones de simuladores
        self.stdout.write('\n🖥️  2. Creando sesiones de simuladores...')
        
        test_employees = employees[:2]
        sessions_created = []
        
        for i, emp in enumerate(test_employees, 1):
            fatigue_profiles = ['rested', 'tired', 'fatigued']
            activity_modes = ['light', 'moderate', 'heavy']
            
            session = SimulatorSession.objects.create(
                employee=emp,
                device_id=f'ESP32-TEST-{i:03d}',
                fatigue_profile=fatigue_profiles[i % 3],
                activity_mode=activity_modes[i % 3],
                base_heart_rate=70 + (i * 5),
                base_spo2=97.0,
                initial_fatigue=20 + (i * 15),
                fatigue_rate=0.5 + (i * 0.2),
            )
            sessions_created.append(session)
            self.stdout.write(f'   ✅ Sesión creada: {session.device_id} para {emp.get_full_name()}')
        
        # 3. Iniciar simuladores
        self.stdout.write('\n▶️  3. Iniciando simuladores...')
        
        for session in sessions_created:
            success = simulator_manager.start_simulator(session.id)
            if success:
                self.stdout.write(f'   ✅ Simulador iniciado: {session.device_id}')
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ Error iniciando: {session.device_id}'))
        
        # 4. Verificar ML Scheduler
        self.stdout.write('\n🤖 4. Verificando ML Scheduler...')
        if ml_scheduler.is_running:
            self.stdout.write('   ✅ ML Scheduler está activo')
        else:
            self.stdout.write(self.style.WARNING('   ⚠️  ML Scheduler no está activo'))
        
        # 5. Monitorear durante X segundos
        self.stdout.write(f'\n⏱️  5. Monitoreando durante {duration} segundos...')
        self.stdout.write('   (Presiona Ctrl+C para detener antes)')
        
        try:
            start_time = time.time()
            last_stats_time = start_time
            
            while (time.time() - start_time) < duration:
                # Mostrar stats cada 10 segundos
                if time.time() - last_stats_time >= 10:
                    self.stdout.write('\n   📊 Estadísticas actuales:')
                    
                    for session in sessions_created:
                        stats = simulator_manager.get_simulator_stats(session.id)
                        if stats:
                            self.stdout.write(
                                f'      - {stats["device_id"]}: '
                                f'Fatiga={stats["current_fatigue"]:.1f}%, '
                                f'Mensajes={stats["messages_sent"]}, '
                                f'Actividad={stats["activity_mode"]}'
                            )
                    
                    # Verificar alertas generadas
                    from apps.analytics.models import FatigueAlert
                    recent_alerts = FatigueAlert.objects.filter(
                        employee__in=test_employees,
                        is_resolved=False
                    ).count()
                    
                    if recent_alerts > 0:
                        self.stdout.write(self.style.WARNING(f'      ⚠️  {recent_alerts} alerta(s) nueva(s) generada(s)'))
                    
                    # Verificar recomendaciones
                    from apps.analytics.models import RoutineRecommendation
                    recent_recs = RoutineRecommendation.objects.filter(
                        employee__in=test_employees,
                        is_applied=False
                    ).count()
                    
                    if recent_recs > 0:
                        self.stdout.write(self.style.WARNING(f'      💡 {recent_recs} recomendación(es) nueva(s)'))
                    
                    last_stats_time = time.time()
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n\n⏸️  Prueba interrumpida por el usuario'))
        
        # 6. Detener simuladores
        self.stdout.write('\n\n🛑 6. Deteniendo simuladores...')
        
        for session in sessions_created:
            success = simulator_manager.stop_simulator(session.id)
            if success:
                session.refresh_from_db()
                self.stdout.write(
                    f'   ✅ {session.device_id} detenido: '
                    f'{session.messages_sent} mensajes enviados'
                )
        
        # 7. Resumen final
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN FINAL'))
        self.stdout.write('=' * 70)
        
        for session in sessions_created:
            session.refresh_from_db()
            self.stdout.write(f'\n📱 {session.device_id}:')
            self.stdout.write(f'   - Empleado: {session.employee.get_full_name()}')
            self.stdout.write(f'   - Mensajes enviados: {session.messages_sent}')
            self.stdout.write(f'   - Fatiga final: {session.current_fatigue:.1f}%')
            self.stdout.write(f'   - Duración: {(session.stopped_at - session.started_at).seconds}s')
        
        # Alertas totales
        from apps.analytics.models import FatigueAlert
        total_alerts = FatigueAlert.objects.filter(
            employee__in=test_employees
        ).count()
        self.stdout.write(f'\n⚠️  Total de alertas generadas: {total_alerts}')
        
        # Recomendaciones totales
        from apps.analytics.models import RoutineRecommendation
        total_recs = RoutineRecommendation.objects.filter(
            employee__in=test_employees
        ).count()
        self.stdout.write(f'💡 Total de recomendaciones generadas: {total_recs}')
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ PRUEBA COMPLETADA'))
        self.stdout.write('=' * 70)
