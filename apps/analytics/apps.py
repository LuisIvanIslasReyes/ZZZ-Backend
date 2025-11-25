from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    
    def ready(self):
        """
        Inicia servicios automáticos cuando Django arranca.
        """
        import sys
        import os
        
        # Solo iniciar en el proceso principal (no en migraciones, shell, etc.)
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            # Solo en el proceso principal de runserver
            if os.environ.get('RUN_MAIN') == 'true':
                self._print_startup_banner()
            
            try:
                # Pausar simuladores huérfanos (que quedaron activos por cierre abrupto)
                self._pause_orphan_simulators()
                
                from apps.analytics.ml_scheduler import start_ml_scheduler
                
                # Iniciar scheduler de análisis ML
                start_ml_scheduler()
                
                logger.info("✅ Sistema de análisis ML activo")
                
            except Exception as e:
                logger.error(f"❌ Error iniciando servicios: {e}")
    
    def _print_startup_banner(self):
        """Imprime un banner bonito al iniciar."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     🏥  SISTEMA DE MONITOREO DE FATIGA LABORAL  🏥           ║
║                                                               ║
║     • Detección de anomalías en tiempo real                   ║
║     • Recomendaciones automáticas ML                          ║
║     • Procesamiento continuo de métricas                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        print(banner)
    
    def _pause_orphan_simulators(self):
        """
        Pausa simuladores que quedaron activos en la BD pero no están corriendo.
        """
        try:
            from apps.analytics.simulator_models import SimulatorSession
            
            # Buscar sesiones activas
            active_sessions = SimulatorSession.objects.filter(status='running')
            
            if active_sessions.exists():
                paused_count = active_sessions.update(status='paused')
                if paused_count > 0:
                    logger.info(f"⏸️  {paused_count} simulador(es) pausado(s)")
                
        except Exception as e:
            pass  # Silencioso si falla
