# apps/analytics/supervisor_dashboard_views.py
"""
Vistas específicas para el Dashboard del Supervisor
Resuelve errores 404 y provee datos para gráficas útiles
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Avg, Count, Q, Max, Min
from datetime import datetime, timedelta
from django.utils import timezone
from apps.users.models import CustomUser
from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import FatigueAlert, ScheduledBreak
from apps.users.permissions import IsSupervisor


class SupervisorTeamStatsView(APIView):
    """
    GET /api/supervisor/team-stats/
    
    Estadísticas generales del equipo del supervisor
    """
    permission_classes = [IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        supervisor = request.user
        team = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        
        # Empleados con dispositivo activo
        employees_with_device = team.filter(device__isnull=False).count()
        
        # Alertas activas (últimas 24h)
        active_alerts = FatigueAlert.objects.filter(
            employee__in=team,
            is_resolved=False,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Nivel promedio de fatiga del equipo (hoy)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        avg_fatigue = ProcessedMetrics.objects.filter(
            employee__in=team,
            timestamp__gte=today_start
        ).aggregate(avg=Avg('fatigue_index'))['avg'] or 0
        
        # Empleados en riesgo (fatiga > 70)
        employees_at_risk = ProcessedMetrics.objects.filter(
            employee__in=team,
            timestamp__gte=today_start,
            fatigue_index__gt=70
        ).values('employee').distinct().count()
        
        return Response({
            'total_employees': team.count(),
            'employees_with_device': employees_with_device,
            'active_alerts': active_alerts,
            'avg_fatigue': round(avg_fatigue, 2),
            'employees_at_risk': employees_at_risk,
            'team_status': 'stable' if employees_at_risk == 0 else 'attention_required'
        })


class SupervisorFatigueTrendsView(APIView):
    """
    GET /api/supervisor/fatigue-trends/?days=7
    
    Tendencia de fatiga del equipo (últimos N días)
    """
    permission_classes = [IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        days = int(request.query_params.get('days', 7))
        supervisor = request.user
        team = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Agrupar por día
        daily_data = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            metrics = ProcessedMetrics.objects.filter(
                employee__in=team,
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).aggregate(
                avg_fatigue=Avg('fatigue_index'),
                max_fatigue=Max('fatigue_index'),
                min_fatigue=Min('fatigue_index')
            )
            
            daily_data.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'avg_fatigue': round(metrics['avg_fatigue'] or 0, 2),
                'max_fatigue': round(metrics['max_fatigue'] or 0, 2),
                'min_fatigue': round(metrics['min_fatigue'] or 0, 2)
            })
        
        return Response({
            'period': f'{days} días',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'data': daily_data
        })


class SupervisorEmployeeRiskDistributionView(APIView):
    """
    GET /api/supervisor/risk-distribution/
    
    Distribución de empleados por nivel de riesgo
    """
    permission_classes = [IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        supervisor = request.user
        team = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        
        # Últimas métricas de cada empleado (últimas 2 horas)
        time_threshold = timezone.now() - timedelta(hours=2)
        
        risk_levels = {
            'normal': [],      # fatigue < 50
            'attention': [],   # 50 <= fatigue < 70
            'high_risk': []    # fatigue >= 70
        }
        
        for employee in team:
            latest_metric = ProcessedMetrics.objects.filter(
                employee=employee,
                timestamp__gte=time_threshold
            ).order_by('-timestamp').first()
            
            if latest_metric:
                employee_data = {
                    'id': employee.id,
                    'name': employee.get_full_name(),
                    'email': employee.email,
                    'fatigue': round(latest_metric.fatigue_index, 2),
                    'timestamp': latest_metric.timestamp.isoformat()
                }
                
                if latest_metric.fatigue_index < 50:
                    risk_levels['normal'].append(employee_data)
                elif latest_metric.fatigue_index < 70:
                    risk_levels['attention'].append(employee_data)
                else:
                    risk_levels['high_risk'].append(employee_data)
        
        return Response({
            'total_employees': team.count(),
            'employees_monitored': len(risk_levels['normal']) + len(risk_levels['attention']) + len(risk_levels['high_risk']),
            'distribution': {
                'normal': {
                    'count': len(risk_levels['normal']),
                    'percentage': round(len(risk_levels['normal']) / max(team.count(), 1) * 100, 1),
                    'employees': risk_levels['normal']
                },
                'attention': {
                    'count': len(risk_levels['attention']),
                    'percentage': round(len(risk_levels['attention']) / max(team.count(), 1) * 100, 1),
                    'employees': risk_levels['attention']
                },
                'high_risk': {
                    'count': len(risk_levels['high_risk']),
                    'percentage': round(len(risk_levels['high_risk']) / max(team.count(), 1) * 100, 1),
                    'employees': risk_levels['high_risk']
                }
            }
        })


class SupervisorActivityVsFatigueView(APIView):
    """
    GET /api/supervisor/activity-vs-fatigue/?days=7
    
    Correlación entre actividad y fatiga del equipo
    """
    permission_classes = [IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        days = int(request.query_params.get('days', 7))
        supervisor = request.user
        team = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        daily_correlation = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            metrics = ProcessedMetrics.objects.filter(
                employee__in=team,
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).aggregate(
                avg_activity=Avg('activity_level'),
                avg_fatigue=Avg('fatigue_index')
            )
            
            daily_correlation.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'activity_level': round(metrics['avg_activity'] or 0, 2),
                'fatigue_level': round(metrics['avg_fatigue'] or 0, 2)
            })
        
        return Response({
            'period': f'{days} días',
            'data': daily_correlation
        })


class SupervisorWorkingHoursView(APIView):
    """
    GET /api/supervisor/working-hours/?days=7
    
    Horas activas del equipo comparadas con recomendaciones
    """
    permission_classes = [IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        days = int(request.query_params.get('days', 7))
        supervisor = request.user
        team = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        daily_hours = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            # Contar registros de métricas (cada 5 min aprox)
            total_records = ProcessedMetrics.objects.filter(
                employee__in=team,
                timestamp__gte=day_start,
                timestamp__lt=day_end
            ).count()
            
            # Estimar horas activas (12 registros por hora = 5 min cada uno)
            active_hours = round(total_records / 12, 1)
            recommended_hours = 8  # Horas recomendadas
            
            daily_hours.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'active_hours': active_hours,
                'recommended_hours': recommended_hours,
                'difference': round(active_hours - recommended_hours, 1)
            })
        
        return Response({
            'period': f'{days} días',
            'data': daily_hours
        })


class SupervisorBreaksSummaryView(APIView):
    """
    GET /api/supervisor/breaks-summary/
    
    Resumen de descansos programados (pendientes, aprobados, rechazados)
    """
    permission_classes = [IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        supervisor = request.user
        team = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        
        # Contar por estado
        pending = ScheduledBreak.objects.filter(
            employee__in=team,
            status='pending'
        ).count()
        
        approved = ScheduledBreak.objects.filter(
            employee__in=team,
            status='approved'
        ).count()
        
        rejected = ScheduledBreak.objects.filter(
            employee__in=team,
            status='rejected'
        ).count()
        
        completed = ScheduledBreak.objects.filter(
            employee__in=team,
            status='completed'
        ).count()
        
        # Descansos de hoy
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        today_breaks = ScheduledBreak.objects.filter(
            employee__in=team,
            scheduled_date=today_start.date()
        ).values('status').annotate(count=Count('id'))
        
        return Response({
            'total': {
                'pending': pending,
                'approved': approved,
                'rejected': rejected,
                'completed': completed
            },
            'today': {
                item['status']: item['count'] for item in today_breaks
            },
            'pending_requires_action': pending > 0
        })


class SupervisorAlertsTimelineView(APIView):
    """
    GET /api/supervisor/alerts-timeline/?days=7
    
    Línea de tiempo de alertas generadas
    """
    permission_classes = [IsAuthenticated, IsSupervisor]
    
    def get(self, request):
        days = int(request.query_params.get('days', 7))
        supervisor = request.user
        team = CustomUser.objects.filter(supervisor=supervisor, role='employee')
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        daily_alerts = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            alerts = FatigueAlert.objects.filter(
                employee__in=team,
                created_at__gte=day_start,
                created_at__lt=day_end
            ).aggregate(
                total=Count('id'),
                high_priority=Count('id', filter=Q(severity='high')),
                medium_priority=Count('id', filter=Q(severity='medium')),
                low_priority=Count('id', filter=Q(severity='low'))
            )
            
            daily_alerts.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'total_alerts': alerts['total'] or 0,
                'high_priority': alerts['high_priority'] or 0,
                'medium_priority': alerts['medium_priority'] or 0,
                'low_priority': alerts['low_priority'] or 0
            })
        
        return Response({
            'period': f'{days} días',
            'data': daily_alerts
        })
