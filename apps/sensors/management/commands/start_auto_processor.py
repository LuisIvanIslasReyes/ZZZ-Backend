"""
Comando para iniciar el procesador automático de métricas.
Este comando inicia el scheduler en modo standalone.
"""

from django.core.management.base import BaseCommand
import signal
import sys
import time
from apps.sensors.scheduler import start_scheduler, stop_scheduler


class Command(BaseCommand):
    help = 'Inicia el procesador automático de métricas en modo standalone'
    
    def __init__(self):
        super().__init__()
        self.scheduler = None
    
    def handle_shutdown(self, signum, frame):
        """Maneja señales de shutdown (Ctrl+C)"""
        self.stdout.write(self.style.WARNING('\n\n⏹️  Deteniendo scheduler...'))
        stop_scheduler(self.scheduler)
        sys.exit(0)
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=2,
            help='Intervalo en minutos entre procesamiento (default: 2)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('PROCESADOR AUTOMÁTICO DE MÉTRICAS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        interval = options['interval']
        
        self.stdout.write(f'\n⏰ Intervalo de procesamiento: {interval} minuto(s)')
        self.stdout.write('🔄 Iniciando scheduler...\n')
        
        # Configurar manejador de señales
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        # Iniciar scheduler
        self.scheduler = start_scheduler()
        
        if self.scheduler:
            self.stdout.write(self.style.SUCCESS('✅ Scheduler iniciado correctamente'))
            self.stdout.write('\n📊 El procesamiento de métricas se ejecutará automáticamente')
            self.stdout.write('⌨️  Presiona Ctrl+C para detener\n')
            
            # Mantener el proceso vivo
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.handle_shutdown(None, None)
        else:
            self.stdout.write(self.style.ERROR('❌ Error al iniciar scheduler'))
            sys.exit(1)
