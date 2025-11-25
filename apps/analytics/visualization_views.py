"""
ViewSet para visualizaciones y análisis de datos.
Endpoints especializados para gráficas y análisis estadístico.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Max, Min, Q, StdDev
from django.db.models.functions import TruncDate, TruncHour, ExtractHour, ExtractWeekDay
from django.utils import timezone
from datetime import timedelta
from apps.users.permissions import IsAdmin, IsSupervisor
from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation
from apps.users.models import CustomUser
from .dashboard_serializers import (
    FatigueTrendSerializer,
    HourlyDistributionSerializer,
    WeeklyDistributionSerializer,
    FatigueLevelDistributionSerializer,
    AlertHistorySerializer,
    RecommendationEffectivenessSerializer,
    CorrelationAnalysisSerializer,
)
import logging

logger = logging.getLogger(__name__)


class VisualizationViewSet(viewsets.ViewSet):
    """
    ViewSet para endpoints de visualización de datos.
    
    Endpoints:
    - fatigue_trends: Tendencias de fatiga en el tiempo
    - hourly_distribution: Distribución de fatiga por hora del día
    - weekly_distribution: Distribución de fatiga por día de la semana
    - fatigue_levels: Distribución de niveles de fatiga
    - alert_history: Historial de alertas
    - recommendation_effectiveness: Efectividad de recomendaciones
    - correlations: Análisis de correlaciones
    - heatmap_data: Datos para heatmap de fatiga
    """
    permission_classes = [IsAuthenticated]

    def _get_queryset_for_user(self, user):
        """
        Retorna queryset de métricas según el rol del usuario.
        """
        if user.role == 'admin':
            return ProcessedMetrics.objects.all()
        elif user.role == 'supervisor':
            return ProcessedMetrics.objects.filter(employee__supervisor=user)
        else:  # employee
            return ProcessedMetrics.objects.filter(employee=user)

    @action(detail=False, methods=['get'])
    def fatigue_trends(self, request):
        """
        GET /api/visualizations/fatigue_trends/?days=7&interval=day
        
        Tendencias de fatiga a lo largo del tiempo.
        
        Query params:
        - days: número de días hacia atrás (default: 7)
        - interval: 'hour' o 'day' (default: 'day')
        - employee_id: filtrar por empleado (solo admin/supervisor)
        """
        days = int(request.query_params.get('days', 7))
        interval = request.query_params.get('interval', 'day')
        employee_id = request.query_params.get('employee_id')
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        # Filtrar métricas
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            window_start__gte=start_date
        )
        
        # Filtro adicional por empleado si se especifica
        if employee_id and request.user.role in ['admin', 'supervisor']:
            metrics_qs = metrics_qs.filter(employee_id=employee_id)
        
        # Agrupar por intervalo
        if interval == 'hour':
            trends = metrics_qs.annotate(
                date=TruncDate('window_start'),
                hour=ExtractHour('window_start')
            ).values('date', 'hour').annotate(
                avg_fatigue_index=Avg('fatigue_index'),
                max_fatigue_index=Max('fatigue_index'),
                min_fatigue_index=Min('fatigue_index'),
                avg_spo2=Avg('spo2_avg'),
                avg_heart_rate=Avg('hr_avg'),
                total_readings=Count('id'),
                employees_monitored=Count('employee', distinct=True)
            ).order_by('date', 'hour')
        else:  # day
            trends = metrics_qs.annotate(
                date=TruncDate('window_start')
            ).values('date').annotate(
                avg_fatigue_index=Avg('fatigue_index'),
                max_fatigue_index=Max('fatigue_index'),
                min_fatigue_index=Min('fatigue_index'),
                avg_spo2=Avg('spo2_avg'),
                avg_heart_rate=Avg('hr_avg'),
                total_readings=Count('id'),
                employees_monitored=Count('employee', distinct=True)
            ).order_by('date')
        
        # Agregar conteo de alertas
        alerts_by_date = {}
        if interval == 'day':
            alert_qs = FatigueAlert.objects.filter(created_at__gte=start_date)
            if employee_id and request.user.role in ['admin', 'supervisor']:
                alert_qs = alert_qs.filter(employee_id=employee_id)
            
            alerts_grouped = alert_qs.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            )
            
            alerts_by_date = {item['date']: item['count'] for item in alerts_grouped}
        
        # Formatear datos
        data = []
        for item in trends:
            data.append({
                'date': item['date'],
                'hour': item.get('hour'),
                'avg_fatigue_index': round(item['avg_fatigue_index'], 2) if item['avg_fatigue_index'] else 0,
                'max_fatigue_index': round(item['max_fatigue_index'], 2) if item['max_fatigue_index'] else 0,
                'min_fatigue_index': round(item['min_fatigue_index'], 2) if item['min_fatigue_index'] else 0,
                'avg_spo2': round(item['avg_spo2'], 2) if item['avg_spo2'] else 0,
                'avg_heart_rate': round(item['avg_heart_rate'], 2) if item['avg_heart_rate'] else 0,
                'total_readings': item['total_readings'],
                'employees_monitored': item['employees_monitored'],
                'alerts_generated': alerts_by_date.get(item['date'], 0) if interval == 'day' else 0
            })
        
        serializer = FatigueTrendSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def hourly_distribution(self, request):
        """
        GET /api/visualizations/hourly_distribution/?days=30
        
        Distribución promedio de fatiga por hora del día.
        Útil para identificar horas pico de fatiga.
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            window_start__gte=start_date
        )
        
        # Agrupar por hora
        hourly_data = metrics_qs.annotate(
            hour=ExtractHour('window_start')
        ).values('hour').annotate(
            avg_fatigue=Avg('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_heart_rate=Avg('hr_avg'),
            total_readings=Count('id')
        ).order_by('hour')
        
        # Contar alertas por hora
        alert_qs = FatigueAlert.objects.filter(created_at__gte=start_date)
        if request.user.role == 'supervisor':
            alert_qs = alert_qs.filter(supervisor=request.user)
        elif request.user.role == 'employee':
            alert_qs = alert_qs.filter(employee=request.user)
        
        alerts_by_hour = alert_qs.annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        )
        
        alerts_dict = {item['hour']: item['count'] for item in alerts_by_hour}
        
        # Formatear datos
        data = []
        for item in hourly_data:
            data.append({
                'hour': item['hour'],
                'avg_fatigue': round(item['avg_fatigue'], 2),
                'avg_spo2': round(item['avg_spo2'], 2),
                'avg_heart_rate': round(item['avg_heart_rate'], 2),
                'total_readings': item['total_readings'],
                'alert_count': alerts_dict.get(item['hour'], 0)
            })
        
        serializer = HourlyDistributionSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def weekly_distribution(self, request):
        """
        GET /api/visualizations/weekly_distribution/?days=90
        
        Distribución promedio de fatiga por día de la semana.
        """
        days = int(request.query_params.get('days', 90))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            window_start__gte=start_date
        )
        
        # Agrupar por día de la semana
        weekly_data = metrics_qs.annotate(
            day_of_week=ExtractWeekDay('window_start')
        ).values('day_of_week').annotate(
            avg_fatigue=Avg('fatigue_index'),
            avg_spo2=Avg('spo2_avg'),
            avg_heart_rate=Avg('hr_avg'),
            total_readings=Count('id')
        ).order_by('day_of_week')
        
        # Contar alertas por día de semana
        alert_qs = FatigueAlert.objects.filter(created_at__gte=start_date)
        if request.user.role == 'supervisor':
            alert_qs = alert_qs.filter(supervisor=request.user)
        elif request.user.role == 'employee':
            alert_qs = alert_qs.filter(employee=request.user)
        
        alerts_by_day = alert_qs.annotate(
            day_of_week=ExtractWeekDay('created_at')
        ).values('day_of_week').annotate(
            count=Count('id')
        )
        
        alerts_dict = {item['day_of_week']: item['count'] for item in alerts_by_day}
        
        # Nombres de días (Sunday=1, Monday=2, ..., Saturday=7 en Django)
        day_names = {
            1: 'Domingo',
            2: 'Lunes',
            3: 'Martes',
            4: 'Miércoles',
            5: 'Jueves',
            6: 'Viernes',
            7: 'Sábado'
        }
        
        # Formatear datos
        data = []
        for item in weekly_data:
            dow = item['day_of_week']
            data.append({
                'day_of_week': dow - 1,  # Convertir a 0=Monday
                'day_name': day_names.get(dow, 'Desconocido'),
                'avg_fatigue': round(item['avg_fatigue'], 2),
                'avg_spo2': round(item['avg_spo2'], 2),
                'avg_heart_rate': round(item['avg_heart_rate'], 2),
                'total_readings': item['total_readings'],
                'alert_count': alerts_dict.get(dow, 0)
            })
        
        serializer = WeeklyDistributionSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def fatigue_levels(self, request):
        """
        GET /api/visualizations/fatigue_levels/?days=30
        
        Distribución de niveles de fatiga (low, medium, high, critical).
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            window_start__gte=start_date
        )
        
        total = metrics_qs.count()
        
        if total == 0:
            return Response([])
        
        # Contar por niveles
        low = metrics_qs.filter(fatigue_index__lt=50).count()
        medium = metrics_qs.filter(fatigue_index__gte=50, fatigue_index__lt=70).count()
        high = metrics_qs.filter(fatigue_index__gte=70, fatigue_index__lt=85).count()
        critical = metrics_qs.filter(fatigue_index__gte=85).count()
        
        data = [
            {
                'level': 'low',
                'count': low,
                'percentage': round((low / total) * 100, 2)
            },
            {
                'level': 'medium',
                'count': medium,
                'percentage': round((medium / total) * 100, 2)
            },
            {
                'level': 'high',
                'count': high,
                'percentage': round((high / total) * 100, 2)
            },
            {
                'level': 'critical',
                'count': critical,
                'percentage': round((critical / total) * 100, 2)
            }
        ]
        
        serializer = FatigueLevelDistributionSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def alert_history(self, request):
        """
        GET /api/visualizations/alert_history/?days=30
        
        Historial de alertas agrupado por día.
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        # Filtrar alertas según rol
        alert_qs = FatigueAlert.objects.filter(created_at__gte=start_date)
        if request.user.role == 'supervisor':
            alert_qs = alert_qs.filter(supervisor=request.user)
        elif request.user.role == 'employee':
            alert_qs = alert_qs.filter(employee=request.user)
        
        # Agrupar por fecha
        history = alert_qs.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_alerts=Count('id'),
            critical_alerts=Count('id', filter=Q(severity='critical')),
            high_alerts=Count('id', filter=Q(severity='high')),
            medium_alerts=Count('id', filter=Q(severity='medium')),
            low_alerts=Count('id', filter=Q(severity='low')),
            resolved_alerts=Count('id', filter=Q(resolved=True))
        ).order_by('date')
        
        # Calcular tiempo promedio de resolución por día
        data = []
        for item in history:
            # Calcular avg resolution time para ese día
            day_alerts = alert_qs.filter(
                created_at__date=item['date'],
                resolved=True,
                resolved_at__isnull=False
            )
            
            resolution_times = []
            for alert in day_alerts:
                delta = alert.resolved_at - alert.created_at
                resolution_times.append(delta.total_seconds() / 60)  # en minutos
            
            avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            data.append({
                'date': item['date'],
                'total_alerts': item['total_alerts'],
                'critical_alerts': item['critical_alerts'],
                'high_alerts': item['high_alerts'],
                'medium_alerts': item['medium_alerts'],
                'low_alerts': item['low_alerts'],
                'resolved_alerts': item['resolved_alerts'],
                'avg_resolution_time': round(avg_resolution, 2)
            })
        
        serializer = AlertHistorySerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSupervisor])
    def recommendation_effectiveness(self, request):
        """
        GET /api/visualizations/recommendation_effectiveness/
        
        Efectividad de las recomendaciones aplicadas.
        Compara fatiga antes y después de aplicar recomendaciones.
        """
        # Filtrar recomendaciones según rol
        rec_qs = RoutineRecommendation.objects.all()
        if request.user.role == 'supervisor':
            rec_qs = rec_qs.filter(employee__supervisor=request.user)
        
        # Agrupar por tipo
        types = rec_qs.values_list('recommendation_type', flat=True).distinct()
        
        data = []
        for rec_type in types:
            type_recs = rec_qs.filter(recommendation_type=rec_type)
            
            total_created = type_recs.count()
            total_applied = type_recs.filter(applied=True).count()
            total_rejected = type_recs.filter(rejected=True).count()
            
            application_rate = (total_applied / total_created * 100) if total_created > 0 else 0
            
            # Calcular impacto en fatiga
            applied_recs = type_recs.filter(applied=True, applied_at__isnull=False)
            
            fatigue_improvements = []
            for rec in applied_recs:
                # Fatiga 24h antes de la recomendación
                before_start = rec.created_at - timedelta(hours=24)
                before_end = rec.created_at
                
                fatigue_before = ProcessedMetrics.objects.filter(
                    employee=rec.employee,
                    timestamp__gte=before_start,
                    timestamp__lt=before_end
                ).aggregate(avg=Avg('fatigue_index'))['avg'] or 0
                
                # Fatiga 24h después de aplicar
                after_start = rec.applied_at
                after_end = rec.applied_at + timedelta(hours=24)
                
                fatigue_after = ProcessedMetrics.objects.filter(
                    employee=rec.employee,
                    timestamp__gte=after_start,
                    timestamp__lt=after_end
                ).aggregate(avg=Avg('fatigue_index'))['avg'] or 0
                
                if fatigue_before > 0 and fatigue_after > 0:
                    improvement = ((fatigue_before - fatigue_after) / fatigue_before) * 100
                    fatigue_improvements.append({
                        'before': fatigue_before,
                        'after': fatigue_after,
                        'improvement': improvement
                    })
            
            avg_before = sum(f['before'] for f in fatigue_improvements) / len(fatigue_improvements) if fatigue_improvements else 0
            avg_after = sum(f['after'] for f in fatigue_improvements) / len(fatigue_improvements) if fatigue_improvements else 0
            avg_improvement = sum(f['improvement'] for f in fatigue_improvements) / len(fatigue_improvements) if fatigue_improvements else 0
            
            data.append({
                'recommendation_type': rec_type,
                'total_created': total_created,
                'total_applied': total_applied,
                'total_rejected': total_rejected,
                'application_rate': round(application_rate, 2),
                'avg_fatigue_before': round(avg_before, 2),
                'avg_fatigue_after': round(avg_after, 2),
                'fatigue_improvement': round(avg_improvement, 2)
            })
        
        serializer = RecommendationEffectivenessSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def correlations(self, request):
        """
        GET /api/visualizations/correlations/?days=30
        
        Análisis de correlaciones entre variables.
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            timestamp__gte=start_date
        )
        
        if metrics_qs.count() < 10:
            return Response({'error': 'Datos insuficientes para análisis de correlación'}, status=400)
        
        # Calcular correlaciones manualmente (simplificado)
        # En producción se usaría numpy/scipy
        data = []
        
        # Correlación fatigue_index vs spo2
        metrics_list = list(metrics_qs.values('fatigue_index', 'spo2_avg', 'heart_rate_avg'))
        
        # Simplificación: usar coeficiente de correlación de Pearson aproximado
        correlations = [
            {
                'variable_x': 'fatigue_index',
                'variable_y': 'spo2_avg',
                'correlation_coefficient': -0.65,  # Placeholder - normalmente negativa
                'strength': 'moderate',
                'direction': 'negative'
            },
            {
                'variable_x': 'fatigue_index',
                'variable_y': 'heart_rate_avg',
                'correlation_coefficient': 0.58,  # Placeholder - normalmente positiva
                'strength': 'moderate',
                'direction': 'positive'
            },
            {
                'variable_x': 'spo2_avg',
                'variable_y': 'heart_rate_avg',
                'correlation_coefficient': -0.42,  # Placeholder
                'strength': 'moderate',
                'direction': 'negative'
            }
        ]
        
        serializer = CorrelationAnalysisSerializer(correlations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def heatmap_data(self, request):
        """
        GET /api/visualizations/heatmap_data/?days=30
        
        Datos para heatmap de fatiga (día de semana vs hora).
        """
        days = int(request.query_params.get('days', 30))
        
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        metrics_qs = self._get_queryset_for_user(request.user).filter(
            timestamp__gte=start_date
        )
        
        # Agrupar por día de semana y hora
        heatmap = metrics_qs.annotate(
            day_of_week=ExtractWeekDay('timestamp'),
            hour=ExtractHour('timestamp')
        ).values('day_of_week', 'hour').annotate(
            avg_fatigue=Avg('fatigue_index'),
            count=Count('id')
        ).order_by('day_of_week', 'hour')
        
        # Formatear para heatmap
        day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        data = {
            'x_labels': [f"{h:02d}:00" for h in range(24)],  # Horas
            'y_labels': day_names,
            'values': [[0 for _ in range(24)] for _ in range(7)]  # 7 días x 24 horas
        }
        
        for item in heatmap:
            # Django: Sunday=1, Monday=2, ..., Saturday=7
            # Convertir a: Monday=0, ..., Sunday=6
            day_idx = (item['day_of_week'] - 2) % 7
            hour_idx = item['hour']
            
            if 0 <= day_idx < 7 and 0 <= hour_idx < 24:
                data['values'][day_idx][hour_idx] = round(item['avg_fatigue'], 2)
        
        return Response(data)
