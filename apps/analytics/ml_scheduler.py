"""
Scheduler de análisis ML en tiempo real.
Ejecuta análisis periódico de métricas para generar alertas y recomendaciones automáticamente.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings

from apps.analytics.anomaly_detector import AnomalyDetector
from apps.analytics.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


class MLAnalysisScheduler:
    """
    Scheduler para ejecutar análisis de ML en tiempo real.
    Genera alertas y recomendaciones basadas en métricas procesadas.
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self, alert_interval_minutes=2, recommendation_interval_minutes=10):
        """
        Inicia el scheduler con intervalos configurables.
        
        Args:
            alert_interval_minutes: Intervalo para detectar anomalías y crear alertas
            recommendation_interval_minutes: Intervalo para generar recomendaciones
        """
        if self.is_running:
            logger.warning("⚠️  Scheduler ML ya está en ejecución")
            return
        
        try:
            # Job 1: Detección de anomalías y alertas
            self.scheduler.add_job(
                func=self._run_anomaly_detection,
                trigger=IntervalTrigger(minutes=alert_interval_minutes),
                id='ml_anomaly_detection',
                name='Detección de Anomalías ML',
                replace_existing=True,
                max_instances=1  # Solo una instancia a la vez
            )
            
            # Job 2: Generación de recomendaciones
            self.scheduler.add_job(
                func=self._run_recommendation_generation,
                trigger=IntervalTrigger(minutes=recommendation_interval_minutes),
                id='ml_recommendation_generation',
                name='Generación de Recomendaciones ML',
                replace_existing=True,
                max_instances=1
            )
            
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ Scheduler de análisis ML iniciado")
            logger.info(f"   📋 Detección de anomalías: cada {alert_interval_minutes} minutos")
            logger.info(f"   📋 Generación de recomendaciones: cada {recommendation_interval_minutes} minutos")
            
            # Ejecutar inmediatamente la primera vez
            self._run_anomaly_detection()
            
        except Exception as e:
            logger.error(f"❌ Error iniciando scheduler ML: {e}")
    
    def stop(self):
        """Detiene el scheduler."""
        if not self.is_running:
            logger.warning("⚠️  Scheduler ML no está en ejecución")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("🛑 Scheduler de análisis ML detenido")
        except Exception as e:
            logger.error(f"❌ Error deteniendo scheduler ML: {e}")
    
    def _run_anomaly_detection(self):
        """
        Ejecuta detección de anomalías y crea alertas.
        Se ejecuta periódicamente en segundo plano.
        """
        logger.info("🔍 Ejecutando análisis de anomalías ML...")
        
        try:
            detector = AnomalyDetector()
            
            # Analizar métricas de la última hora
            alerts_created = detector.detect_and_create_alerts(window_minutes=60)
            
            if alerts_created > 0:
                logger.info(f"   ⚠️  {alerts_created} alerta(s) generada(s)")
            else:
                logger.info("   ✅ No se detectaron anomalías")
            
            return alerts_created
            
        except Exception as e:
            logger.error(f"❌ Error en detección de anomalías: {e}")
            return 0
    
    def _run_recommendation_generation(self):
        """
        Ejecuta generación de recomendaciones.
        Se ejecuta periódicamente en segundo plano.
        """
        logger.info("💡 Ejecutando generación de recomendaciones ML...")
        
        try:
            service = RecommendationService()
            
            # Generar recomendaciones para todos los supervisores
            result = service.generate_all_recommendations()
            
            total = result.get('total', 0)
            by_type = result.get('by_type', {})
            
            if total > 0:
                logger.info(f"   ✅ {total} recomendación(es) generada(s)")
                logger.info(f"      - Descansos: {by_type.get('break', 0)}")
                logger.info(f"      - Redistribuciones: {by_type.get('task_redistribution', 0)}")
                logger.info(f"      - Rotaciones: {by_type.get('shift_rotation', 0)}")
            else:
                logger.info("   ℹ️  No se generaron nuevas recomendaciones")
            
            return total
            
        except Exception as e:
            logger.error(f"❌ Error en generación de recomendaciones: {e}")
            return 0
    
    def run_manual_analysis(self):
        """
        Ejecuta análisis manual completo (alertas + recomendaciones).
        Útil para testing o ejecución bajo demanda.
        """
        logger.info("🚀 Ejecutando análisis ML manual completo...")
        
        alerts = self._run_anomaly_detection()
        recommendations = self._run_recommendation_generation()
        
        logger.info(f"✅ Análisis manual completado: {alerts} alertas, {recommendations} recomendaciones")
        
        return {
            'alerts_created': alerts,
            'recommendations_created': recommendations
        }


# Instancia global del scheduler
ml_scheduler = MLAnalysisScheduler()


def start_ml_scheduler():
    """
    Función de conveniencia para iniciar el scheduler.
    Puede ser llamada desde AppConfig o management commands.
    """
    ml_scheduler.start(
        alert_interval_minutes=2,  # Alertas cada 2 minutos
        recommendation_interval_minutes=10  # Recomendaciones cada 10 minutos
    )


def stop_ml_scheduler():
    """Función de conveniencia para detener el scheduler."""
    ml_scheduler.stop()
