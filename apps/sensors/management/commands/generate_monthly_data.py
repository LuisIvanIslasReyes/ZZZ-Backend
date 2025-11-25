"""
Comando para generar datos de prueba de jornadas completas de 8 horas
durante un mes completo para múltiples empleados.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.devices.models import Device
from apps.sensors.models import SensorData
import random


class Command(BaseCommand):
    help = 'Genera datos de jornadas completas de 8 horas durante un mes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de días a generar (default: 30)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Fecha inicial (formato: YYYY-MM-DD). Default: hace 30 días'
        )
        parser.add_argument(
            '--devices',
            type=str,
            help='IDs de dispositivos separados por coma (default: todos activos)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('GENERADOR DE DATOS DE JORNADAS LABORALES COMPLETAS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        days = options['days']
        
        # Determinar fecha inicial
        if options['start_date']:
            try:
                start_date = timezone.make_aware(
                    datetime.strptime(options['start_date'], '%Y-%m-%d')
                )
            except ValueError:
                self.stdout.write(self.style.ERROR('❌ Formato de fecha inválido. Use YYYY-MM-DD'))
                return
        else:
            start_date = timezone.now() - timedelta(days=days)
        
        # Obtener dispositivos
        if options['devices']:
            device_ids = options['devices'].split(',')
            devices = Device.objects.filter(
                device_identifier__in=device_ids,
                is_active=True
            )
        else:
            devices = Device.objects.filter(is_active=True)
        
        if not devices.exists():
            self.stdout.write(self.style.ERROR('❌ No se encontraron dispositivos activos'))
            return
        
        self.stdout.write(f'\n📱 Dispositivos: {devices.count()}')
        for device in devices:
            self.stdout.write(f'   • {device.device_identifier} ({device.employee.email})')
        
        self.stdout.write(f'\n📅 Generando {days} días de jornadas laborales')
        self.stdout.write(f'📆 Desde: {start_date.strftime("%Y-%m-%d")}')
        self.stdout.write(f'⏰ Horario laboral: 8:00 AM - 5:00 PM (8 horas + 1h almuerzo)')
        self.stdout.write(f'📊 Frecuencia: Cada 5 segundos durante jornada\n')
        
        total_records = 0
        
        for device in devices:
            self.stdout.write(f'\n🔄 Procesando: {device.device_identifier}')
            device_records = 0
            
            for day_offset in range(days):
                current_date = start_date + timedelta(days=day_offset)
                
                # Saltar fines de semana (sábado=5, domingo=6)
                if current_date.weekday() >= 5:
                    continue
                
                # Generar jornada laboral
                records = self._generate_workday(device, current_date)
                device_records += records
                
                if records > 0:
                    self.stdout.write(
                        f'   ✅ {current_date.strftime("%Y-%m-%d")}: {records} registros'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'   📊 Total {device.device_identifier}: {device_records} registros')
            )
            total_records += device_records
        
        self.stdout.write(self.style.SUCCESS(f'\n{"=" * 70}'))
        self.stdout.write(self.style.SUCCESS(f'✅ Generación completada'))
        self.stdout.write(self.style.SUCCESS(f'📊 Total de registros generados: {total_records:,}'))
        self.stdout.write(self.style.SUCCESS(f'🗓️  Días laborales generados: {days - (days // 7 * 2)} días'))
        self.stdout.write(self.style.SUCCESS(f'{"=" * 70}\n'))
    
    def _generate_workday(self, device, date):
        """
        Genera datos para una jornada laboral completa (8 horas).
        
        Horario:
        - 8:00 AM - 12:00 PM (4 horas)
        - 12:00 PM - 1:00 PM (Almuerzo - sin datos)
        - 1:00 PM - 5:00 PM (4 horas)
        
        Total: 8 horas de trabajo efectivo
        """
        records_created = 0
        
        # Sesión matutina: 8:00 AM - 12:00 PM
        morning_start = date.replace(hour=8, minute=0, second=0, microsecond=0)
        morning_end = date.replace(hour=12, minute=0, second=0, microsecond=0)
        records_created += self._generate_work_session(
            device, morning_start, morning_end, fatigue_base=20
        )
        
        # Sesión tarde: 1:00 PM - 5:00 PM
        afternoon_start = date.replace(hour=13, minute=0, second=0, microsecond=0)
        afternoon_end = date.replace(hour=17, minute=0, second=0, microsecond=0)
        records_created += self._generate_work_session(
            device, afternoon_start, afternoon_end, fatigue_base=40
        )
        
        return records_created
    
    def _generate_work_session(self, device, start_time, end_time, fatigue_base):
        """
        Genera datos para una sesión de trabajo con datos cada 5 segundos.
        """
        records = []
        current_time = start_time
        interval = timedelta(seconds=5)
        
        # Calcular duración en horas
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        while current_time < end_time:
            # Calcular progreso en la sesión (0.0 a 1.0)
            progress = (current_time - start_time).total_seconds() / (end_time - start_time).total_seconds()
            
            # Fatiga aumenta con el tiempo (curva exponencial suave)
            fatigue_factor = fatigue_base + (progress ** 1.5) * 30
            
            # Heart Rate: 65-90 BPM con variación según fatiga
            hr_base = 70 + (fatigue_factor / 100) * 20
            heart_rate = round(
                hr_base + random.uniform(-5, 5) + random.uniform(-2, 2),
                1
            )
            heart_rate = max(60, min(100, heart_rate))
            
            # SpO2: 95-99% (mejor al inicio, puede bajar con fatiga)
            spo2_base = 98.5 - (fatigue_factor / 100) * 2
            spo2 = round(
                spo2_base + random.uniform(-0.5, 0.5),
                1
            )
            spo2 = max(94, min(100, spo2))
            
            # Acelerómetro: simular actividad variable
            # Mayor actividad al inicio, menor al final
            activity_level = 1.0 - (progress * 0.5)
            
            accel_x = round(random.uniform(-0.3, 0.3) * activity_level, 3)
            accel_y = round(random.uniform(-0.3, 0.3) * activity_level, 3)
            accel_z = round(9.81 + random.uniform(-0.2, 0.2), 3)
            
            records.append(
                SensorData(
                    device=device,
                    timestamp=current_time,
                    heart_rate=heart_rate,
                    spo2=spo2,
                    accel_x=accel_x,
                    accel_y=accel_y,
                    accel_z=accel_z
                )
            )
            
            current_time += interval
        
        # Bulk create para eficiencia
        if records:
            SensorData.objects.bulk_create(records, batch_size=1000)
        
        return len(records)
    
    def _calculate_fatigue_pattern(self, hour, base_fatigue=30):
        """
        Calcula el patrón de fatiga según la hora del día.
        
        Patrón típico:
        - 8-10 AM: Fatiga baja (recién llegado)
        - 10-12 PM: Fatiga aumenta gradualmente
        - 1-3 PM: Fatiga post-almuerzo (pico)
        - 3-5 PM: Fatiga alta (final del día)
        """
        if 8 <= hour < 10:
            return base_fatigue * 0.6  # 60% de fatiga base
        elif 10 <= hour < 12:
            return base_fatigue * 1.0  # 100% de fatiga base
        elif 13 <= hour < 15:
            return base_fatigue * 1.3  # 130% (post-almuerzo)
        elif 15 <= hour < 17:
            return base_fatigue * 1.5  # 150% (final del día)
        else:
            return base_fatigue
