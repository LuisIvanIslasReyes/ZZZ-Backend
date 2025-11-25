"""
Detector automático de anomalías para generación de alertas de fatiga.
Este script analiza métricas procesadas y crea alertas cuando detecta condiciones peligrosas.
"""

import logging
from django.utils import timezone
from datetime import timedelta
from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import FatigueAlert
from apps.devices.models import Device

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detector de anomalías en métricas de fatiga.
    Genera alertas automáticamente cuando detecta condiciones peligrosas.
    """
    
    # Umbrales de detección (ajustados para mayor sensibilidad)
    FATIGUE_CRITICAL = 80  # Fatiga crítica (bajado de 85)
    FATIGUE_HIGH = 60      # Fatiga alta (bajado de 70)
    FATIGUE_MEDIUM = 40    # Fatiga media (bajado de 50)
    
    SPO2_CRITICAL = 88     # SpO2 crítico
    SPO2_LOW = 92          # SpO2 bajo (subido de 90 para mayor sensibilidad)
    
    HR_VERY_HIGH = 140     # Frecuencia cardíaca muy alta (bajado de 160)
    HR_HIGH = 120          # Frecuencia cardíaca alta (bajado de 140)
    
    DESATURATION_WARNING = 2  # Número de desaturaciones para alerta (bajado de 3)
    
    def __init__(self):
        self.alerts_created = 0
    
    def detect_and_create_alerts(self, window_minutes=60):
        """
        Detecta anomalías en las métricas recientes y crea alertas.
        
        Args:
            window_minutes (int): Ventana de tiempo en minutos para analizar métricas recientes
        
        Returns:
            int: Número de alertas creadas
        """
        # Obtener métricas recientes
        time_threshold = timezone.now() - timedelta(minutes=window_minutes)
        recent_metrics = ProcessedMetrics.objects.filter(
            window_end__gte=time_threshold
        ).select_related('device', 'employee')
        
        logger.debug(f"🔍 Analizando {recent_metrics.count()} métricas (ventana: {window_minutes}min)")
        
        for metric in recent_metrics:
            # Verificar si ya existe una alerta reciente para este empleado
            recent_alert = FatigueAlert.objects.filter(
                employee=metric.employee,
                created_at__gte=time_threshold,
                is_resolved=False
            ).first()
            
            # Si ya hay una alerta sin resolver, evitar duplicados
            if recent_alert:
                continue
            
            # Detectar diferentes tipos de anomalías
            self._check_fatigue_level(metric)
            self._check_spo2_level(metric)
            self._check_heart_rate(metric)
            self._check_desaturations(metric)
            self._check_combined_risks(metric)
        
        return self.alerts_created
    
    def _check_fatigue_level(self, metric):
        """Verificar nivel de fatiga."""
        fatigue = metric.fatigue_index
        
        logger.debug(f"Verificando fatiga: {fatigue:.1f} (umbral crítico: {self.FATIGUE_CRITICAL})")
        
        if fatigue >= self.FATIGUE_CRITICAL:
            self._create_alert(
                metric=metric,
                severity='critical',
                message=f'Fatiga CRÍTICA detectada: {fatigue:.1f}/100. Requiere descanso inmediato.',
                additional_data={
                    'type': 'fatigue_critical',
                    'fatigue_index': fatigue,
                    'threshold': self.FATIGUE_CRITICAL
                }
            )
        elif fatigue >= self.FATIGUE_HIGH:
            self._create_alert(
                metric=metric,
                severity='high',
                message=f'Fatiga ALTA detectada: {fatigue:.1f}/100. Se recomienda descanso pronto.',
                additional_data={
                    'type': 'fatigue_high',
                    'fatigue_index': fatigue,
                    'threshold': self.FATIGUE_HIGH
                }
            )
        elif fatigue >= self.FATIGUE_MEDIUM:
            self._create_alert(
                metric=metric,
                severity='medium',
                message=f'Fatiga MODERADA detectada: {fatigue:.1f}/100. Monitorear de cerca.',
                additional_data={
                    'type': 'fatigue_medium',
                    'fatigue_index': fatigue,
                    'threshold': self.FATIGUE_MEDIUM
                }
            )
    
    def _check_spo2_level(self, metric):
        """Verificar nivel de saturación de oxígeno."""
        spo2 = metric.spo2_avg
        
        if spo2 < self.SPO2_CRITICAL:
            self._create_alert(
                metric=metric,
                severity='critical',
                message=f'SpO2 CRÍTICO: {spo2:.1f}%. Atención médica urgente.',
                additional_data={
                    'type': 'spo2_critical',
                    'spo2_avg': spo2,
                    'spo2_min': metric.spo2_min,
                    'threshold': self.SPO2_CRITICAL
                }
            )
        elif spo2 < self.SPO2_LOW:
            self._create_alert(
                metric=metric,
                severity='high',
                message=f'SpO2 BAJO: {spo2:.1f}%. Revisar estado del empleado.',
                additional_data={
                    'type': 'spo2_low',
                    'spo2_avg': spo2,
                    'spo2_min': metric.spo2_min,
                    'threshold': self.SPO2_LOW
                }
            )
    
    def _check_heart_rate(self, metric):
        """Verificar frecuencia cardíaca elevada."""
        hr_avg = metric.hr_avg
        hr_max = metric.hr_max
        
        if hr_avg >= self.HR_VERY_HIGH:
            self._create_alert(
                metric=metric,
                severity='critical',
                message=f'Frecuencia cardíaca MUY ALTA: {hr_avg:.0f} bpm (máx: {hr_max:.0f}). Revisar urgente.',
                additional_data={
                    'type': 'heart_rate_very_high',
                    'hr_avg': hr_avg,
                    'hr_max': hr_max,
                    'threshold': self.HR_VERY_HIGH
                }
            )
        elif hr_avg >= self.HR_HIGH:
            self._create_alert(
                metric=metric,
                severity='high',
                message=f'Frecuencia cardíaca ALTA: {hr_avg:.0f} bpm (máx: {hr_max:.0f}). Monitorear.',
                additional_data={
                    'type': 'heart_rate_high',
                    'hr_avg': hr_avg,
                    'hr_max': hr_max,
                    'threshold': self.HR_HIGH
                }
            )
    
    def _check_desaturations(self, metric):
        """Verificar desaturaciones de oxígeno."""
        desat_count = metric.desaturation_count
        
        if desat_count >= self.DESATURATION_WARNING:
            self._create_alert(
                metric=metric,
                severity='high',
                message=f'Múltiples desaturaciones detectadas: {desat_count} eventos. Revisar condición respiratoria.',
                additional_data={
                    'type': 'multiple_desaturations',
                    'desaturation_count': desat_count,
                    'spo2_avg': metric.spo2_avg,
                    'spo2_min': metric.spo2_min,
                    'threshold': self.DESATURATION_WARNING
                }
            )
    
    def _check_combined_risks(self, metric):
        """Verificar combinación de factores de riesgo."""
        fatigue = metric.fatigue_index
        spo2 = metric.spo2_avg
        hr = metric.hr_avg
        
        # Fatiga alta + SpO2 bajo
        if fatigue >= self.FATIGUE_HIGH and spo2 < self.SPO2_LOW:
            self._create_alert(
                metric=metric,
                severity='critical',
                message=f'ALERTA COMBINADA: Fatiga alta ({fatigue:.1f}) + SpO2 bajo ({spo2:.1f}%). Acción inmediata requerida.',
                additional_data={
                    'type': 'combined_fatigue_spo2',
                    'fatigue_index': fatigue,
                    'spo2_avg': spo2,
                    'hr_avg': hr
                }
            )
        
        # Fatiga alta + HR alta
        elif fatigue >= self.FATIGUE_HIGH and hr >= self.HR_HIGH:
            self._create_alert(
                metric=metric,
                severity='critical',
                message=f'ALERTA COMBINADA: Fatiga alta ({fatigue:.1f}) + HR elevada ({hr:.0f} bpm). Reducir actividad.',
                additional_data={
                    'type': 'combined_fatigue_hr',
                    'fatigue_index': fatigue,
                    'hr_avg': hr,
                    'spo2_avg': spo2
                }
            )
    
    def _create_alert(self, metric, severity, message, additional_data):
        """
        Crear una alerta de fatiga.
        
        Args:
            metric: Métrica procesada que generó la alerta
            severity: Nivel de severidad (low, medium, high, critical)
            message: Mensaje descriptivo de la alerta
            additional_data: Datos adicionales en formato JSON
        """
        try:
            # Extraer el tipo de alerta desde additional_data
            alert_type = additional_data.get('type', 'unknown')
            
            # Enriquecer el mensaje con métricas relevantes
            enriched_message = (
                f"{message} "
                f"[HR: {metric.hr_avg:.0f} bpm, SpO2: {metric.spo2_avg:.1f}%]"
            )
            
            alert = FatigueAlert.objects.create(
                employee=metric.employee,
                supervisor=metric.employee.supervisor,
                severity=severity,
                alert_type=alert_type,
                message=enriched_message,
                fatigue_index=metric.fatigue_index
            )
            
            self.alerts_created += 1
            logger.info(f"   ⚠️  Alerta creada: {severity.upper()} - {message[:50]}...")
            
            return alert
            
        except Exception as e:
            logger.error(f"   ❌ Error al crear alerta: {str(e)}")
            return None
    
    def check_device_offline(self, offline_threshold_minutes=30):
        """
        Detectar dispositivos que han estado offline por mucho tiempo.
        
        Args:
            offline_threshold_minutes: Minutos sin conexión para generar alerta
        
        Returns:
            int: Número de alertas creadas
        """
        logger.info(f"🔍 Verificando dispositivos offline (umbral: {offline_threshold_minutes} min)")
        
        time_threshold = timezone.now() - timedelta(minutes=offline_threshold_minutes)
        
        # Dispositivos activos sin conexión reciente
        offline_devices = Device.objects.filter(
            is_active=True,
            last_connection__lt=time_threshold
        ).select_related('employee')
        
        alerts_created = 0
        
        for device in offline_devices:
            # Verificar si ya existe una alerta de offline reciente
            existing_alert = FatigueAlert.objects.filter(
                employee=device.employee,
                alert_type='device_offline',
                is_resolved=False,
                created_at__gte=time_threshold
            ).first()
            
            if existing_alert:
                continue
            
            offline_minutes = (timezone.now() - device.last_connection).total_seconds() / 60
            
            try:
                FatigueAlert.objects.create(
                    employee=device.employee,
                    supervisor=device.employee.supervisor,
                    severity='medium',
                    alert_type='device_offline',
                    message=f'Dispositivo {device.device_id} sin conexión por {offline_minutes:.0f} minutos. Verificar estado. [Última conexión: {device.last_connection.strftime("%H:%M")}]',
                    fatigue_index=0
                )
                
                alerts_created += 1
                logger.info(f"   ⚠️  Alerta offline: {device.device_id} ({offline_minutes:.0f} min)")
                
            except Exception as e:
                logger.error(f"   ❌ Error al crear alerta offline: {str(e)}")
        
        logger.info(f"✅ Verificación offline completada. Alertas creadas: {alerts_created}")
        return alerts_created


# Instancia global del detector
anomaly_detector = AnomalyDetector()


# Función de conveniencia
def run_anomaly_detection(window_minutes=60, check_offline=True):
    """
    Ejecutar detección de anomalías.
    
    Args:
        window_minutes: Ventana de tiempo para analizar métricas
        check_offline: Si debe verificar dispositivos offline
    
    Returns:
        dict: Resumen de alertas creadas
    """
    detector = AnomalyDetector()
    
    metric_alerts = detector.detect_and_create_alerts(window_minutes=window_minutes)
    offline_alerts = detector.check_device_offline() if check_offline else 0
    
    return {
        'metric_alerts': metric_alerts,
        'offline_alerts': offline_alerts,
        'total_alerts': metric_alerts + offline_alerts
    }
