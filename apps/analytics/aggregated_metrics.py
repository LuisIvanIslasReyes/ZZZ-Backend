"""
Sistema de métricas agregadas para cálculo de estadísticas.
Permite pre-calcular métricas diarias, semanales y mensuales para mejorar performance.

Uso:
    python manage.py shell
    >>> from apps.analytics.aggregated_metrics import calculate_daily_metrics, calculate_weekly_metrics
    >>> calculate_daily_metrics()
"""

from django.db.models import Avg, Count, Max, Min, Sum, StdDev, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta
from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation
from apps.users.models import CustomUser
from apps.devices.models import Device
import logging

logger = logging.getLogger(__name__)


class AggregatedMetricsCalculator:
    """
    Calcula y almacena métricas agregadas.
    En una implementación con cache (Redis), estas métricas se guardarían en cache.
    """
    
    def __init__(self):
        self.cache_enabled = False  # Cambiar a True si se configura Redis
    
    def calculate_daily_stats(self, start_date=None, end_date=None):
        """
        Calcula estadísticas diarias agregadas.
        
        Args:
            start_date: Fecha inicio (default: hace 30 días)
            end_date: Fecha fin (default: hoy)
        
        Returns:
            Lista de diccionarios con estadísticas por día
        """
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        logger.info(f"Calculando métricas diarias desde {start_date} hasta {end_date}")
        
        # Métricas agrupadas por día
        daily_metrics = ProcessedMetrics.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            # Fatiga
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            min_fatigue=Min('fatigue_index'),
            std_fatigue=StdDev('fatigue_index'),
            
            # SpO2
            avg_spo2=Avg('spo2_avg'),
            min_spo2=Min('spo2_avg'),
            max_spo2=Max('spo2_avg'),
            
            # Frecuencia Cardíaca
            avg_heart_rate=Avg('heart_rate_avg'),
            max_heart_rate=Max('heart_rate_avg'),
            min_heart_rate=Min('heart_rate_avg'),
            
            # Movimiento
            avg_movement=Avg('movement_intensity'),
            
            # Contadores
            total_readings=Count('id'),
            unique_employees=Count('employee', distinct=True),
            unique_devices=Count('device', distinct=True),
            
            # Niveles de fatiga
            low_fatigue_count=Count('id', filter=Q(fatigue_index__lt=50)),
            medium_fatigue_count=Count('id', filter=Q(fatigue_index__gte=50, fatigue_index__lt=70)),
            high_fatigue_count=Count('id', filter=Q(fatigue_index__gte=70, fatigue_index__lt=85)),
            critical_fatigue_count=Count('id', filter=Q(fatigue_index__gte=85)),
        ).order_by('date')
        
        # Agregar conteo de alertas por día
        alerts_by_day = FatigueAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_alerts=Count('id'),
            critical_alerts=Count('id', filter=Q(severity='critical')),
            high_alerts=Count('id', filter=Q(severity='high')),
            resolved_alerts=Count('id', filter=Q(resolved=True)),
        )
        
        alerts_dict = {item['date']: item for item in alerts_by_day}
        
        # Combinar métricas y alertas
        results = []
        for metric in daily_metrics:
            date = metric['date']
            alerts = alerts_dict.get(date, {})
            
            result = {
                'date': date,
                'metrics': {
                    'fatigue': {
                        'avg': round(metric['avg_fatigue'] or 0, 2),
                        'max': round(metric['max_fatigue'] or 0, 2),
                        'min': round(metric['min_fatigue'] or 0, 2),
                        'std': round(metric['std_fatigue'] or 0, 2),
                    },
                    'spo2': {
                        'avg': round(metric['avg_spo2'] or 0, 2),
                        'min': round(metric['min_spo2'] or 0, 2),
                        'max': round(metric['max_spo2'] or 0, 2),
                    },
                    'heart_rate': {
                        'avg': round(metric['avg_heart_rate'] or 0, 2),
                        'max': round(metric['max_heart_rate'] or 0, 2),
                        'min': round(metric['min_heart_rate'] or 0, 2),
                    },
                    'movement': {
                        'avg': round(metric['avg_movement'] or 0, 2),
                    }
                },
                'counts': {
                    'total_readings': metric['total_readings'],
                    'unique_employees': metric['unique_employees'],
                    'unique_devices': metric['unique_devices'],
                    'fatigue_levels': {
                        'low': metric['low_fatigue_count'],
                        'medium': metric['medium_fatigue_count'],
                        'high': metric['high_fatigue_count'],
                        'critical': metric['critical_fatigue_count'],
                    }
                },
                'alerts': {
                    'total': alerts.get('total_alerts', 0),
                    'critical': alerts.get('critical_alerts', 0),
                    'high': alerts.get('high_alerts', 0),
                    'resolved': alerts.get('resolved_alerts', 0),
                }
            }
            
            results.append(result)
        
        logger.info(f"Calculadas métricas para {len(results)} días")
        return results
    
    def calculate_weekly_stats(self, weeks=4):
        """
        Calcula estadísticas semanales agregadas.
        
        Args:
            weeks: Número de semanas hacia atrás (default: 4)
        
        Returns:
            Lista de diccionarios con estadísticas por semana
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        logger.info(f"Calculando métricas semanales para {weeks} semanas")
        
        weekly_metrics = ProcessedMetrics.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).annotate(
            week=TruncWeek('timestamp')
        ).values('week').annotate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            min_spo2=Min('spo2_avg'),
            avg_heart_rate=Avg('heart_rate_avg'),
            total_readings=Count('id'),
            unique_employees=Count('employee', distinct=True),
        ).order_by('week')
        
        # Alertas por semana
        weekly_alerts = FatigueAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            week=TruncWeek('created_at')
        ).values('week').annotate(
            total_alerts=Count('id'),
            critical_alerts=Count('id', filter=Q(severity='critical')),
        )
        
        alerts_dict = {item['week']: item for item in weekly_alerts}
        
        results = []
        for metric in weekly_metrics:
            week = metric['week']
            alerts = alerts_dict.get(week, {})
            
            results.append({
                'week': week,
                'avg_fatigue': round(metric['avg_fatigue'] or 0, 2),
                'max_fatigue': round(metric['max_fatigue'] or 0, 2),
                'avg_spo2': round(metric['avg_spo2'] or 0, 2),
                'min_spo2': round(metric['min_spo2'] or 0, 2),
                'avg_heart_rate': round(metric['avg_heart_rate'] or 0, 2),
                'total_readings': metric['total_readings'],
                'unique_employees': metric['unique_employees'],
                'total_alerts': alerts.get('total_alerts', 0),
                'critical_alerts': alerts.get('critical_alerts', 0),
            })
        
        logger.info(f"Calculadas métricas para {len(results)} semanas")
        return results
    
    def calculate_monthly_stats(self, months=3):
        """
        Calcula estadísticas mensuales agregadas.
        
        Args:
            months: Número de meses hacia atrás (default: 3)
        
        Returns:
            Lista de diccionarios con estadísticas por mes
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months * 30)
        
        logger.info(f"Calculando métricas mensuales para {months} meses")
        
        monthly_metrics = ProcessedMetrics.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).annotate(
            month=TruncMonth('timestamp')
        ).values('month').annotate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            min_fatigue=Min('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_heart_rate=Avg('heart_rate_avg'),
            total_readings=Count('id'),
            unique_employees=Count('employee', distinct=True),
        ).order_by('month')
        
        # Alertas por mes
        monthly_alerts = FatigueAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_alerts=Count('id'),
            resolved_alerts=Count('id', filter=Q(resolved=True)),
        )
        
        alerts_dict = {item['month']: item for item in monthly_alerts}
        
        results = []
        for metric in monthly_metrics:
            month = metric['month']
            alerts = alerts_dict.get(month, {})
            
            results.append({
                'month': month,
                'avg_fatigue': round(metric['avg_fatigue'] or 0, 2),
                'max_fatigue': round(metric['max_fatigue'] or 0, 2),
                'min_fatigue': round(metric['min_fatigue'] or 0, 2),
                'avg_spo2': round(metric['avg_spo2'] or 0, 2),
                'avg_heart_rate': round(metric['avg_heart_rate'] or 0, 2),
                'total_readings': metric['total_readings'],
                'unique_employees': metric['unique_employees'],
                'total_alerts': alerts.get('total_alerts', 0),
                'resolved_alerts': alerts.get('resolved_alerts', 0),
            })
        
        logger.info(f"Calculadas métricas para {len(results)} meses")
        return results
    
    def calculate_employee_performance(self, employee_id, days=30):
        """
        Calcula métricas de rendimiento para un empleado específico.
        
        Args:
            employee_id: ID del empleado
            days: Días hacia atrás (default: 30)
        
        Returns:
            Diccionario con métricas del empleado
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = ProcessedMetrics.objects.filter(
            employee_id=employee_id,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            min_fatigue=Min('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            min_spo2=Min('spo2_avg'),
            avg_hr=Avg('heart_rate_avg'),
            max_hr=Max('heart_rate_avg'),
            total_readings=Count('id'),
        )
        
        # Alertas
        alerts = FatigueAlert.objects.filter(
            employee_id=employee_id,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).aggregate(
            total=Count('id'),
            critical=Count('id', filter=Q(severity='critical')),
            resolved=Count('id', filter=Q(resolved=True)),
        )
        
        # Recomendaciones
        recommendations = RoutineRecommendation.objects.filter(
            employee_id=employee_id,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).aggregate(
            total=Count('id'),
            applied=Count('id', filter=Q(applied=True)),
        )
        
        return {
            'employee_id': employee_id,
            'period_days': days,
            'metrics': metrics,
            'alerts': alerts,
            'recommendations': recommendations,
        }
    
    def calculate_team_performance(self, supervisor_id, days=30):
        """
        Calcula métricas de rendimiento para el equipo de un supervisor.
        
        Args:
            supervisor_id: ID del supervisor
            days: Días hacia atrás (default: 30)
        
        Returns:
            Diccionario con métricas del equipo
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Obtener empleados del supervisor
        team_employees = CustomUser.objects.filter(
            supervisor_id=supervisor_id,
            role='employee'
        )
        
        team_metrics = ProcessedMetrics.objects.filter(
            employee__in=team_employees,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_hr=Avg('heart_rate_avg'),
            total_readings=Count('id'),
            unique_employees=Count('employee', distinct=True),
        )
        
        # Alertas del equipo
        team_alerts = FatigueAlert.objects.filter(
            supervisor_id=supervisor_id,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).aggregate(
            total=Count('id'),
            critical=Count('id', filter=Q(severity='critical')),
            pending=Count('id', filter=Q(resolved=False)),
        )
        
        return {
            'supervisor_id': supervisor_id,
            'period_days': days,
            'team_size': team_employees.count(),
            'metrics': team_metrics,
            'alerts': team_alerts,
        }


# Funciones de conveniencia para uso directo
def calculate_daily_metrics(start_date=None, end_date=None):
    """
    Calcula métricas diarias.
    
    Usage:
        >>> from apps.analytics.aggregated_metrics import calculate_daily_metrics
        >>> stats = calculate_daily_metrics()
    """
    calculator = AggregatedMetricsCalculator()
    return calculator.calculate_daily_stats(start_date, end_date)


def calculate_weekly_metrics(weeks=4):
    """
    Calcula métricas semanales.
    
    Usage:
        >>> from apps.analytics.aggregated_metrics import calculate_weekly_metrics
        >>> stats = calculate_weekly_metrics(weeks=8)
    """
    calculator = AggregatedMetricsCalculator()
    return calculator.calculate_weekly_stats(weeks)


def calculate_monthly_metrics(months=3):
    """
    Calcula métricas mensuales.
    
    Usage:
        >>> from apps.analytics.aggregated_metrics import calculate_monthly_metrics
        >>> stats = calculate_monthly_metrics(months=6)
    """
    calculator = AggregatedMetricsCalculator()
    return calculator.calculate_monthly_stats(months)


def get_employee_performance(employee_id, days=30):
    """
    Obtiene métricas de rendimiento de un empleado.
    
    Usage:
        >>> from apps.analytics.aggregated_metrics import get_employee_performance
        >>> stats = get_employee_performance(employee_id=5, days=30)
    """
    calculator = AggregatedMetricsCalculator()
    return calculator.calculate_employee_performance(employee_id, days)


def get_team_performance(supervisor_id, days=30):
    """
    Obtiene métricas de rendimiento de un equipo.
    
    Usage:
        >>> from apps.analytics.aggregated_metrics import get_team_performance
        >>> stats = get_team_performance(supervisor_id=3, days=30)
    """
    calculator = AggregatedMetricsCalculator()
    return calculator.calculate_team_performance(supervisor_id, days)


def generate_all_metrics():
    """
    Genera todas las métricas agregadas (daily, weekly, monthly).
    Útil para ejecutar como tarea programada (cron job o Celery).
    
    Usage:
        >>> from apps.analytics.aggregated_metrics import generate_all_metrics
        >>> generate_all_metrics()
    """
    logger.info("Iniciando generación de todas las métricas agregadas")
    
    daily = calculate_daily_metrics()
    logger.info(f"✓ Métricas diarias: {len(daily)} días procesados")
    
    weekly = calculate_weekly_metrics()
    logger.info(f"✓ Métricas semanales: {len(weekly)} semanas procesadas")
    
    monthly = calculate_monthly_metrics()
    logger.info(f"✓ Métricas mensuales: {len(monthly)} meses procesados")
    
    logger.info("Generación de métricas completada")
    
    return {
        'daily': daily,
        'weekly': weekly,
        'monthly': monthly,
    }
