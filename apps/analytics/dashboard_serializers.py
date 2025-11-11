"""
Serializers para dashboards y visualizaciones del sistema.
Proporciona datos agregados para diferentes roles y vistas.
"""

from rest_framework import serializers
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.utils import timezone
from datetime import timedelta
from apps.devices.models import Device
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation
from apps.users.models import CustomUser


class OverviewStatsSerializer(serializers.Serializer):
    """
    Estadísticas generales del sistema para dashboard principal.
    """
    # Contadores generales
    total_employees = serializers.IntegerField(read_only=True)
    active_employees = serializers.IntegerField(read_only=True)
    total_devices = serializers.IntegerField(read_only=True)
    active_devices = serializers.IntegerField(read_only=True)
    
    # Alertas
    total_alerts = serializers.IntegerField(read_only=True)
    pending_alerts = serializers.IntegerField(read_only=True)
    critical_alerts = serializers.IntegerField(read_only=True)
    alerts_today = serializers.IntegerField(read_only=True)
    
    # Recomendaciones
    total_recommendations = serializers.IntegerField(read_only=True)
    pending_recommendations = serializers.IntegerField(read_only=True)
    applied_recommendations = serializers.IntegerField(read_only=True)
    
    # Métricas promedio
    avg_fatigue_index = serializers.FloatField(read_only=True)
    avg_spo2 = serializers.FloatField(read_only=True)
    avg_heart_rate = serializers.FloatField(read_only=True)
    
    # Datos de sensores
    total_sensor_readings = serializers.IntegerField(read_only=True)
    readings_today = serializers.IntegerField(read_only=True)


class EmployeeFatigueStatsSerializer(serializers.Serializer):
    """
    Estadísticas de fatiga por empleado individual.
    """
    employee_id = serializers.IntegerField(read_only=True)
    employee_name = serializers.CharField(read_only=True)
    employee_email = serializers.EmailField(read_only=True)
    
    # Métricas actuales
    current_fatigue_index = serializers.FloatField(read_only=True)
    current_spo2 = serializers.FloatField(read_only=True)
    current_heart_rate = serializers.FloatField(read_only=True)
    last_reading = serializers.DateTimeField(read_only=True)
    
    # Promedios
    avg_fatigue_7d = serializers.FloatField(read_only=True)
    avg_spo2_7d = serializers.FloatField(read_only=True)
    avg_heart_rate_7d = serializers.FloatField(read_only=True)
    
    # Alertas
    total_alerts = serializers.IntegerField(read_only=True)
    pending_alerts = serializers.IntegerField(read_only=True)
    alerts_this_week = serializers.IntegerField(read_only=True)
    
    # Estado del dispositivo
    device_status = serializers.CharField(read_only=True)
    device_battery = serializers.FloatField(read_only=True)


class TeamPerformanceSerializer(serializers.Serializer):
    """
    Métricas de rendimiento de equipo para supervisores.
    """
    supervisor_id = serializers.IntegerField(read_only=True)
    supervisor_name = serializers.CharField(read_only=True)
    
    # Equipo
    total_employees = serializers.IntegerField(read_only=True)
    active_employees = serializers.IntegerField(read_only=True)
    
    # Alertas del equipo
    team_alerts = serializers.IntegerField(read_only=True)
    team_pending_alerts = serializers.IntegerField(read_only=True)
    team_critical_alerts = serializers.IntegerField(read_only=True)
    
    # Promedios del equipo
    team_avg_fatigue = serializers.FloatField(read_only=True)
    team_avg_spo2 = serializers.FloatField(read_only=True)
    team_avg_heart_rate = serializers.FloatField(read_only=True)
    
    # Empleado con mayor riesgo
    highest_risk_employee = serializers.DictField(read_only=True)
    
    # Tendencias
    fatigue_trend = serializers.CharField(read_only=True)  # 'increasing', 'decreasing', 'stable'
    alerts_trend = serializers.CharField(read_only=True)


class RealTimeMetricsSerializer(serializers.Serializer):
    """
    Métricas en tiempo real para monitoreo continuo.
    """
    timestamp = serializers.DateTimeField(read_only=True)
    
    # Métricas actuales del sistema
    active_employees = serializers.IntegerField(read_only=True)
    employees_in_danger = serializers.IntegerField(read_only=True)  # fatigue > 70
    employees_critical = serializers.IntegerField(read_only=True)  # fatigue > 85
    
    # Alertas recientes (últimos 5 minutos)
    recent_alerts = serializers.IntegerField(read_only=True)
    
    # Top empleados en riesgo
    high_risk_employees = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    # Dispositivos offline
    offline_devices = serializers.IntegerField(read_only=True)


class FatigueTrendSerializer(serializers.Serializer):
    """
    Tendencias de fatiga a lo largo del tiempo.
    """
    date = serializers.DateField(read_only=True)
    hour = serializers.IntegerField(read_only=True, required=False)
    
    # Métricas agregadas
    avg_fatigue_index = serializers.FloatField(read_only=True)
    max_fatigue_index = serializers.FloatField(read_only=True)
    min_fatigue_index = serializers.FloatField(read_only=True)
    
    avg_spo2 = serializers.FloatField(read_only=True)
    avg_heart_rate = serializers.FloatField(read_only=True)
    
    # Contadores
    total_readings = serializers.IntegerField(read_only=True)
    employees_monitored = serializers.IntegerField(read_only=True)
    alerts_generated = serializers.IntegerField(read_only=True)


class HourlyDistributionSerializer(serializers.Serializer):
    """
    Distribución de fatiga por hora del día.
    Útil para identificar patrones horarios.
    """
    hour = serializers.IntegerField(read_only=True)
    avg_fatigue = serializers.FloatField(read_only=True)
    avg_spo2 = serializers.FloatField(read_only=True)
    avg_heart_rate = serializers.FloatField(read_only=True)
    total_readings = serializers.IntegerField(read_only=True)
    alert_count = serializers.IntegerField(read_only=True)


class WeeklyDistributionSerializer(serializers.Serializer):
    """
    Distribución de fatiga por día de la semana.
    """
    day_of_week = serializers.IntegerField(read_only=True)  # 0=Monday, 6=Sunday
    day_name = serializers.CharField(read_only=True)
    avg_fatigue = serializers.FloatField(read_only=True)
    avg_spo2 = serializers.FloatField(read_only=True)
    avg_heart_rate = serializers.FloatField(read_only=True)
    total_readings = serializers.IntegerField(read_only=True)
    alert_count = serializers.IntegerField(read_only=True)


class FatigueLevelDistributionSerializer(serializers.Serializer):
    """
    Distribución de niveles de fatiga.
    """
    level = serializers.CharField(read_only=True)  # 'low', 'medium', 'high', 'critical'
    count = serializers.IntegerField(read_only=True)
    percentage = serializers.FloatField(read_only=True)


class DeviceHealthSerializer(serializers.Serializer):
    """
    Estado de salud de dispositivos IoT.
    """
    device_id = serializers.IntegerField(read_only=True)
    device_identifier = serializers.CharField(read_only=True)
    employee_name = serializers.CharField(read_only=True)
    
    status = serializers.CharField(read_only=True)
    battery_level = serializers.FloatField(read_only=True)
    last_connection = serializers.DateTimeField(read_only=True)
    
    # Estadísticas de conexión
    uptime_percentage = serializers.FloatField(read_only=True)
    total_readings = serializers.IntegerField(read_only=True)
    readings_today = serializers.IntegerField(read_only=True)
    
    # Calidad de datos
    data_quality_score = serializers.FloatField(read_only=True)  # 0-100


class AlertHistorySerializer(serializers.Serializer):
    """
    Historial de alertas para análisis de tendencias.
    """
    date = serializers.DateField(read_only=True)
    
    total_alerts = serializers.IntegerField(read_only=True)
    critical_alerts = serializers.IntegerField(read_only=True)
    high_alerts = serializers.IntegerField(read_only=True)
    medium_alerts = serializers.IntegerField(read_only=True)
    low_alerts = serializers.IntegerField(read_only=True)
    
    resolved_alerts = serializers.IntegerField(read_only=True)
    avg_resolution_time = serializers.FloatField(read_only=True)  # en minutos


class RecommendationEffectivenessSerializer(serializers.Serializer):
    """
    Efectividad de las recomendaciones aplicadas.
    """
    recommendation_type = serializers.CharField(read_only=True)
    
    total_created = serializers.IntegerField(read_only=True)
    total_applied = serializers.IntegerField(read_only=True)
    total_rejected = serializers.IntegerField(read_only=True)
    
    application_rate = serializers.FloatField(read_only=True)  # porcentaje
    
    # Impacto en fatiga (comparación antes/después)
    avg_fatigue_before = serializers.FloatField(read_only=True)
    avg_fatigue_after = serializers.FloatField(read_only=True)
    fatigue_improvement = serializers.FloatField(read_only=True)  # porcentaje


class EmployeeComparisonSerializer(serializers.Serializer):
    """
    Comparación entre empleados para benchmarking.
    """
    employee_id = serializers.IntegerField(read_only=True)
    employee_name = serializers.CharField(read_only=True)
    
    avg_fatigue = serializers.FloatField(read_only=True)
    avg_spo2 = serializers.FloatField(read_only=True)
    avg_heart_rate = serializers.FloatField(read_only=True)
    
    total_alerts = serializers.IntegerField(read_only=True)
    alert_rate = serializers.FloatField(read_only=True)  # alertas por día
    
    # Ranking
    fatigue_rank = serializers.IntegerField(read_only=True)
    overall_health_score = serializers.FloatField(read_only=True)  # 0-100


class CorrelationAnalysisSerializer(serializers.Serializer):
    """
    Análisis de correlaciones entre variables.
    """
    variable_x = serializers.CharField(read_only=True)
    variable_y = serializers.CharField(read_only=True)
    correlation_coefficient = serializers.FloatField(read_only=True)
    strength = serializers.CharField(read_only=True)  # 'weak', 'moderate', 'strong'
    direction = serializers.CharField(read_only=True)  # 'positive', 'negative'


class PredictiveInsightsSerializer(serializers.Serializer):
    """
    Insights predictivos basados en patrones históricos.
    """
    employee_id = serializers.IntegerField(read_only=True)
    employee_name = serializers.CharField(read_only=True)
    
    # Predicción de fatiga
    predicted_fatigue_next_hour = serializers.FloatField(read_only=True)
    predicted_fatigue_next_shift = serializers.FloatField(read_only=True)
    
    # Riesgo de alerta
    alert_probability = serializers.FloatField(read_only=True)  # 0-1
    risk_level = serializers.CharField(read_only=True)  # 'low', 'medium', 'high'
    
    # Recomendaciones automáticas
    suggested_actions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    
    # Confianza de la predicción
    confidence_score = serializers.FloatField(read_only=True)  # 0-1


class DashboardSummarySerializer(serializers.Serializer):
    """
    Resumen completo para dashboard principal.
    Combina múltiples métricas en una sola respuesta.
    """
    # Estadísticas generales
    overview = OverviewStatsSerializer(read_only=True)
    
    # Métricas en tiempo real
    real_time = RealTimeMetricsSerializer(read_only=True)
    
    # Top empleados en riesgo
    high_risk_employees = serializers.ListField(
        child=EmployeeFatigueStatsSerializer(),
        read_only=True
    )
    
    # Alertas recientes
    recent_alerts = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    # Tendencias (últimos 7 días)
    fatigue_trend = serializers.ListField(
        child=FatigueTrendSerializer(),
        read_only=True
    )
    
    # Dispositivos con problemas
    problematic_devices = serializers.ListField(
        child=DeviceHealthSerializer(),
        read_only=True
    )


class SupervisorDashboardSerializer(serializers.Serializer):
    """
    Dashboard específico para supervisores.
    Enfocado en métricas de equipo.
    """
    # Información del supervisor
    supervisor_info = serializers.DictField(read_only=True)
    
    # Rendimiento del equipo
    team_performance = TeamPerformanceSerializer(read_only=True)
    
    # Lista de empleados con métricas
    employees = serializers.ListField(
        child=EmployeeFatigueStatsSerializer(),
        read_only=True
    )
    
    # Alertas del equipo
    team_alerts = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    # Comparación entre empleados
    employee_comparison = serializers.ListField(
        child=EmployeeComparisonSerializer(),
        read_only=True
    )
    
    # Recomendaciones pendientes
    pending_recommendations = serializers.IntegerField(read_only=True)


class EmployeeDashboardSerializer(serializers.Serializer):
    """
    Dashboard específico para empleados.
    Muestra solo información personal.
    """
    # Información del empleado
    employee_info = serializers.DictField(read_only=True)
    
    # Métricas personales
    personal_stats = EmployeeFatigueStatsSerializer(read_only=True)
    
    # Historial de fatiga (últimos 7 días)
    fatigue_history = serializers.ListField(
        child=FatigueTrendSerializer(),
        read_only=True
    )
    
    # Alertas personales
    my_alerts = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    # Recomendaciones personales
    my_recommendations = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    # Comparación con promedio del equipo
    vs_team_average = serializers.DictField(read_only=True)
    
    # Progreso y logros
    progress = serializers.DictField(read_only=True)
