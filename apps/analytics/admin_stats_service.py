# apps/analytics/admin_stats_service.py
"""
Servicio para calcular estadísticas administrativas del sistema.
Proporciona funciones centralizadas para generar reportes y métricas globales.
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q, Max, Min, Sum
from django.utils import timezone
from datetime import timedelta

from apps.devices.models import Device
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation

User = get_user_model()


class AdminStatsService:
    """
    Servicio centralizado para calcular estadísticas administrativas.
    """
    
    def __init__(self, admin_user):
        """
        Inicializa el servicio con el usuario admin.
        
        Args:
            admin_user: Usuario administrador
        """
        self.admin = admin_user
        self.supervisors = User.objects.filter(
            role='supervisor',
            admin=admin_user
        )
        self.supervisor_ids = list(self.supervisors.values_list('id', flat=True))
        self.employees = User.objects.filter(
            role='employee',
            supervisor_id__in=self.supervisor_ids
        )
        self.employee_ids = list(self.employees.values_list('id', flat=True))
    
    def get_user_statistics(self):
        """
        Estadísticas de usuarios del sistema.
        
        Returns:
            dict: Estadísticas de supervisores y empleados
        """
        return {
            'supervisors': {
                'total': self.supervisors.count(),
                'active': self.supervisors.filter(is_active=True).count(),
                'inactive': self.supervisors.filter(is_active=False).count(),
                'with_employees': self.supervisors.annotate(
                    emp_count=Count('employees')
                ).filter(emp_count__gt=0).count()
            },
            'employees': {
                'total': self.employees.count(),
                'active': self.employees.filter(is_active=True).count(),
                'inactive': self.employees.filter(is_active=False).count(),
                'with_devices': self.employees.filter(
                    device__isnull=False,
                    device__is_active=True
                ).count(),
                'without_devices': self.employees.filter(
                    Q(device__isnull=True) | Q(device__is_active=False)
                ).count()
            }
        }
    
    def get_device_statistics(self):
        """
        Estadísticas de dispositivos del sistema.
        
        Returns:
            dict: Estadísticas de dispositivos
        """
        devices = Device.objects.filter(supervisor_id__in=self.supervisor_ids)
        now = timezone.now()
        
        # Dispositivos conectados en las últimas 24 horas
        connected_24h = devices.filter(
            last_connection__gte=now - timedelta(hours=24)
        ).count()
        
        # Dispositivos conectados en la última hora
        connected_1h = devices.filter(
            last_connection__gte=now - timedelta(hours=1)
        ).count()
        
        return {
            'total': devices.count(),
            'active': devices.filter(is_active=True).count(),
            'inactive': devices.filter(is_active=False).count(),
            'connected_24h': connected_24h,
            'connected_1h': connected_1h,
            'never_connected': devices.filter(last_connection__isnull=True).count()
        }
    
    def get_alert_statistics(self, period_days=7):
        """
        Estadísticas de alertas del sistema.
        
        Args:
            period_days: Días para el período (default: 7)
        
        Returns:
            dict: Estadísticas de alertas
        """
        alerts = FatigueAlert.objects.filter(
            supervisor_id__in=self.supervisor_ids
        )
        
        # Alertas del período
        start_date = timezone.now() - timedelta(days=period_days)
        alerts_period = alerts.filter(timestamp__gte=start_date)
        
        # Distribución por severidad
        severity_distribution = alerts_period.values('severity').annotate(
            count=Count('id')
        )
        severity_dict = {item['severity']: item['count'] for item in severity_distribution}
        
        # Tiempo promedio de resolución
        resolved_alerts = alerts.filter(
            is_resolved=True,
            resolved_at__isnull=False
        )
        
        avg_resolution_time = None
        if resolved_alerts.exists():
            total_seconds = 0
            count = 0
            for alert in resolved_alerts:
                if alert.resolved_at and alert.timestamp:
                    delta = alert.resolved_at - alert.timestamp
                    total_seconds += delta.total_seconds()
                    count += 1
            
            if count > 0:
                avg_resolution_time = total_seconds / count / 3600  # en horas
        
        return {
            'total_all_time': alerts.count(),
            'total_period': alerts_period.count(),
            'active': alerts.filter(is_resolved=False).count(),
            'resolved': alerts.filter(is_resolved=True).count(),
            'by_severity': {
                'low': severity_dict.get('low', 0),
                'medium': severity_dict.get('medium', 0),
                'high': severity_dict.get('high', 0),
                'critical': severity_dict.get('critical', 0)
            },
            'avg_resolution_hours': round(avg_resolution_time, 2) if avg_resolution_time else None,
            'unresolved_critical': alerts.filter(
                is_resolved=False,
                severity='critical'
            ).count()
        }
    
    def get_recommendation_statistics(self, period_days=7):
        """
        Estadísticas de recomendaciones del sistema.
        
        Args:
            period_days: Días para el período (default: 7)
        
        Returns:
            dict: Estadísticas de recomendaciones
        """
        recommendations = RoutineRecommendation.objects.filter(
            supervisor_id__in=self.supervisor_ids
        )
        
        # Recomendaciones del período
        start_date = timezone.now() - timedelta(days=period_days)
        recommendations_period = recommendations.filter(created_at__gte=start_date)
        
        # Distribución por tipo
        type_distribution = recommendations_period.values('recommendation_type').annotate(
            count=Count('id')
        )
        type_dict = {item['recommendation_type']: item['count'] for item in type_distribution}
        
        # Tasa de aplicación
        total = recommendations.count()
        applied = recommendations.filter(is_applied=True).count()
        application_rate = (applied / total * 100) if total > 0 else 0
        
        return {
            'total_all_time': total,
            'total_period': recommendations_period.count(),
            'applied': applied,
            'pending': recommendations.filter(is_applied=False).count(),
            'application_rate': round(application_rate, 2),
            'by_type': {
                'break': type_dict.get('break', 0),
                'task_redistribution': type_dict.get('task_redistribution', 0),
                'shift_rotation': type_dict.get('shift_rotation', 0)
            },
            'high_priority_pending': recommendations.filter(
                is_applied=False,
                priority__gte=4
            ).count()
        }
    
    def get_metrics_statistics(self, period_days=7):
        """
        Estadísticas de métricas procesadas del sistema.
        
        Args:
            period_days: Días para el período (default: 7)
        
        Returns:
            dict: Estadísticas de métricas
        """
        start_date = timezone.now() - timedelta(days=period_days)
        
        metrics = ProcessedMetrics.objects.filter(
            employee_id__in=self.employee_ids,
            window_start__gte=start_date
        )
        
        # Promedios generales
        aggregates = metrics.aggregate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            min_fatigue=Min('fatigue_index'),
            avg_hr=Avg('hr_avg'),
            avg_spo2=Avg('spo2_avg'),
            avg_activity=Avg('activity_level')
        )
        
        # Distribución de niveles de fatiga
        fatigue_distribution = {
            'low': metrics.filter(fatigue_index__lt=30).count(),
            'medium': metrics.filter(fatigue_index__gte=30, fatigue_index__lt=60).count(),
            'high': metrics.filter(fatigue_index__gte=60, fatigue_index__lt=80).count(),
            'critical': metrics.filter(fatigue_index__gte=80).count()
        }
        
        # Empleados con alta fatiga frecuente
        from django.db.models import Avg as DjangoAvg
        high_fatigue_employees = metrics.values('employee_id').annotate(
            avg_fatigue=DjangoAvg('fatigue_index')
        ).filter(avg_fatigue__gte=70).count()
        
        return {
            'total_readings': metrics.count(),
            'averages': {
                'fatigue_index': round(aggregates['avg_fatigue'] or 0, 2),
                'heart_rate': round(aggregates['avg_hr'] or 0, 2),
                'spo2': round(aggregates['avg_spo2'] or 0, 2),
                'activity_level': round(aggregates['avg_activity'] or 0, 2)
            },
            'fatigue_range': {
                'max': round(aggregates['max_fatigue'] or 0, 2),
                'min': round(aggregates['min_fatigue'] or 0, 2)
            },
            'fatigue_distribution': fatigue_distribution,
            'high_fatigue_employees': high_fatigue_employees,
            'readings_per_employee': round(
                metrics.count() / len(self.employee_ids), 2
            ) if self.employee_ids else 0
        }
    
    def get_sensor_data_statistics(self, period_days=1):
        """
        Estadísticas de datos crudos de sensores.
        
        Args:
            period_days: Días para el período (default: 1)
        
        Returns:
            dict: Estadísticas de datos de sensores
        """
        start_date = timezone.now() - timedelta(days=period_days)
        
        # Obtener dispositivos de empleados
        devices = Device.objects.filter(
            employee_id__in=self.employee_ids,
            is_active=True
        )
        device_ids = list(devices.values_list('id', flat=True))
        
        sensor_data = SensorData.objects.filter(
            device_id__in=device_ids,
            timestamp__gte=start_date
        )
        
        # Datos por dispositivo
        data_per_device = sensor_data.values('device_id').annotate(
            count=Count('id')
        )
        
        total_readings = sensor_data.count()
        expected_readings = len(device_ids) * period_days * 24 * 12  # 12 por hora (cada 5 seg)
        data_completeness = (total_readings / expected_readings * 100) if expected_readings > 0 else 0
        
        return {
            'total_readings': total_readings,
            'active_devices_reporting': len(data_per_device),
            'expected_readings': expected_readings,
            'data_completeness': round(data_completeness, 2),
            'avg_readings_per_device': round(
                total_readings / len(device_ids), 2
            ) if device_ids else 0
        }
    
    def get_supervisor_performance(self):
        """
        Rendimiento de cada supervisor.
        
        Returns:
            list: Lista de supervisores con sus métricas
        """
        supervisor_stats = []
        
        for supervisor in self.supervisors:
            employees = supervisor.employees.all()
            employee_ids = list(employees.values_list('id', flat=True))
            
            # Alertas
            total_alerts = FatigueAlert.objects.filter(supervisor=supervisor).count()
            active_alerts = FatigueAlert.objects.filter(
                supervisor=supervisor,
                is_resolved=False
            ).count()
            
            # Recomendaciones
            total_recommendations = RoutineRecommendation.objects.filter(
                supervisor=supervisor
            ).count()
            applied_recommendations = RoutineRecommendation.objects.filter(
                supervisor=supervisor,
                is_applied=True
            ).count()
            
            # Fatiga promedio de empleados
            avg_fatigue = ProcessedMetrics.objects.filter(
                employee_id__in=employee_ids,
                window_start__gte=timezone.now() - timedelta(days=7)
            ).aggregate(avg=Avg('fatigue_index'))['avg']
            
            supervisor_stats.append({
                'id': supervisor.id,
                'name': supervisor.get_full_name(),
                'email': supervisor.email,
                'employees_count': employees.count(),
                'active_employees': employees.filter(is_active=True).count(),
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'alert_resolution_rate': round(
                    (total_alerts - active_alerts) / total_alerts * 100, 2
                ) if total_alerts > 0 else 0,
                'total_recommendations': total_recommendations,
                'applied_recommendations': applied_recommendations,
                'recommendation_application_rate': round(
                    applied_recommendations / total_recommendations * 100, 2
                ) if total_recommendations > 0 else 0,
                'avg_team_fatigue': round(avg_fatigue or 0, 2)
            })
        
        # Ordenar por número de empleados (descendente)
        supervisor_stats.sort(key=lambda x: x['employees_count'], reverse=True)
        
        return supervisor_stats
    
    def get_complete_report(self, period_days=7):
        """
        Reporte completo con todas las estadísticas.
        
        Args:
            period_days: Días para el período (default: 7)
        
        Returns:
            dict: Reporte completo del sistema
        """
        return {
            'generated_at': timezone.now(),
            'period_days': period_days,
            'admin': {
                'id': self.admin.id,
                'name': self.admin.get_full_name(),
                'email': self.admin.email
            },
            'users': self.get_user_statistics(),
            'devices': self.get_device_statistics(),
            'alerts': self.get_alert_statistics(period_days),
            'recommendations': self.get_recommendation_statistics(period_days),
            'metrics': self.get_metrics_statistics(period_days),
            'sensor_data': self.get_sensor_data_statistics(period_days=1),
            'supervisor_performance': self.get_supervisor_performance()
        }


# Funciones de conveniencia para uso rápido

def get_admin_dashboard_stats(admin_user, period_days=7):
    """
    Función de conveniencia para obtener estadísticas del dashboard.
    
    Args:
        admin_user: Usuario administrador
        period_days: Días para el período
    
    Returns:
        dict: Estadísticas del dashboard
    """
    service = AdminStatsService(admin_user)
    return service.get_complete_report(period_days)


def get_supervisor_rankings(admin_user):
    """
    Función de conveniencia para obtener ranking de supervisores.
    
    Args:
        admin_user: Usuario administrador
    
    Returns:
        list: Lista de supervisores ordenados por rendimiento
    """
    service = AdminStatsService(admin_user)
    return service.get_supervisor_performance()


def calculate_system_health(admin_user):
    """
    Calcula un índice de salud del sistema (0-100).
    
    Args:
        admin_user: Usuario administrador
    
    Returns:
        dict: Índice de salud y componentes
    """
    service = AdminStatsService(admin_user)
    
    # Obtener estadísticas
    devices = service.get_device_statistics()
    alerts = service.get_alert_statistics()
    metrics = service.get_metrics_statistics()
    
    # Calcular componentes del índice de salud
    
    # 1. Conectividad de dispositivos (30%)
    device_health = (devices['connected_24h'] / devices['total'] * 100) if devices['total'] > 0 else 0
    device_score = device_health * 0.3
    
    # 2. Gestión de alertas (30%)
    alert_resolution_rate = (
        alerts['resolved'] / alerts['total_all_time'] * 100
    ) if alerts['total_all_time'] > 0 else 100
    alert_score = alert_resolution_rate * 0.3
    
    # 3. Nivel de fatiga promedio (40%)
    # Invertir: menos fatiga = mejor salud
    avg_fatigue = metrics['averages']['fatigue_index']
    fatigue_health = max(0, 100 - avg_fatigue)
    fatigue_score = fatigue_health * 0.4
    
    # Índice total
    health_index = device_score + alert_score + fatigue_score
    
    return {
        'health_index': round(health_index, 2),
        'components': {
            'device_connectivity': {
                'score': round(device_health, 2),
                'weight': 30,
                'status': 'good' if device_health >= 80 else 'warning' if device_health >= 60 else 'critical'
            },
            'alert_management': {
                'score': round(alert_resolution_rate, 2),
                'weight': 30,
                'status': 'good' if alert_resolution_rate >= 80 else 'warning' if alert_resolution_rate >= 60 else 'critical'
            },
            'employee_wellbeing': {
                'score': round(fatigue_health, 2),
                'weight': 40,
                'status': 'good' if avg_fatigue < 50 else 'warning' if avg_fatigue < 70 else 'critical'
            }
        },
        'overall_status': 'healthy' if health_index >= 80 else 'warning' if health_index >= 60 else 'critical'
    }
