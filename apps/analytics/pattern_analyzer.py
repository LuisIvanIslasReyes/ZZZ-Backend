"""
Analizador de Patrones de Fatiga.
Proporciona análisis estadístico avanzado de patrones de fatiga para empleados.
"""

import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Max, Min, Count, Q, StdDev, F, FloatField
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDate
from collections import defaultdict
import numpy as np

from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import FatigueAlert

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """
    Analiza patrones de fatiga en empleados para identificar tendencias y correlaciones.
    """
    
    def __init__(self, employee, days=7):
        """
        Inicializa el analizador.
        
        Args:
            employee: Usuario empleado a analizar
            days: Número de días a analizar (default: 7)
        """
        self.employee = employee
        self.days = days
        self.cutoff_date = timezone.now() - timedelta(days=days)
        self.metrics = ProcessedMetrics.objects.filter(
            employee=employee,
            window_start__gte=self.cutoff_date
        ).order_by('window_start')
    
    def analyze_all_patterns(self):
        """
        Ejecuta todos los análisis de patrones.
        
        Returns:
            dict: Diccionario con todos los patrones detectados
        """
        if self.metrics.count() < 10:
            logger.warning(f"⚠️  Datos insuficientes para {self.employee.get_full_name()}")
            return None
        
        return {
            'employee': {
                'id': self.employee.id,
                'name': self.employee.get_full_name(),
                'email': self.employee.email
            },
            'analysis_period': {
                'days': self.days,
                'start_date': self.cutoff_date.isoformat(),
                'end_date': timezone.now().isoformat(),
                'data_points': self.metrics.count()
            },
            'overall_stats': self.get_overall_stats(),
            'hourly_patterns': self.analyze_hourly_patterns(),
            'daily_patterns': self.analyze_daily_patterns(),
            'trends': self.analyze_trends(),
            'correlations': self.analyze_correlations(),
            'alert_patterns': self.analyze_alert_patterns(),
            'recovery_patterns': self.analyze_recovery_patterns(),
            'risk_assessment': self.assess_risk_level()
        }
    
    def get_overall_stats(self):
        """
        Estadísticas generales del período.
        """
        stats = self.metrics.aggregate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            min_fatigue=Min('fatigue_index'),
            std_fatigue=StdDev('fatigue_index'),
            avg_hr=Avg('heart_rate_avg'),
            avg_spo2=Avg('spo2_avg'),
            avg_activity=Avg('activity_level')
        )
        
        # Contar episodios de alta fatiga
        high_fatigue_count = self.metrics.filter(fatigue_index__gte=70).count()
        critical_fatigue_count = self.metrics.filter(fatigue_index__gte=85).count()
        
        return {
            'fatigue': {
                'average': round(stats['avg_fatigue'] or 0, 2),
                'maximum': round(stats['max_fatigue'] or 0, 2),
                'minimum': round(stats['min_fatigue'] or 0, 2),
                'std_dev': round(stats['std_fatigue'] or 0, 2),
                'high_episodes': high_fatigue_count,
                'critical_episodes': critical_fatigue_count
            },
            'heart_rate': {
                'average': round(stats['avg_hr'] or 0, 2)
            },
            'spo2': {
                'average': round(stats['avg_spo2'] or 0, 2)
            },
            'activity': {
                'average': round(stats['avg_activity'] or 0, 2)
            }
        }
    
    def analyze_hourly_patterns(self):
        """
        Analiza patrones por hora del día.
        
        Returns:
            dict: Patrones de fatiga por hora
        """
        hourly_data = self.metrics.annotate(
            hour=ExtractHour('window_start')
        ).values('hour').annotate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            count=Count('id'),
            avg_hr=Avg('heart_rate_avg'),
            avg_activity=Avg('activity_level')
        ).filter(count__gte=2).order_by('hour')
        
        hourly_list = list(hourly_data)
        
        # Identificar horas pico y valle
        if hourly_list:
            sorted_by_fatigue = sorted(hourly_list, key=lambda x: x['avg_fatigue'], reverse=True)
            peak_hours = sorted_by_fatigue[:3]
            valley_hours = sorted(hourly_list, key=lambda x: x['avg_fatigue'])[:3]
        else:
            peak_hours = []
            valley_hours = []
        
        return {
            'hourly_breakdown': [
                {
                    'hour': h['hour'],
                    'avg_fatigue': round(h['avg_fatigue'], 2),
                    'max_fatigue': round(h['max_fatigue'], 2),
                    'avg_hr': round(h['avg_hr'], 2),
                    'avg_activity': round(h['avg_activity'], 2),
                    'samples': h['count']
                }
                for h in hourly_list
            ],
            'peak_hours': [
                {
                    'hour': h['hour'],
                    'avg_fatigue': round(h['avg_fatigue'], 2)
                }
                for h in peak_hours
            ],
            'best_hours': [
                {
                    'hour': h['hour'],
                    'avg_fatigue': round(h['avg_fatigue'], 2)
                }
                for h in valley_hours
            ]
        }
    
    def analyze_daily_patterns(self):
        """
        Analiza patrones por día de la semana.
        
        Returns:
            dict: Patrones de fatiga por día
        """
        daily_data = self.metrics.annotate(
            weekday=ExtractWeekDay('window_start')
        ).values('weekday').annotate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            count=Count('id')
        ).filter(count__gte=2).order_by('weekday')
        
        days_map = {
            1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles',
            5: 'Jueves', 6: 'Viernes', 7: 'Sábado'
        }
        
        daily_list = list(daily_data)
        
        # Identificar días con mayor y menor fatiga
        if daily_list:
            sorted_by_fatigue = sorted(daily_list, key=lambda x: x['avg_fatigue'], reverse=True)
            hardest_days = sorted_by_fatigue[:3]
            easiest_days = sorted(daily_list, key=lambda x: x['avg_fatigue'])[:3]
        else:
            hardest_days = []
            easiest_days = []
        
        return {
            'daily_breakdown': [
                {
                    'weekday': d['weekday'],
                    'day_name': days_map.get(d['weekday'], 'Unknown'),
                    'avg_fatigue': round(d['avg_fatigue'], 2),
                    'max_fatigue': round(d['max_fatigue'], 2),
                    'samples': d['count']
                }
                for d in daily_list
            ],
            'hardest_days': [
                {
                    'weekday': d['weekday'],
                    'day_name': days_map.get(d['weekday'], 'Unknown'),
                    'avg_fatigue': round(d['avg_fatigue'], 2)
                }
                for d in hardest_days
            ],
            'easiest_days': [
                {
                    'weekday': d['weekday'],
                    'day_name': days_map.get(d['weekday'], 'Unknown'),
                    'avg_fatigue': round(d['avg_fatigue'], 2)
                }
                for d in easiest_days
            ]
        }
    
    def analyze_trends(self):
        """
        Analiza tendencias temporales de fatiga.
        
        Returns:
            dict: Tendencias detectadas
        """
        # Agrupar por día
        daily_metrics = self.metrics.annotate(
            date=TruncDate('window_start')
        ).values('date').annotate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index')
        ).order_by('date')
        
        daily_list = list(daily_metrics)
        
        if len(daily_list) < 3:
            return {'trend': 'insufficient_data'}
        
        # Calcular tendencia usando regresión lineal simple
        fatigue_values = [d['avg_fatigue'] for d in daily_list]
        x = np.arange(len(fatigue_values))
        
        # Pendiente de la línea de tendencia
        slope = np.polyfit(x, fatigue_values, 1)[0]
        
        # Clasificar tendencia
        if slope > 2:
            trend = 'increasing'
            trend_label = 'Tendencia creciente'
        elif slope < -2:
            trend = 'decreasing'
            trend_label = 'Tendencia decreciente'
        else:
            trend = 'stable'
            trend_label = 'Tendencia estable'
        
        # Calcular variabilidad
        variability = np.std(fatigue_values)
        
        return {
            'trend': trend,
            'trend_label': trend_label,
            'slope': round(float(slope), 3),
            'variability': round(float(variability), 2),
            'daily_averages': [
                {
                    'date': d['date'].isoformat(),
                    'avg_fatigue': round(d['avg_fatigue'], 2),
                    'max_fatigue': round(d['max_fatigue'], 2)
                }
                for d in daily_list
            ]
        }
    
    def analyze_correlations(self):
        """
        Analiza correlaciones entre métricas.
        
        Returns:
            dict: Correlaciones encontradas
        """
        metrics_data = list(self.metrics.values(
            'fatigue_index', 'heart_rate_avg', 'spo2_avg', 
            'activity_level', 'hrv_rmssd'
        ))
        
        if len(metrics_data) < 10:
            return {'correlations': 'insufficient_data'}
        
        # Extraer arrays de datos
        fatigue = np.array([m['fatigue_index'] for m in metrics_data if m['fatigue_index'] is not None])
        hr = np.array([m['heart_rate_avg'] for m in metrics_data if m['heart_rate_avg'] is not None])
        spo2 = np.array([m['spo2_avg'] for m in metrics_data if m['spo2_avg'] is not None])
        activity = np.array([m['activity_level'] for m in metrics_data if m['activity_level'] is not None])
        hrv = np.array([m['hrv_rmssd'] for m in metrics_data if m['hrv_rmssd'] is not None])
        
        correlations = {}
        
        # Calcular correlaciones si hay suficientes datos
        if len(fatigue) > 0 and len(hr) > 0 and len(fatigue) == len(hr):
            correlations['fatigue_hr'] = round(float(np.corrcoef(fatigue, hr)[0, 1]), 3)
        
        if len(fatigue) > 0 and len(spo2) > 0 and len(fatigue) == len(spo2):
            correlations['fatigue_spo2'] = round(float(np.corrcoef(fatigue, spo2)[0, 1]), 3)
        
        if len(fatigue) > 0 and len(activity) > 0 and len(fatigue) == len(activity):
            correlations['fatigue_activity'] = round(float(np.corrcoef(fatigue, activity)[0, 1]), 3)
        
        if len(fatigue) > 0 and len(hrv) > 0 and len(fatigue) == len(hrv):
            correlations['fatigue_hrv'] = round(float(np.corrcoef(fatigue, hrv)[0, 1]), 3)
        
        # Interpretar correlaciones
        interpretations = []
        
        if correlations.get('fatigue_hr', 0) > 0.5:
            interpretations.append("Correlación positiva fuerte entre fatiga y ritmo cardíaco")
        
        if correlations.get('fatigue_spo2', 0) < -0.3:
            interpretations.append("Correlación negativa entre fatiga y oxigenación")
        
        if correlations.get('fatigue_activity', 0) < -0.3:
            interpretations.append("Menor actividad correlacionada con mayor fatiga")
        
        if correlations.get('fatigue_hrv', 0) < -0.3:
            interpretations.append("Menor HRV correlacionada con mayor fatiga (estrés)")
        
        return {
            'correlations': correlations,
            'interpretations': interpretations
        }
    
    def analyze_alert_patterns(self):
        """
        Analiza patrones en las alertas generadas.
        
        Returns:
            dict: Patrones de alertas
        """
        alerts = FatigueAlert.objects.filter(
            employee=self.employee,
            timestamp__gte=self.cutoff_date
        )
        
        total_alerts = alerts.count()
        
        if total_alerts == 0:
            return {
                'total_alerts': 0,
                'message': 'Sin alertas en el período analizado'
            }
        
        # Contar por severidad
        by_severity = alerts.values('severity').annotate(
            count=Count('id')
        )
        
        # Contar por tipo
        by_type = alerts.values('alert_type').annotate(
            count=Count('id')
        )
        
        # Alertas resueltas vs pendientes
        resolved = alerts.filter(is_resolved=True).count()
        pending = alerts.filter(is_resolved=False).count()
        
        return {
            'total_alerts': total_alerts,
            'resolved': resolved,
            'pending': pending,
            'by_severity': {item['severity']: item['count'] for item in by_severity},
            'by_type': {item['alert_type']: item['count'] for item in by_type},
            'resolution_rate': round((resolved / total_alerts * 100), 2) if total_alerts > 0 else 0
        }
    
    def analyze_recovery_patterns(self):
        """
        Analiza patrones de recuperación (cómo baja la fatiga).
        
        Returns:
            dict: Patrones de recuperación
        """
        metrics_list = list(self.metrics.values('window_start', 'fatigue_index').order_by('window_start'))
        
        if len(metrics_list) < 5:
            return {'recovery': 'insufficient_data'}
        
        # Detectar episodios de alta fatiga y su recuperación
        recovery_times = []
        in_high_fatigue = False
        high_fatigue_start = None
        
        for i, metric in enumerate(metrics_list):
            if metric['fatigue_index'] >= 70 and not in_high_fatigue:
                # Inicio de episodio de alta fatiga
                in_high_fatigue = True
                high_fatigue_start = i
            elif metric['fatigue_index'] < 50 and in_high_fatigue:
                # Recuperación completada
                in_high_fatigue = False
                if high_fatigue_start is not None:
                    recovery_time = i - high_fatigue_start
                    recovery_times.append(recovery_time)
        
        if recovery_times:
            avg_recovery = np.mean(recovery_times)
            max_recovery = np.max(recovery_times)
            
            # Clasificar velocidad de recuperación
            if avg_recovery <= 3:
                recovery_speed = 'fast'
                recovery_label = 'Recuperación rápida'
            elif avg_recovery <= 6:
                recovery_speed = 'normal'
                recovery_label = 'Recuperación normal'
            else:
                recovery_speed = 'slow'
                recovery_label = 'Recuperación lenta'
        else:
            avg_recovery = None
            max_recovery = None
            recovery_speed = 'unknown'
            recovery_label = 'Sin episodios de alta fatiga para analizar'
        
        return {
            'recovery_speed': recovery_speed,
            'recovery_label': recovery_label,
            'avg_recovery_time': round(float(avg_recovery), 2) if avg_recovery else None,
            'max_recovery_time': int(max_recovery) if max_recovery else None,
            'episodes_analyzed': len(recovery_times),
            'unit': 'ventanas de medición'
        }
    
    def assess_risk_level(self):
        """
        Evalúa el nivel de riesgo general del empleado.
        
        Returns:
            dict: Evaluación de riesgo
        """
        overall = self.get_overall_stats()
        trends = self.analyze_trends()
        alerts = self.analyze_alert_patterns()
        
        # Factores de riesgo
        risk_score = 0
        risk_factors = []
        
        # Factor 1: Fatiga promedio alta
        avg_fatigue = overall['fatigue']['average']
        if avg_fatigue >= 70:
            risk_score += 3
            risk_factors.append(f"Fatiga promedio crítica ({avg_fatigue:.1f}/100)")
        elif avg_fatigue >= 50:
            risk_score += 2
            risk_factors.append(f"Fatiga promedio elevada ({avg_fatigue:.1f}/100)")
        elif avg_fatigue >= 30:
            risk_score += 1
            risk_factors.append(f"Fatiga promedio moderada ({avg_fatigue:.1f}/100)")
        
        # Factor 2: Tendencia creciente
        if trends.get('trend') == 'increasing':
            risk_score += 2
            risk_factors.append("Tendencia de fatiga creciente")
        
        # Factor 3: Episodios críticos
        critical_episodes = overall['fatigue']['critical_episodes']
        if critical_episodes > 0:
            risk_score += 2
            risk_factors.append(f"{critical_episodes} episodios de fatiga crítica")
        
        # Factor 4: Alertas pendientes
        pending_alerts = alerts.get('pending', 0)
        if pending_alerts > 5:
            risk_score += 2
            risk_factors.append(f"{pending_alerts} alertas pendientes")
        elif pending_alerts > 0:
            risk_score += 1
            risk_factors.append(f"{pending_alerts} alertas pendientes")
        
        # Factor 5: Recuperación lenta
        recovery = self.analyze_recovery_patterns()
        if recovery.get('recovery_speed') == 'slow':
            risk_score += 1
            risk_factors.append("Recuperación lenta de episodios de fatiga")
        
        # Clasificar nivel de riesgo
        if risk_score >= 7:
            risk_level = 'critical'
            risk_label = 'Riesgo Crítico'
            recommendation = 'Acción inmediata requerida'
        elif risk_score >= 5:
            risk_level = 'high'
            risk_label = 'Riesgo Alto'
            recommendation = 'Requiere atención prioritaria'
        elif risk_score >= 3:
            risk_level = 'medium'
            risk_label = 'Riesgo Medio'
            recommendation = 'Monitorear de cerca'
        elif risk_score >= 1:
            risk_level = 'low'
            risk_label = 'Riesgo Bajo'
            recommendation = 'Monitoreo regular'
        else:
            risk_level = 'minimal'
            risk_label = 'Riesgo Mínimo'
            recommendation = 'Continuar monitoreo normal'
        
        return {
            'risk_level': risk_level,
            'risk_label': risk_label,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'recommendation': recommendation
        }
