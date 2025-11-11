"""
Views para dashboards y visualizaciones del sistema.
Proporciona endpoints para métricas agregadas y análisis.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Max, Min, Q, Sum, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDate, TruncHour, ExtractHour, ExtractWeekDay
from django.utils import timezone
from datetime import timedelta, datetime
from apps.users.permissions import IsAdmin, IsSupervisor, IsEmployee
from apps.devices.models import Device
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation
from apps.users.models import CustomUser
from .dashboard_serializers import *
import logging

logger = logging.getLogger(__name__)


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para dashboards y métricas del sistema.
    
    Endpoints:
    - overview: Estadísticas generales del sistema
    - real_time: Métricas en tiempo real
    - employee_dashboard: Dashboard personal de empleado
    - supervisor_dashboard: Dashboard de supervisor con equipo
    - admin_dashboard: Dashboard completo de administrador
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        GET /api/dashboard/overview/
        Estadísticas generales del sistema.
        """
        # Contadores de usuarios
        total_employees = CustomUser.objects.filter(role='employee').count()
        active_employees = CustomUser.objects.filter(role='employee', is_active=True).count()
        
        # Contadores de dispositivos
        total_devices = Device.objects.count()
        active_devices = Device.objects.filter(is_active=True).count()
        
        # Alertas
        today = timezone.now().date()
        total_alerts = FatigueAlert.objects.count()
        pending_alerts = FatigueAlert.objects.filter(resolved=False).count()
        critical_alerts = FatigueAlert.objects.filter(severity='critical', resolved=False).count()
        alerts_today = FatigueAlert.objects.filter(created_at__date=today).count()
        
        # Recomendaciones
        total_recommendations = RoutineRecommendation.objects.count()
        pending_recommendations = RoutineRecommendation.objects.filter(applied=False, rejected=False).count()
        applied_recommendations = RoutineRecommendation.objects.filter(applied=True).count()
        
        # Métricas promedio (últimas 24 horas)
        last_24h = timezone.now() - timedelta(hours=24)
        recent_metrics = ProcessedMetrics.objects.filter(timestamp__gte=last_24h)
        
        metrics_agg = recent_metrics.aggregate(
            avg_fatigue=Avg('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_hr=Avg('heart_rate_avg')
        )
        
        # Datos de sensores
        total_sensor_readings = SensorData.objects.count()
        readings_today = SensorData.objects.filter(timestamp__date=today).count()
        
        data = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'total_devices': total_devices,
            'active_devices': active_devices,
            'total_alerts': total_alerts,
            'pending_alerts': pending_alerts,
            'critical_alerts': critical_alerts,
            'alerts_today': alerts_today,
            'total_recommendations': total_recommendations,
            'pending_recommendations': pending_recommendations,
            'applied_recommendations': applied_recommendations,
            'avg_fatigue_index': round(metrics_agg['avg_fatigue'] or 0, 2),
            'avg_spo2': round(metrics_agg['avg_spo2'] or 0, 2),
            'avg_heart_rate': round(metrics_agg['avg_hr'] or 0, 2),
            'total_sensor_readings': total_sensor_readings,
            'readings_today': readings_today,
        }
        
        serializer = OverviewStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def real_time(self, request):
        """
        GET /api/dashboard/real_time/
        Métricas en tiempo real (últimos 5 minutos).
        """
        now = timezone.now()
        last_5_min = now - timedelta(minutes=5)
        
        # Métricas más recientes por empleado
        recent_metrics = ProcessedMetrics.objects.filter(
            timestamp__gte=last_5_min
        ).select_related('employee', 'device')
        
        # Empleados activos (con lecturas recientes)
        active_employees = recent_metrics.values('employee').distinct().count()
        
        # Empleados en peligro
        employees_in_danger = recent_metrics.filter(fatigue_index__gte=70).values('employee').distinct().count()
        employees_critical = recent_metrics.filter(fatigue_index__gte=85).values('employee').distinct().count()
        
        # Alertas recientes
        recent_alerts = FatigueAlert.objects.filter(created_at__gte=last_5_min).count()
        
        # Top 5 empleados en riesgo
        high_risk = ProcessedMetrics.objects.filter(
            timestamp__gte=now - timedelta(hours=1)
        ).values(
            'employee__id',
            'employee__first_name',
            'employee__last_name',
            'employee__email'
        ).annotate(
            avg_fatigue=Avg('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            latest_reading=Max('timestamp')
        ).filter(
            avg_fatigue__gte=60
        ).order_by('-avg_fatigue')[:5]
        
        high_risk_list = [
            {
                'employee_id': item['employee__id'],
                'employee_name': f"{item['employee__first_name']} {item['employee__last_name']}",
                'fatigue_index': round(item['avg_fatigue'], 2),
                'spo2': round(item['avg_spo2'], 2),
                'last_reading': item['latest_reading']
            }
            for item in high_risk
        ]
        
        # Dispositivos offline (sin datos en últimos 30 minutos)
        last_30_min = now - timedelta(minutes=30)
        active_device_ids = SensorData.objects.filter(
            timestamp__gte=last_30_min
        ).values_list('device_id', flat=True).distinct()
        
        offline_devices = Device.objects.filter(is_active=True).exclude(
            id__in=active_device_ids
        ).count()
        
        data = {
            'timestamp': now,
            'active_employees': active_employees,
            'employees_in_danger': employees_in_danger,
            'employees_critical': employees_critical,
            'recent_alerts': recent_alerts,
            'high_risk_employees': high_risk_list,
            'offline_devices': offline_devices,
        }
        
        serializer = RealTimeMetricsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def employee_dashboard(self, request):
        """
        GET /api/dashboard/employee_dashboard/
        Dashboard personal del empleado autenticado.
        """
        employee = request.user
        
        if employee.role != 'employee':
            return Response(
                {'error': 'Este endpoint es solo para empleados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Información del empleado
        employee_info = {
            'id': employee.id,
            'name': f"{employee.first_name} {employee.last_name}",
            'email': employee.email,
            'phone': employee.phone_number,
        }
        
        # Obtener dispositivo del empleado
        try:
            device = Device.objects.get(employee=employee)
        except Device.DoesNotExist:
            return Response(
                {'error': 'No hay dispositivo asignado a este empleado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Métricas personales
        now = timezone.now()
        last_7_days = now - timedelta(days=7)
        
        # Métrica más reciente
        latest_metric = ProcessedMetrics.objects.filter(
            employee=employee
        ).order_by('-timestamp').first()
        
        # Promedios de 7 días
        metrics_7d = ProcessedMetrics.objects.filter(
            employee=employee,
            timestamp__gte=last_7_days
        ).aggregate(
            avg_fatigue=Avg('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_hr=Avg('heart_rate_avg')
        )
        
        # Alertas
        total_alerts = FatigueAlert.objects.filter(employee=employee).count()
        pending_alerts = FatigueAlert.objects.filter(employee=employee, resolved=False).count()
        alerts_this_week = FatigueAlert.objects.filter(
            employee=employee,
            created_at__gte=now - timedelta(days=7)
        ).count()
        
        personal_stats = {
            'employee_id': employee.id,
            'employee_name': f"{employee.first_name} {employee.last_name}",
            'employee_email': employee.email,
            'current_fatigue_index': round(latest_metric.fatigue_index, 2) if latest_metric else None,
            'current_spo2': round(latest_metric.spo2_avg, 2) if latest_metric else None,
            'current_heart_rate': round(latest_metric.heart_rate_avg, 2) if latest_metric else None,
            'last_reading': latest_metric.timestamp if latest_metric else None,
            'avg_fatigue_7d': round(metrics_7d['avg_fatigue'] or 0, 2),
            'avg_spo2_7d': round(metrics_7d['avg_spo2'] or 0, 2),
            'avg_heart_rate_7d': round(metrics_7d['avg_hr'] or 0, 2),
            'total_alerts': total_alerts,
            'pending_alerts': pending_alerts,
            'alerts_this_week': alerts_this_week,
            'device_status': device.status,
            'device_battery': device.battery_level,
        }
        
        # Historial de fatiga (últimos 7 días por día)
        fatigue_history = ProcessedMetrics.objects.filter(
            employee=employee,
            timestamp__gte=last_7_days
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            avg_fatigue_index=Avg('fatigue_index'),
            max_fatigue_index=Max('fatigue_index'),
            min_fatigue_index=Min('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_heart_rate=Avg('heart_rate_avg'),
            total_readings=Count('id')
        ).order_by('date')
        
        fatigue_history_data = [
            {
                'date': item['date'],
                'hour': None,
                'avg_fatigue_index': round(item['avg_fatigue_index'], 2),
                'max_fatigue_index': round(item['max_fatigue_index'], 2),
                'min_fatigue_index': round(item['min_fatigue_index'], 2),
                'avg_spo2': round(item['avg_spo2'], 2),
                'avg_heart_rate': round(item['avg_heart_rate'], 2),
                'total_readings': item['total_readings'],
                'employees_monitored': 1,
                'alerts_generated': 0  # Se puede calcular si es necesario
            }
            for item in fatigue_history
        ]
        
        # Alertas personales (últimas 10)
        my_alerts = FatigueAlert.objects.filter(
            employee=employee
        ).order_by('-created_at')[:10].values(
            'id', 'severity', 'message', 'resolved', 'created_at'
        )
        
        # Recomendaciones personales (últimas 10)
        my_recommendations = RoutineRecommendation.objects.filter(
            employee=employee
        ).order_by('-created_at')[:10].values(
            'id', 'recommendation_type', 'applied', 'created_at', 'data'
        )
        
        # Comparación con promedio del equipo
        if employee.supervisor:
            team_metrics = ProcessedMetrics.objects.filter(
                employee__supervisor=employee.supervisor,
                timestamp__gte=last_7_days
            ).aggregate(
                team_avg_fatigue=Avg('fatigue_index'),
                team_avg_spo2=Avg('spo2_avg'),
                team_avg_hr=Avg('heart_rate_avg')
            )
            
            vs_team_average = {
                'my_fatigue': round(metrics_7d['avg_fatigue'] or 0, 2),
                'team_fatigue': round(team_metrics['team_avg_fatigue'] or 0, 2),
                'fatigue_diff': round((metrics_7d['avg_fatigue'] or 0) - (team_metrics['team_avg_fatigue'] or 0), 2),
                'my_spo2': round(metrics_7d['avg_spo2'] or 0, 2),
                'team_spo2': round(team_metrics['team_avg_spo2'] or 0, 2),
            }
        else:
            vs_team_average = {}
        
        # Progreso (comparar semana actual vs anterior)
        last_week = now - timedelta(days=14)
        week_ago = now - timedelta(days=7)
        
        current_week_avg = ProcessedMetrics.objects.filter(
            employee=employee,
            timestamp__gte=week_ago
        ).aggregate(avg=Avg('fatigue_index'))['avg'] or 0
        
        previous_week_avg = ProcessedMetrics.objects.filter(
            employee=employee,
            timestamp__gte=last_week,
            timestamp__lt=week_ago
        ).aggregate(avg=Avg('fatigue_index'))['avg'] or 0
        
        improvement = previous_week_avg - current_week_avg if previous_week_avg else 0
        
        progress = {
            'current_week_fatigue': round(current_week_avg, 2),
            'previous_week_fatigue': round(previous_week_avg, 2),
            'improvement': round(improvement, 2),
            'trend': 'improving' if improvement > 0 else 'worsening' if improvement < 0 else 'stable'
        }
        
        data = {
            'employee_info': employee_info,
            'personal_stats': personal_stats,
            'fatigue_history': fatigue_history_data,
            'my_alerts': list(my_alerts),
            'my_recommendations': list(my_recommendations),
            'vs_team_average': vs_team_average,
            'progress': progress,
        }
        
        serializer = EmployeeDashboardSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSupervisor])
    def supervisor_dashboard(self, request):
        """
        GET /api/dashboard/supervisor_dashboard/
        Dashboard para supervisores con métricas de equipo.
        """
        supervisor = request.user
        
        # Información del supervisor
        supervisor_info = {
            'id': supervisor.id,
            'name': f"{supervisor.first_name} {supervisor.last_name}",
            'email': supervisor.email,
        }
        
        # Empleados del supervisor
        team_employees = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        total_employees = team_employees.count()
        active_employees = team_employees.filter(is_active=True).count()
        
        # Alertas del equipo
        now = timezone.now()
        team_alerts = FatigueAlert.objects.filter(supervisor=supervisor).count()
        team_pending_alerts = FatigueAlert.objects.filter(supervisor=supervisor, resolved=False).count()
        team_critical_alerts = FatigueAlert.objects.filter(
            supervisor=supervisor, 
            severity='critical', 
            resolved=False
        ).count()
        
        # Promedios del equipo (últimos 7 días)
        last_7_days = now - timedelta(days=7)
        team_metrics = ProcessedMetrics.objects.filter(
            employee__in=team_employees,
            timestamp__gte=last_7_days
        ).aggregate(
            avg_fatigue=Avg('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_hr=Avg('heart_rate_avg')
        )
        
        # Empleado con mayor riesgo
        high_risk_employee = ProcessedMetrics.objects.filter(
            employee__in=team_employees,
            timestamp__gte=now - timedelta(hours=24)
        ).values(
            'employee__id',
            'employee__first_name',
            'employee__last_name'
        ).annotate(
            avg_fatigue=Avg('fatigue_index')
        ).order_by('-avg_fatigue').first()
        
        highest_risk = {}
        if high_risk_employee:
            highest_risk = {
                'employee_id': high_risk_employee['employee__id'],
                'employee_name': f"{high_risk_employee['employee__first_name']} {high_risk_employee['employee__last_name']}",
                'fatigue_index': round(high_risk_employee['avg_fatigue'], 2)
            }
        
        # Tendencias (comparar esta semana vs anterior)
        last_14_days = now - timedelta(days=14)
        week_ago = now - timedelta(days=7)
        
        current_week_fatigue = ProcessedMetrics.objects.filter(
            employee__in=team_employees,
            timestamp__gte=week_ago
        ).aggregate(avg=Avg('fatigue_index'))['avg'] or 0
        
        previous_week_fatigue = ProcessedMetrics.objects.filter(
            employee__in=team_employees,
            timestamp__gte=last_14_days,
            timestamp__lt=week_ago
        ).aggregate(avg=Avg('fatigue_index'))['avg'] or 0
        
        fatigue_trend = 'stable'
        if current_week_fatigue > previous_week_fatigue + 5:
            fatigue_trend = 'increasing'
        elif current_week_fatigue < previous_week_fatigue - 5:
            fatigue_trend = 'decreasing'
        
        # Tendencia de alertas
        current_week_alerts = FatigueAlert.objects.filter(
            supervisor=supervisor,
            created_at__gte=week_ago
        ).count()
        
        previous_week_alerts = FatigueAlert.objects.filter(
            supervisor=supervisor,
            created_at__gte=last_14_days,
            created_at__lt=week_ago
        ).count()
        
        alerts_trend = 'stable'
        if current_week_alerts > previous_week_alerts:
            alerts_trend = 'increasing'
        elif current_week_alerts < previous_week_alerts:
            alerts_trend = 'decreasing'
        
        team_performance = {
            'supervisor_id': supervisor.id,
            'supervisor_name': f"{supervisor.first_name} {supervisor.last_name}",
            'total_employees': total_employees,
            'active_employees': active_employees,
            'team_alerts': team_alerts,
            'team_pending_alerts': team_pending_alerts,
            'team_critical_alerts': team_critical_alerts,
            'team_avg_fatigue': round(team_metrics['avg_fatigue'] or 0, 2),
            'team_avg_spo2': round(team_metrics['avg_spo2'] or 0, 2),
            'team_avg_heart_rate': round(team_metrics['avg_hr'] or 0, 2),
            'highest_risk_employee': highest_risk,
            'fatigue_trend': fatigue_trend,
            'alerts_trend': alerts_trend,
        }
        
        # Lista de empleados con métricas
        employees_data = []
        for emp in team_employees:
            latest_metric = ProcessedMetrics.objects.filter(employee=emp).order_by('-timestamp').first()
            
            metrics_7d = ProcessedMetrics.objects.filter(
                employee=emp,
                timestamp__gte=last_7_days
            ).aggregate(
                avg_fatigue=Avg('fatigue_index'),
                avg_spo2=Avg('spo2_avg'),
                avg_hr=Avg('heart_rate_avg')
            )
            
            emp_alerts = FatigueAlert.objects.filter(employee=emp).count()
            emp_pending = FatigueAlert.objects.filter(employee=emp, resolved=False).count()
            emp_week_alerts = FatigueAlert.objects.filter(
                employee=emp,
                created_at__gte=week_ago
            ).count()
            
            try:
                device = Device.objects.get(employee=emp)
                device_status = device.status
                device_battery = device.battery_level
            except Device.DoesNotExist:
                device_status = 'no_device'
                device_battery = 0
            
            employees_data.append({
                'employee_id': emp.id,
                'employee_name': f"{emp.first_name} {emp.last_name}",
                'employee_email': emp.email,
                'current_fatigue_index': round(latest_metric.fatigue_index, 2) if latest_metric else None,
                'current_spo2': round(latest_metric.spo2_avg, 2) if latest_metric else None,
                'current_heart_rate': round(latest_metric.heart_rate_avg, 2) if latest_metric else None,
                'last_reading': latest_metric.timestamp if latest_metric else None,
                'avg_fatigue_7d': round(metrics_7d['avg_fatigue'] or 0, 2),
                'avg_spo2_7d': round(metrics_7d['avg_spo2'] or 0, 2),
                'avg_heart_rate_7d': round(metrics_7d['avg_hr'] or 0, 2),
                'total_alerts': emp_alerts,
                'pending_alerts': emp_pending,
                'alerts_this_week': emp_week_alerts,
                'device_status': device_status,
                'device_battery': device_battery,
            })
        
        # Alertas del equipo (últimas 10)
        team_alerts_data = FatigueAlert.objects.filter(
            supervisor=supervisor
        ).order_by('-created_at')[:10].values(
            'id', 'employee__first_name', 'employee__last_name', 
            'severity', 'message', 'resolved', 'created_at'
        )
        
        team_alerts_list = [
            {
                'id': alert['id'],
                'employee_name': f"{alert['employee__first_name']} {alert['employee__last_name']}",
                'severity': alert['severity'],
                'message': alert['message'],
                'resolved': alert['resolved'],
                'created_at': alert['created_at']
            }
            for alert in team_alerts_data
        ]
        
        # Comparación entre empleados
        employee_comparison = []
        for i, emp_data in enumerate(employees_data, 1):
            employee_comparison.append({
                'employee_id': emp_data['employee_id'],
                'employee_name': emp_data['employee_name'],
                'avg_fatigue': emp_data['avg_fatigue_7d'],
                'avg_spo2': emp_data['avg_spo2_7d'],
                'avg_heart_rate': emp_data['avg_heart_rate_7d'],
                'total_alerts': emp_data['total_alerts'],
                'alert_rate': round(emp_data['alerts_this_week'] / 7, 2),
                'fatigue_rank': i,
                'overall_health_score': 100 - emp_data['avg_fatigue_7d'] if emp_data['avg_fatigue_7d'] else 100,
            })
        
        # Ordenar por fatiga para ranking correcto
        employee_comparison.sort(key=lambda x: x['avg_fatigue'], reverse=True)
        for i, emp in enumerate(employee_comparison, 1):
            emp['fatigue_rank'] = i
        
        # Recomendaciones pendientes
        pending_recommendations = RoutineRecommendation.objects.filter(
            employee__in=team_employees,
            applied=False,
            rejected=False
        ).count()
        
        data = {
            'supervisor_info': supervisor_info,
            'team_performance': team_performance,
            'employees': employees_data,
            'team_alerts': team_alerts_list,
            'employee_comparison': employee_comparison,
            'pending_recommendations': pending_recommendations,
        }
        
        serializer = SupervisorDashboardSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def admin_dashboard(self, request):
        """
        GET /api/dashboard/admin_dashboard/
        Dashboard completo para administradores.
        Combina overview + real_time + métricas globales.
        """
        # Obtener overview
        overview_response = self.overview(request)
        overview_data = overview_response.data
        
        # Obtener real-time
        realtime_response = self.real_time(request)
        realtime_data = realtime_response.data
        
        # Top empleados en riesgo (últimas 24 horas)
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        high_risk_employees_data = []
        high_risk_metrics = ProcessedMetrics.objects.filter(
            timestamp__gte=last_24h
        ).values(
            'employee__id',
            'employee__first_name',
            'employee__last_name',
            'employee__email'
        ).annotate(
            avg_fatigue=Avg('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_hr=Avg('heart_rate_avg'),
            latest=Max('timestamp')
        ).filter(
            avg_fatigue__gte=60
        ).order_by('-avg_fatigue')[:10]
        
        for item in high_risk_metrics:
            # Obtener alertas y dispositivo
            employee_id = item['employee__id']
            alerts = FatigueAlert.objects.filter(employee_id=employee_id).count()
            pending = FatigueAlert.objects.filter(employee_id=employee_id, resolved=False).count()
            week_alerts = FatigueAlert.objects.filter(
                employee_id=employee_id,
                created_at__gte=now - timedelta(days=7)
            ).count()
            
            try:
                device = Device.objects.get(employee_id=employee_id)
                device_status = device.status
                device_battery = device.battery_level
            except Device.DoesNotExist:
                device_status = 'no_device'
                device_battery = 0
            
            high_risk_employees_data.append({
                'employee_id': employee_id,
                'employee_name': f"{item['employee__first_name']} {item['employee__last_name']}",
                'employee_email': item['employee__email'],
                'current_fatigue_index': round(item['avg_fatigue'], 2),
                'current_spo2': round(item['avg_spo2'], 2),
                'current_heart_rate': round(item['avg_hr'], 2),
                'last_reading': item['latest'],
                'avg_fatigue_7d': round(item['avg_fatigue'], 2),
                'avg_spo2_7d': round(item['avg_spo2'], 2),
                'avg_heart_rate_7d': round(item['avg_hr'], 2),
                'total_alerts': alerts,
                'pending_alerts': pending,
                'alerts_this_week': week_alerts,
                'device_status': device_status,
                'device_battery': device_battery,
            })
        
        # Alertas recientes
        recent_alerts = FatigueAlert.objects.order_by('-created_at')[:10].values(
            'id', 'employee__first_name', 'employee__last_name',
            'severity', 'message', 'resolved', 'created_at'
        )
        
        recent_alerts_list = [
            {
                'id': alert['id'],
                'employee_name': f"{alert['employee__first_name']} {alert['employee__last_name']}",
                'severity': alert['severity'],
                'message': alert['message'],
                'resolved': alert['resolved'],
                'created_at': alert['created_at']
            }
            for alert in recent_alerts
        ]
        
        # Tendencia de fatiga (últimos 7 días)
        last_7_days = now - timedelta(days=7)
        fatigue_trend_data = ProcessedMetrics.objects.filter(
            timestamp__gte=last_7_days
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            avg_fatigue_index=Avg('fatigue_index'),
            max_fatigue_index=Max('fatigue_index'),
            min_fatigue_index=Min('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_heart_rate=Avg('heart_rate_avg'),
            total_readings=Count('id'),
            employees_monitored=Count('employee', distinct=True)
        ).order_by('date')
        
        # Contar alertas por día
        alerts_by_day = FatigueAlert.objects.filter(
            created_at__gte=last_7_days
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        )
        
        alerts_dict = {item['date']: item['count'] for item in alerts_by_day}
        
        fatigue_trend_list = []
        for item in fatigue_trend_data:
            fatigue_trend_list.append({
                'date': item['date'],
                'hour': None,
                'avg_fatigue_index': round(item['avg_fatigue_index'], 2),
                'max_fatigue_index': round(item['max_fatigue_index'], 2),
                'min_fatigue_index': round(item['min_fatigue_index'], 2),
                'avg_spo2': round(item['avg_spo2'], 2),
                'avg_heart_rate': round(item['avg_heart_rate'], 2),
                'total_readings': item['total_readings'],
                'employees_monitored': item['employees_monitored'],
                'alerts_generated': alerts_dict.get(item['date'], 0)
            })
        
        # Dispositivos problemáticos
        last_30_min = now - timedelta(minutes=30)
        active_device_ids = SensorData.objects.filter(
            timestamp__gte=last_30_min
        ).values_list('device_id', flat=True).distinct()
        
        problematic_devices_qs = Device.objects.filter(
            Q(is_active=True) & ~Q(id__in=active_device_ids)
        ).select_related('employee')
        
        problematic_devices_data = []
        for device in problematic_devices_qs[:10]:
            last_reading = SensorData.objects.filter(device=device).order_by('-timestamp').first()
            total_readings = SensorData.objects.filter(device=device).count()
            readings_today = SensorData.objects.filter(device=device, timestamp__date=now.date()).count()
            
            problematic_devices_data.append({
                'device_id': device.id,
                'device_identifier': device.device_identifier,
                'employee_name': f"{device.employee.first_name} {device.employee.last_name}" if device.employee else 'N/A',
                'status': device.status,
                'battery_level': device.battery_level,
                'last_connection': last_reading.timestamp if last_reading else None,
                'uptime_percentage': 0,  # Se puede calcular con más lógica
                'total_readings': total_readings,
                'readings_today': readings_today,
                'data_quality_score': 50,  # Placeholder
            })
        
        # Construir summary
        summary_data = {
            'overview': overview_data,
            'real_time': realtime_data,
            'high_risk_employees': high_risk_employees_data,
            'recent_alerts': recent_alerts_list,
            'fatigue_trend': fatigue_trend_list,
            'problematic_devices': problematic_devices_data,
        }
        
        serializer = DashboardSummarySerializer(summary_data)
        return Response(serializer.data)
