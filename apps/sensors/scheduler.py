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


@util.close_old_connections
def retrain_ml_model_job():
    """
    Job que re-entrena el modelo ML con datos acumulados.
    Se ejecuta semanalmente para mejorar precisión.
    """
    try:
        import os
        import subprocess
        from pathlib import Path
        from django.conf import settings
        from apps.sensors.models import ProcessedMetrics
        
        logger.info("🤖 Iniciando re-entrenamiento del modelo ML...")
        
        # 1. Verificar que haya suficientes datos nuevos
        metrics_count = ProcessedMetrics.objects.count()
        min_required = 100  # Mínimo de métricas para re-entrenar
        
        if metrics_count < min_required:
            logger.info(f"⏭️  Re-entrenamiento omitido: solo {metrics_count} métricas (mínimo {min_required})")
            return
        
        logger.info(f"📊 Datos disponibles: {metrics_count} métricas procesadas")
        
        # 2. Exportar datos a CSV (si no existe el script, usar datos existentes)
        base_dir = Path(settings.BASE_DIR)
        training_script = base_dir / 'train_simple_model.py'
        
        if not training_script.exists():
            logger.error(f"❌ Script de entrenamiento no encontrado: {training_script}")
            return
        
        # 3. Ejecutar script de entrenamiento
        logger.info("⚙️  Ejecutando entrenamiento...")
        
        # Usar el Python del virtual environment
        python_executable = os.path.join(base_dir, 'venv', 'Scripts', 'python.exe')
        if not os.path.exists(python_executable):
            python_executable = 'python'  # Fallback
        
        result = subprocess.run(
            [python_executable, str(training_script)],
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos máximo
        )
        
        # 4. Verificar resultado
        if result.returncode == 0:
            logger.info("✅ Modelo ML re-entrenado exitosamente")
            logger.debug(f"Salida: {result.stdout[:500]}")  # Primeros 500 caracteres
            
            # 5. Recargar modelo en memoria
            try:
                from apps.analytics.ml_service import ml_service
                if ml_service.load_model():
                    logger.info("✅ Modelo recargado en memoria")
                else:
                    logger.warning("⚠️  Modelo re-entrenado pero no se pudo recargar")
            except Exception as e:
                logger.error(f"❌ Error recargando modelo: {e}")
        else:
            logger.error(f"❌ Error en re-entrenamiento: {result.stderr[:500]}")
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Re-entrenamiento cancelado: timeout de 5 minutos")
    except Exception as e:
        logger.error(f"❌ Error en re-entrenamiento automático: {e}", exc_info=True)


def start_scheduler():
    """
    Inicia el scheduler de procesamiento automático.
    """
    try:
        from apscheduler.jobstores.memory import MemoryJobStore
        
        # Usar MemoryJobStore en lugar de DjangoJobStore para evitar warnings
        jobstores = {
            'default': MemoryJobStore()
        }
        
        scheduler = BackgroundScheduler(
            timezone=timezone.get_current_timezone(),
            jobstores=jobstores
        )
        
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
        
        # Job 3: Re-entrenar modelo ML semanalmente
        scheduler.add_job(
            retrain_ml_model_job,
            trigger=IntervalTrigger(days=7),
            id="retrain_ml_model",
            max_instances=1,
            replace_existing=True,
            name="Re-entrenamiento automático del modelo ML"
        )
        
        # Iniciar scheduler
        scheduler.start()
        logger.info("🚀 Scheduler iniciado:")
        logger.info("   • Procesamiento de métricas: cada 2 minutos")
        logger.info("   • Limpieza de logs: cada 1 día")
        logger.info("   • Re-entrenamiento ML: cada 7 días")
        
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
