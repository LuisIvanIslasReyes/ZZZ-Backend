"""
ViewSet para generación de reportes y exportación de datos.
Permite exportar datos en formato CSV para análisis offline.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db.models import Avg, Count, Max, Min, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
import csv
from apps.users.permissions import IsAdmin, IsSupervisor
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation
from apps.devices.models import Device
from apps.users.models import CustomUser
import logging

logger = logging.getLogger(__name__)


class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet para generación de reportes del sistema.
    
    Endpoints:
    - employee_report: Reporte individual de empleado
    - team_report: Reporte de equipo para supervisor
    - alerts_report: Reporte de alertas
    - metrics_report: Reporte de métricas agregadas
    - recommendations_report: Reporte de recomendaciones
    - devices_report: Reporte de estado de dispositivos
    - executive_summary: Resumen ejecutivo
    """
    permission_classes = [IsAuthenticated]

    def _filter_by_role(self, queryset, user, employee_field='employee'):
        """
        Filtra queryset según el rol del usuario.
        """
        if user.role == 'admin':
            return queryset
        elif user.role == 'supervisor':
            filter_kwargs = {f'{employee_field}__supervisor': user}
            return queryset.filter(**filter_kwargs)
        else:  # employee
            filter_kwargs = {employee_field: user}
            return queryset.filter(**filter_kwargs)

    def _get_date_range(self, request):
        """
        Obtiene rango de fechas de los query params.
        """
        days = int(request.query_params.get('days', 30))
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        now = timezone.now()
        
        if start_date_str and end_date_str:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            start_date = timezone.make_aware(start_date)
            end_date = timezone.make_aware(end_date)
        else:
            start_date = now - timedelta(days=days)
            end_date = now
        
        return start_date, end_date

    @action(detail=False, methods=['get'])
    def employee_report(self, request):
        """
        GET /api/reports/employee_report/?employee_id=5&days=30&format=csv
        
        Reporte completo de un empleado específico.
        Incluye: métricas, alertas, recomendaciones.
        """
        employee_id = request.query_params.get('employee_id')
        export_format = request.query_params.get('format', 'json')
        
        if not employee_id:
            return Response({'error': 'employee_id es requerido'}, status=400)
        
        try:
            employee = CustomUser.objects.get(id=employee_id, role='employee')
        except CustomUser.DoesNotExist:
            return Response({'error': 'Empleado no encontrado'}, status=404)
        
        # Verificar permisos
        if request.user.role == 'employee' and request.user.id != int(employee_id):
            return Response({'error': 'Sin permisos'}, status=403)
        elif request.user.role == 'supervisor' and employee.supervisor != request.user:
            return Response({'error': 'Sin permisos'}, status=403)
        
        start_date, end_date = self._get_date_range(request)
        
        # Obtener métricas
        metrics = ProcessedMetrics.objects.filter(
            employee=employee,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('-timestamp')
        
        # Estadísticas agregadas
        metrics_stats = metrics.aggregate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            min_fatigue=Min('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_hr=Avg('heart_rate_avg'),
            total_readings=Count('id')
        )
        
        # Alertas
        alerts = FatigueAlert.objects.filter(
            employee=employee,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')
        
        alerts_stats = {
            'total': alerts.count(),
            'critical': alerts.filter(severity='critical').count(),
            'high': alerts.filter(severity='high').count(),
            'resolved': alerts.filter(is_resolved=True).count(),
            'pending': alerts.filter(is_resolved=False).count(),
        }
        
        # Recomendaciones
        recommendations = RoutineRecommendation.objects.filter(
            employee=employee,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')
        
        rec_stats = {
            'total': recommendations.count(),
            'applied': recommendations.filter(applied=True).count(),
            'rejected': recommendations.filter(rejected=True).count(),
            'pending': recommendations.filter(applied=False, rejected=False).count(),
        }
        
        if export_format == 'csv':
            # Exportar a CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reporte_empleado_{employee_id}_{start_date.date()}_to_{end_date.date()}.csv"'
            
            writer = csv.writer(response)
            
            # Header
            writer.writerow(['REPORTE DE EMPLEADO'])
            writer.writerow(['Empleado', f"{employee.first_name} {employee.last_name}"])
            writer.writerow(['Email', employee.email])
            writer.writerow(['Período', f"{start_date.date()} a {end_date.date()}"])
            writer.writerow([])
            
            # Estadísticas
            writer.writerow(['ESTADÍSTICAS GENERALES'])
            writer.writerow(['Métrica', 'Valor'])
            writer.writerow(['Fatiga Promedio', round(metrics_stats['avg_fatigue'] or 0, 2)])
            writer.writerow(['Fatiga Máxima', round(metrics_stats['max_fatigue'] or 0, 2)])
            writer.writerow(['Fatiga Mínima', round(metrics_stats['min_fatigue'] or 0, 2)])
            writer.writerow(['SpO2 Promedio', round(metrics_stats['avg_spo2'] or 0, 2)])
            writer.writerow(['FC Promedio', round(metrics_stats['avg_hr'] or 0, 2)])
            writer.writerow(['Total Lecturas', metrics_stats['total_readings']])
            writer.writerow([])
            
            # Alertas
            writer.writerow(['RESUMEN DE ALERTAS'])
            writer.writerow(['Tipo', 'Cantidad'])
            writer.writerow(['Total', alerts_stats['total']])
            writer.writerow(['Críticas', alerts_stats['critical']])
            writer.writerow(['Altas', alerts_stats['high']])
            writer.writerow(['Resueltas', alerts_stats['resolved']])
            writer.writerow(['Pendientes', alerts_stats['pending']])
            writer.writerow([])
            
            # Recomendaciones
            writer.writerow(['RESUMEN DE RECOMENDACIONES'])
            writer.writerow(['Estado', 'Cantidad'])
            writer.writerow(['Total', rec_stats['total']])
            writer.writerow(['Aplicadas', rec_stats['applied']])
            writer.writerow(['Rechazadas', rec_stats['rejected']])
            writer.writerow(['Pendientes', rec_stats['pending']])
            writer.writerow([])
            
            # Detalle de métricas diarias
            writer.writerow(['MÉTRICAS DIARIAS'])
            writer.writerow(['Fecha', 'Fatiga Promedio', 'SpO2 Promedio', 'FC Promedio', 'Lecturas'])
            
            daily_metrics = metrics.annotate(
                date=TruncDate('timestamp')
            ).values('date').annotate(
                avg_fatigue=Avg('fatigue_index'),
                avg_spo2=Avg('spo2_avg'),
                avg_hr=Avg('heart_rate_avg'),
                count=Count('id')
            ).order_by('date')
            
            for item in daily_metrics:
                writer.writerow([
                    item['date'],
                    round(item['avg_fatigue'], 2),
                    round(item['avg_spo2'], 2),
                    round(item['avg_hr'], 2),
                    item['count']
                ])
            
            return response
        
        # Respuesta JSON
        data = {
            'employee': {
                'id': employee.id,
                'name': f"{employee.first_name} {employee.last_name}",
                'email': employee.email,
            },
            'period': {
                'start': start_date,
                'end': end_date,
            },
            'metrics_summary': metrics_stats,
            'alerts_summary': alerts_stats,
            'recommendations_summary': rec_stats,
            'recent_alerts': list(alerts[:10].values(
                'id', 'severity', 'message', 'created_at', 'resolved'
            )),
            'recent_recommendations': list(recommendations[:10].values(
                'id', 'recommendation_type', 'created_at', 'applied', 'rejected'
            )),
        }
        
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSupervisor])
    def team_report(self, request):
        """
        GET /api/reports/team_report/?days=30&format=csv
        
        Reporte de equipo para supervisores.
        """
        export_format = request.query_params.get('format', 'json')
        start_date, end_date = self._get_date_range(request)
        
        supervisor = request.user
        team_employees = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reporte_equipo_{supervisor.id}_{start_date.date()}_to_{end_date.date()}.csv"'
            
            writer = csv.writer(response)
            
            # Header
            writer.writerow(['REPORTE DE EQUIPO'])
            writer.writerow(['Supervisor', f"{supervisor.first_name} {supervisor.last_name}"])
            writer.writerow(['Período', f"{start_date.date()} a {end_date.date()}"])
            writer.writerow([])
            
            # Resumen por empleado
            writer.writerow(['RESUMEN POR EMPLEADO'])
            writer.writerow([
                'Empleado', 'Email', 'Fatiga Promedio', 'SpO2 Promedio', 
                'FC Promedio', 'Total Alertas', 'Alertas Pendientes'
            ])
            
            for emp in team_employees:
                metrics = ProcessedMetrics.objects.filter(
                    employee=emp,
                    timestamp__gte=start_date,
                    timestamp__lte=end_date
                ).aggregate(
                    avg_fatigue=Avg('fatigue_index'),
                    avg_spo2=Avg('spo2_avg'),
                    avg_hr=Avg('heart_rate_avg')
                )
                
                alerts_count = FatigueAlert.objects.filter(
                    employee=emp,
                    created_at__gte=start_date,
                    created_at__lte=end_date
                ).count()
                
                pending_alerts = FatigueAlert.objects.filter(
                    employee=emp,
                    is_resolved=False
                ).count()
                
                writer.writerow([
                    f"{emp.first_name} {emp.last_name}",
                    emp.email,
                    round(metrics['avg_fatigue'] or 0, 2),
                    round(metrics['avg_spo2'] or 0, 2),
                    round(metrics['avg_hr'] or 0, 2),
                    alerts_count,
                    pending_alerts
                ])
            
            return response
        
        # JSON response
        team_data = []
        for emp in team_employees:
            metrics = ProcessedMetrics.objects.filter(
                employee=emp,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).aggregate(
                avg_fatigue=Avg('fatigue_index'),
                avg_spo2=Avg('spo2_avg'),
                avg_hr=Avg('heart_rate_avg'),
                total_readings=Count('id')
            )
            
            alerts = FatigueAlert.objects.filter(
                employee=emp,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            team_data.append({
                'employee_id': emp.id,
                'employee_name': f"{emp.first_name} {emp.last_name}",
                'employee_email': emp.email,
                'metrics': metrics,
                'total_alerts': alerts.count(),
                'pending_alerts': alerts.filter(is_resolved=False).count(),
            })
        
        return Response({
            'supervisor': {
                'id': supervisor.id,
                'name': f"{supervisor.first_name} {supervisor.last_name}",
            },
            'period': {
                'start': start_date,
                'end': end_date,
            },
            'team_members': len(team_employees),
            'team_data': team_data,
        })

    @action(detail=False, methods=['get'])
    def alerts_report(self, request):
        """
        GET /api/reports/alerts_report/?days=30&format=csv
        
        Reporte detallado de alertas.
        """
        export_format = request.query_params.get('format', 'json')
        start_date, end_date = self._get_date_range(request)
        
        alerts_qs = FatigueAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        alerts_qs = self._filter_by_role(alerts_qs, request.user)
        
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reporte_alertas_{start_date.date()}_to_{end_date.date()}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Fecha', 'Empleado', 'Email', 'Severidad', 
                'Mensaje', 'Resuelto', 'Fecha Resolución', 'Supervisor'
            ])
            
            for alert in alerts_qs.select_related('employee', 'supervisor'):
                writer.writerow([
                    alert.id,
                    alert.created_at,
                    f"{alert.employee.first_name} {alert.employee.last_name}",
                    alert.employee.email,
                    alert.severity,
                    alert.message,
                    'Sí' if alert.resolved else 'No',
                    alert.resolved_at if alert.resolved_at else '',
                    f"{alert.supervisor.first_name} {alert.supervisor.last_name}" if alert.supervisor else ''
                ])
            
            return response
        
        # JSON
        alerts_data = list(alerts_qs.select_related('employee', 'supervisor').values(
            'id', 'created_at', 'employee__first_name', 'employee__last_name',
            'employee__email', 'severity', 'message', 'resolved', 'resolved_at',
            'supervisor__first_name', 'supervisor__last_name'
        ))
        
        return Response({
            'period': {'start': start_date, 'end': end_date},
            'total_alerts': len(alerts_data),
            'alerts': alerts_data,
        })

    @action(detail=False, methods=['get'])
    def metrics_report(self, request):
        """
        GET /api/reports/metrics_report/?days=30&format=csv
        
        Reporte de métricas agregadas por día.
        """
        export_format = request.query_params.get('format', 'json')
        start_date, end_date = self._get_date_range(request)
        
        metrics_qs = ProcessedMetrics.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        metrics_qs = self._filter_by_role(metrics_qs, request.user)
        
        # Agrupar por día
        daily_metrics = metrics_qs.annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            min_fatigue=Min('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            min_spo2=Min('spo2_avg'),
            avg_hr=Avg('heart_rate_avg'),
            max_hr=Max('heart_rate_avg'),
            total_readings=Count('id'),
            employees=Count('employee', distinct=True)
        ).order_by('date')
        
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reporte_metricas_{start_date.date()}_to_{end_date.date()}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Fecha', 'Fatiga Promedio', 'Fatiga Máxima', 'Fatiga Mínima',
                'SpO2 Promedio', 'SpO2 Mínimo', 'FC Promedio', 'FC Máxima',
                'Total Lecturas', 'Empleados Monitoreados'
            ])
            
            for item in daily_metrics:
                writer.writerow([
                    item['date'],
                    round(item['avg_fatigue'], 2),
                    round(item['max_fatigue'], 2),
                    round(item['min_fatigue'], 2),
                    round(item['avg_spo2'], 2),
                    round(item['min_spo2'], 2),
                    round(item['avg_hr'], 2),
                    round(item['max_hr'], 2),
                    item['total_readings'],
                    item['employees']
                ])
            
            return response
        
        # JSON
        return Response({
            'period': {'start': start_date, 'end': end_date},
            'daily_metrics': list(daily_metrics),
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdmin])
    def executive_summary(self, request):
        """
        GET /api/reports/executive_summary/?format=csv
        
        Resumen ejecutivo del sistema (solo Admin).
        """
        export_format = request.query_params.get('format', 'json')
        start_date, end_date = self._get_date_range(request)
        
        # Métricas generales
        total_employees = CustomUser.objects.filter(role='employee').count()
        active_employees = CustomUser.objects.filter(role='employee', is_active=True).count()
        total_devices = Device.objects.count()
        active_devices = Device.objects.filter(is_active=True).count()
        
        # Métricas del período
        metrics = ProcessedMetrics.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(
            avg_fatigue=Avg('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_hr=Avg('heart_rate_avg'),
            total_readings=Count('id')
        )
        
        # Alertas
        alerts = FatigueAlert.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        alerts_summary = {
            'total': alerts.count(),
            'critical': alerts.filter(severity='critical').count(),
            'high': alerts.filter(severity='high').count(),
            'resolved': alerts.filter(is_resolved=True).count(),
            'pending': alerts.filter(is_resolved=False).count(),
        }
        
        # Recomendaciones
        recommendations = RoutineRecommendation.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        rec_summary = {
            'total': recommendations.count(),
            'applied': recommendations.filter(applied=True).count(),
            'rejected': recommendations.filter(rejected=True).count(),
        }
        
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="resumen_ejecutivo_{start_date.date()}_to_{end_date.date()}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['RESUMEN EJECUTIVO DEL SISTEMA'])
            writer.writerow(['Período', f"{start_date.date()} a {end_date.date()}"])
            writer.writerow([])
            
            writer.writerow(['RECURSOS'])
            writer.writerow(['Total Empleados', total_employees])
            writer.writerow(['Empleados Activos', active_employees])
            writer.writerow(['Total Dispositivos', total_devices])
            writer.writerow(['Dispositivos Activos', active_devices])
            writer.writerow([])
            
            writer.writerow(['MÉTRICAS PROMEDIO'])
            writer.writerow(['Fatiga Promedio', round(metrics['avg_fatigue'] or 0, 2)])
            writer.writerow(['SpO2 Promedio', round(metrics['avg_spo2'] or 0, 2)])
            writer.writerow(['FC Promedio', round(metrics['avg_hr'] or 0, 2)])
            writer.writerow(['Total Lecturas', metrics['total_readings']])
            writer.writerow([])
            
            writer.writerow(['ALERTAS'])
            writer.writerow(['Total', alerts_summary['total']])
            writer.writerow(['Críticas', alerts_summary['critical']])
            writer.writerow(['Altas', alerts_summary['high']])
            writer.writerow(['Resueltas', alerts_summary['resolved']])
            writer.writerow(['Pendientes', alerts_summary['pending']])
            writer.writerow([])
            
            writer.writerow(['RECOMENDACIONES'])
            writer.writerow(['Total', rec_summary['total']])
            writer.writerow(['Aplicadas', rec_summary['applied']])
            writer.writerow(['Rechazadas', rec_summary['rejected']])
            
            return response
        
        # JSON
        return Response({
            'period': {'start': start_date, 'end': end_date},
            'resources': {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'total_devices': total_devices,
                'active_devices': active_devices,
            },
            'metrics': metrics,
            'alerts': alerts_summary,
            'recommendations': rec_summary,
        })
