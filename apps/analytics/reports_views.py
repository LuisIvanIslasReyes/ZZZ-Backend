"""
ViewSet para generación de reportes.
Endpoints para reportes de productividad, fatiga y alertas.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Sum, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from apps.users.permissions import IsAdmin, IsSupervisor
from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import FatigueAlert
from apps.users.models import CustomUser
import logging

logger = logging.getLogger(__name__)


class ReportsViewSet(viewsets.ViewSet):
    """
    ViewSet para endpoints de reportes.
    
    Endpoints:
    - summary: Resumen general del reporte
    - employee_productivity: Productividad por empleado
    - productivity_trends: Tendencias de productividad
    - alerts_history: Historial de alertas
    - export: Exportar reportes en diferentes formatos
    """
    permission_classes = [IsAuthenticated]

    def _get_queryset_for_user(self, user):
        """Retorna queryset de métricas según el rol del usuario."""
        if user.role == 'admin':
            return ProcessedMetrics.objects.all()
        elif user.role == 'supervisor':
            return ProcessedMetrics.objects.filter(employee__supervisor=user)
        else:
            return ProcessedMetrics.objects.filter(employee=user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        GET /api/reports/summary/?days=30
        
        Resumen general de métricas para reportes.
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        # Obtener métricas
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            window_start__gte=start_date
        )
        
        # Calcular estadísticas
        stats = metrics_qs.aggregate(
            avg_fatigue=Avg('fatigue_index'),
            avg_heart_rate=Avg('hr_avg'),
            avg_spo2=Avg('spo2_avg'),
            total_readings=Count('id')
        )
        
        # Calcular productividad (100 - fatiga promedio)
        avg_productivity = 100 - (stats['avg_fatigue'] or 0)
        
        # Contar empleados únicos
        total_employees = metrics_qs.values('employee').distinct().count()
        
        # Calcular horas trabajadas (asumiendo 1 lectura por minuto)
        total_work_hours = (stats['total_readings'] or 0) / 60
        
        # Obtener alertas
        alert_qs = FatigueAlert.objects.filter(created_at__gte=start_date)
        if request.user.role == 'supervisor':
            alert_qs = alert_qs.filter(supervisor=request.user)
        elif request.user.role == 'employee':
            alert_qs = alert_qs.filter(employee=request.user)
        
        total_alerts = alert_qs.count()
        critical_alerts = alert_qs.filter(severity='critical').count()
        
        return Response({
            'total_employees': total_employees,
            'avg_fatigue_index': round(stats['avg_fatigue'] or 0, 2),
            'avg_productivity': round(avg_productivity, 2),
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'total_work_hours': round(total_work_hours, 1),
            'avg_heart_rate': round(stats['avg_heart_rate'] or 0, 1),
            'avg_spo2': round(stats['avg_spo2'] or 0, 1)
        })

    @action(detail=False, methods=['get'])
    def employee_productivity(self, request):
        """
        GET /api/reports/employee-productivity/?days=30
        
        Análisis de productividad por empleado.
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        # Obtener métricas por empleado
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            window_start__gte=start_date
        )
        
        # Agrupar por empleado
        employee_stats = metrics_qs.values(
            'employee__id',
            'employee__first_name',
            'employee__last_name',
            'employee__email'
        ).annotate(
            avg_fatigue=Avg('fatigue_index'),
            total_readings=Count('id'),
            attendance_days=Count('window_start__date', distinct=True)
        ).order_by('-total_readings')
        
        # Obtener alertas por empleado
        alert_counts = {}
        alert_qs = FatigueAlert.objects.filter(created_at__gte=start_date)
        if request.user.role == 'supervisor':
            alert_qs = alert_qs.filter(supervisor=request.user)
        
        for alert in alert_qs.values('employee_id').annotate(count=Count('id')):
            alert_counts[alert['employee_id']] = alert['count']
        
        # Formatear datos
        data = []
        for item in employee_stats:
            employee_id = item['employee__id']
            avg_fatigue = item['avg_fatigue'] or 0
            productivity_score = 100 - avg_fatigue
            total_hours = (item['total_readings'] or 0) / 60
            
            data.append({
                'employee_id': employee_id,
                'employee_name': f"{item['employee__first_name']} {item['employee__last_name']}",
                'employee_email': item['employee__email'],
                'total_hours': round(total_hours, 1),
                'avg_fatigue': round(avg_fatigue, 2),
                'productivity_score': round(productivity_score, 2),
                'alerts_count': alert_counts.get(employee_id, 0),
                'attendance_days': item['attendance_days']
            })
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def productivity_trends(self, request):
        """
        GET /api/reports/productivity-trends/?days=30
        
        Tendencias de productividad a lo largo del tiempo.
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            window_start__gte=start_date
        )
        
        # Agrupar por día
        daily_stats = metrics_qs.annotate(
            date=TruncDate('window_start')
        ).values('date').annotate(
            avg_fatigue=Avg('fatigue_index'),
            total_readings=Count('id'),
            employees_active=Count('employee', distinct=True)
        ).order_by('date')
        
        # Formatear datos
        data = []
        for item in daily_stats:
            avg_fatigue = item['avg_fatigue'] or 0
            avg_productivity = 100 - avg_fatigue
            total_hours = (item['total_readings'] or 0) / 60
            
            data.append({
                'date': item['date'],
                'avg_productivity': round(avg_productivity, 2),
                'avg_fatigue': round(avg_fatigue, 2),
                'total_hours': round(total_hours, 1),
                'employees_active': item['employees_active']
            })
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def alerts_history(self, request):
        """
        GET /api/reports/alerts-history/?days=30
        
        Historial de alertas agrupado por día.
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        alert_qs = FatigueAlert.objects.filter(created_at__gte=start_date)
        if request.user.role == 'supervisor':
            alert_qs = alert_qs.filter(supervisor=request.user)
        elif request.user.role == 'employee':
            alert_qs = alert_qs.filter(employee=request.user)
        
        # Agrupar por día
        daily_alerts = alert_qs.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_alerts=Count('id'),
            critical_alerts=Count('id', filter=Q(severity='critical')),
            medium_alerts=Count('id', filter=Q(severity='medium')),
            low_alerts=Count('id', filter=Q(severity='low')),
            resolved_alerts=Count('id', filter=Q(resolved=True))
        ).order_by('date')
        
        return Response(list(daily_alerts))

    @action(detail=False, methods=['get'], url_path='export/(?P<report_type>[^/.]+)')
    def export_report(self, request, report_type=None):
        """
        GET /api/reports/export/{report_type}/?format=pdf&days=30
        
        Exporta reporte en el formato especificado.
        Formatos: pdf, excel, csv
        """
        format_type = request.query_params.get('format', 'pdf')
        days = int(request.query_params.get('days', 30))
        
        # Por ahora, retornar datos en JSON
        # TODO: Implementar exportación real a PDF/Excel/CSV
        
        if report_type == 'productivity':
            data = self.employee_productivity(request).data
        elif report_type == 'fatigue':
            data = self.productivity_trends(request).data
        elif report_type == 'alerts':
            data = self.alerts_history(request).data
        else:
            data = self.summary(request).data
        
        return Response({
            'message': f'Exportación a {format_type} estará disponible próximamente',
            'data': data
        })
