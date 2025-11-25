"""
Comando de Django para procesar métricas de sensores.
Uso: python manage.py process_metrics
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.sensors.processors import metrics_processor
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.devices.models import Device
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Procesa datos de sensores y genera métricas procesadas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--window-minutes',
            type=int,
            default=1,
            help='Tamaño de la ventana de procesamiento en minutos (default: 1)'
        )
        parser.add_argument(
            '--device',
            type=str,
            help='Procesar solo un dispositivo específico (device_identifier)'
        )
        parser.add_argument(
            '--hours-back',
            type=int,
            default=24,
            help='Procesar datos de las últimas N horas (default: 24)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Procesar todos los datos históricos disponibles'
        )

    def handle(self, *args, **options):
        window_minutes = options['window_minutes']
        device_id = options.get('device')
        hours_back = options['hours_back']
        process_all = options['all']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('PROCESADOR DE MÉTRICAS DE SENSORES'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        # Configurar procesador
        processor = metrics_processor
        processor.window_minutes = window_minutes
        
        # Determinar dispositivos a procesar
        if device_id:
            devices = Device.objects.filter(device_identifier=device_id, is_active=True)
            if not devices.exists():
                self.stdout.write(self.style.ERROR(f'❌ Dispositivo no encontrado: {device_id}'))
                return
        else:
            devices = Device.objects.filter(is_active=True)
        
        self.stdout.write(f'📱 Dispositivos a procesar: {devices.count()}')
        
        # Determinar ventanas de tiempo
        now = timezone.now()
        
        if process_all:
            # Procesar desde el primer dato disponible
            first_data = SensorData.objects.order_by('timestamp').first()
            if not first_data:
                self.stdout.write(self.style.WARNING('⚠️  No hay datos de sensores disponibles'))
                return
            start_time = first_data.timestamp
            self.stdout.write(f'⏰ Procesando desde: {start_time}')
        else:
            start_time = now - timedelta(hours=hours_back)
            self.stdout.write(f'⏰ Procesando últimas {hours_back} horas')
        
        self.stdout.write(f'⏱️  Tamaño de ventana: {window_minutes} minuto(s)\n')
        
        # Procesar ventanas
        total_processed = 0
        total_windows = 0
        
        for device in devices:
            self.stdout.write(f'\n🔄 Procesando: {device.device_identifier}')
            
            # Obtener rango de datos del dispositivo
            device_data = SensorData.objects.filter(
                device=device,
                timestamp__gte=start_time
            ).order_by('timestamp')
            
            if not device_data.exists():
                self.stdout.write(self.style.WARNING(f'   ⚠️  Sin datos para este dispositivo'))
                continue
            
            first_timestamp = device_data.first().timestamp
            last_timestamp = device_data.last().timestamp
            
            self.stdout.write(f'   📊 Datos disponibles: {device_data.count()} registros')
            self.stdout.write(f'   📅 Rango: {first_timestamp} → {last_timestamp}')
            
            # Generar ventanas
            current = first_timestamp
            window_delta = timedelta(minutes=window_minutes)
            device_windows = 0
            
            while current < last_timestamp:
                window_end = current + window_delta
                
                # Verificar si ya existe métrica procesada para esta ventana
                existing = ProcessedMetrics.objects.filter(
                    device=device,
                    window_start=current
                ).exists()
                
                if not existing:
                    result = processor.process_device_window(device, current, window_end)
                    if result:
                        device_windows += 1
                        total_processed += 1
                
                total_windows += 1
                current = window_end
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ Ventanas procesadas: {device_windows}'))
        
        # Resumen final
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'📊 Total de ventanas evaluadas: {total_windows}')
        self.stdout.write(f'✅ Métricas nuevas generadas: {total_processed}')
        self.stdout.write(f'📈 Total en BD: {ProcessedMetrics.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        if total_processed > 0:
            self.stdout.write(self.style.SUCCESS('🎉 Procesamiento completado exitosamente!\n'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  No se generaron métricas nuevas (pueden ya existir)\n'))
