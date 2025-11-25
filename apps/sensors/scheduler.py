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
        logger.info("🔄 Iniciando procesamiento automático de métricas...")
        
        processor = MetricsProcessor(window_minutes=1)
        devices = Device.objects.filter(is_active=True)
        
        total_processed = 0
        
        for device in devices:
            try:
                # Procesar últimos 5 minutos para no sobrecargar
                hours_back = 0.1  # 6 minutos
                result = processor.process_device_data(device, hours_back=hours_back)
                
                if result and result.get('windows_processed', 0) > 0:
                    windows = result['windows_processed']
                    total_processed += windows
                    logger.info(f"  ✅ {device.device_identifier}: {windows} ventanas procesadas")
                    
            except Exception as e:
                logger.error(f"  ❌ Error procesando {device.device_identifier}: {e}")
                continue
        
        if total_processed > 0:
            logger.info(f"✅ Procesamiento automático completado: {total_processed} ventanas totales")
        else:
            logger.debug("ℹ️  No hay datos nuevos para procesar")
            
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
        logger.info("📋 Job programado: Procesar métricas cada 2 minutos")
        
        # Job 2: Limpiar ejecuciones antiguas cada día
        scheduler.add_job(
            cleanup_old_executions,
            trigger=IntervalTrigger(days=1),
            id="cleanup_executions",
            max_instances=1,
            replace_existing=True,
            name="Limpieza de ejecuciones antiguas"
        )
        logger.info("📋 Job programado: Limpiar ejecuciones cada 24 horas")
        
        # Iniciar scheduler
        scheduler.start()
        logger.info("🚀 Scheduler de procesamiento automático iniciado")
        
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
