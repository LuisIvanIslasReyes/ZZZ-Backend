"""
Scheduler para procesamiento automático de métricas.
Este módulo ejecuta tareas en background para procesar datos de sensores.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
from apps.sensors.processors import MetricsProcessor
from apps.devices.models import Device

logger = logging.getLogger(__name__)


@util.close_old_connections
def process_metrics_job():
    """
    Job que procesa métricas de todos los dispositivos activos.
    Se ejecuta periódicamente en background.
    """
    try:
        processor = MetricsProcessor(window_minutes=1)
        devices = Device.objects.filter(is_active=True)
        
        total_processed = 0
        now = timezone.now()
        
        for device in devices:
            try:
                # Procesar últimas ventanas (últimos 5 minutos)
                minutes_back = 5
                window_start = now - timedelta(minutes=minutes_back)
                
                # Verificar si hay datos en este periodo
                from apps.sensors.models import SensorData
                has_data = SensorData.objects.filter(
                    device=device,
                    timestamp__gte=window_start,
                    timestamp__lte=now
                ).exists()
                
                if not has_data:
                    continue
                
                # Procesar ventana actual
                result = processor.process_device_window(device, window_start, now)
                
                if result:
                    total_processed += 1
                    logger.info(f"  ✅ {device.device_identifier}: Ventana procesada")
                    
            except Exception as e:
                logger.error(f"  ❌ Error procesando {device.device_identifier}: {e}")
                continue
        
        if total_processed > 0:
            logger.info(f"📊 {total_processed} dispositivo(s) procesado(s)")
        else:
            logger.debug("ℹ️  Sin datos nuevos")
            
    except Exception as e:
        logger.error(f"❌ Error en procesamiento automático: {e}", exc_info=True)


@util.close_old_connections
def cleanup_old_executions():
    """
    Limpia ejecuciones antiguas del scheduler (más de 7 días).
    """
    try:
        DjangoJobExecution.objects.delete_old_job_executions(7)
        logger.debug("🧹 Limpieza de ejecuciones antiguas completada")
    except Exception as e:
        logger.error(f"❌ Error limpiando ejecuciones: {e}")


def start_scheduler():
    """
    Inicia el scheduler de procesamiento automático.
    """
    try:
        scheduler = BackgroundScheduler(timezone=timezone.get_current_timezone())
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # Job 1: Procesar métricas cada 2 minutos
        scheduler.add_job(
            process_metrics_job,
            trigger=IntervalTrigger(minutes=2),
            id="process_metrics_auto",
            max_instances=1,
            replace_existing=True,
            name="Procesamiento automático de métricas"
        )
        
        # Job 2: Limpiar ejecuciones antiguas cada día
        scheduler.add_job(
            cleanup_old_executions,
            trigger=IntervalTrigger(days=1),
            id="cleanup_executions",
            max_instances=1,
            replace_existing=True,
            name="Limpieza de ejecuciones antiguas"
        )
        
        # Iniciar scheduler
        scheduler.start()
        logger.info("🚀 Scheduler de métricas iniciado (intervalo: 2min)")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ Error iniciando scheduler: {e}", exc_info=True)
        return None


def stop_scheduler(scheduler):
    """
    Detiene el scheduler de forma segura.
    """
    if scheduler:
        try:
            scheduler.shutdown(wait=False)
            logger.info("⏹️  Scheduler detenido")
        except Exception as e:
            logger.error(f"❌ Error deteniendo scheduler: {e}")
