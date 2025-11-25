"""
Comando de Django para generar datos históricos de prueba
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from apps.sensors.models import ProcessedMetrics
from apps.devices.models import Device


class Command(BaseCommand):
    help = 'Genera datos históricos de prueba para las gráficas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Número de días hacia atrás para generar datos'
        )

    def handle(self, *args, **options):
        days_back = options['days']
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('GENERADOR DE DATOS HISTÓRICOS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Obtener dispositivos activos
        devices = Device.objects.filter(is_active=True)
        
        if not devices.exists():
            self.stdout.write(self.style.ERROR('❌ No hay dispositivos activos'))
            return
        
        self.stdout.write(f'\n📱 Dispositivos: {devices.count()}')
        
        now = timezone.now()
        total_created = 0
        
        for device in devices:
            employee = device.employee
            self.stdout.write(f'\n🔄 {employee.get_full_name()} ({employee.email})')
            
            for day_offset in range(days_back):
                target_date = now - timedelta(days=day_offset)
                metrics_per_day = random.randint(5, 10)
                day_created = 0
                
                for i in range(metrics_per_day):
                    hour = random.randint(8, 20)
                    minute = random.randint(0, 59)
                    
                    window_start = target_date.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    window_end = window_start + timedelta(minutes=1)
                    
                    # Verificar si existe
                    if ProcessedMetrics.objects.filter(
                        device=device,
                        window_start=window_start
                    ).exists():
                        continue
                    
                    # Valores realistas
                    base_fatigue = 50 + (day_offset * 2)
                    hr_base = 75 + random.randint(-10, 10)
                    
                    # Variación por hora
                    hour_factor = 1.0
                    if 8 <= hour <= 10:
                        hour_factor = 0.8
                    elif 14 <= hour <= 16:
                        hour_factor = 1.3
                    elif 18 <= hour <= 20:
                        hour_factor = 1.2
                    
                    fatigue_index = min(100, base_fatigue * hour_factor + random.randint(-5, 5))
                    hr_avg = hr_base + random.randint(-5, 5)
                    spo2_avg = 97.0 + random.uniform(-1.0, 1.5)
                    
                    ProcessedMetrics.objects.create(
                        device=device,
                        employee=employee,
                        window_start=window_start,
                        window_end=window_end,
                        hr_avg=hr_avg,
                        hr_max=hr_avg + random.randint(5, 15),
                        hr_min=hr_avg - random.randint(5, 10),
                        hrv_rmssd=random.uniform(20, 50),
                        hrv_sdnn=random.uniform(15, 40),
                        hr_trend='stable',
                        spo2_avg=spo2_avg,
                        spo2_min=spo2_avg - random.uniform(0.5, 2.0),
                        spo2_variance=random.uniform(0.1, 1.0),
                        desaturation_count=random.randint(0, 2),
                        activity_level=random.uniform(0.5, 2.5),
                        movement_variance=random.uniform(0.1, 0.5),
                        movement_entropy=random.uniform(1.0, 3.0),
                        fatigue_index=fatigue_index,
                        hr_activity_ratio=hr_avg / 1.5,
                    )
                    
                    day_created += 1
                    total_created += 1
                
                date_str = target_date.strftime('%Y-%m-%d')
                self.stdout.write(f'  ✅ {date_str}: {day_created} métricas')
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('✅ COMPLETADO'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'📊 Creadas: {total_created}')
        self.stdout.write(f'📈 Total en BD: {ProcessedMetrics.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n🎉 Recarga el frontend para ver las gráficas!\n'))
