"""
Vistas API para datos de sensores y métricas procesadas.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Max, Min, Count, Q
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend

from .models import SensorData, ProcessedMetrics
from .serializers import (
    SensorDataListSerializer,
    SensorDataDetailSerializer,
    SensorDataCreateSerializer,
    SensorDataBulkCreateSerializer,
    ProcessedMetricsListSerializer,
    ProcessedMetricsDetailSerializer,
    ProcessedMetricsStatsSerializer,
)
from apps.users.permissions import IsAdmin, IsAdminOrSupervisor


class SensorDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet para datos de sensores.
    
    Permisos:
    - Admin: Acceso completo
    - Supervisor: Ver datos de sus empleados
    - Empleado: Solo ver sus propios datos
    
    Endpoints:
    - GET /api/sensor-data/ - Listar datos
    - POST /api/sensor-data/ - Crear registro (MQTT, simuladores)
    - GET /api/sensor-data/{id}/ - Ver detalle
    - POST /api/sensor-data/bulk_create/ - Crear múltiples registros
    - GET /api/sensor-data/latest/ - Últimos datos por dispositivo
    """
    
    queryset = SensorData.objects.select_related(
        'device', 
        'device__employee',
        'device__employee__supervisor'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['device', 'device__employee']
    ordering_fields = ['timestamp', 'created_at', 'heart_rate', 'spo2']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return SensorDataListSerializer
        elif self.action == 'create':
            return SensorDataCreateSerializer
        elif self.action == 'bulk_create':
            return SensorDataBulkCreateSerializer
        else:
            return SensorDataDetailSerializer
    
    def get_queryset(self):
        """
        Filtrar datos según el rol del usuario.
        """
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'admin':
            # Admin ve todos los datos
            pass
        elif user.role == 'supervisor':
            # Supervisor ve datos de sus empleados
            queryset = queryset.filter(device__supervisor=user)
        else:  # employee
            # Empleado solo ve sus propios datos
            queryset = queryset.filter(device__employee=user)
        
        # Filtros por query params
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device__device_id=device_id)
        
        # Filtro por rango de fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Filtro por últimas N horas
        hours = self.request.query_params.get('hours')
        if hours:
            start_time = timezone.now() - timedelta(hours=int(hours))
            queryset = queryset.filter(timestamp__gte=start_time)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Crear múltiples registros de sensores a la vez.
        Útil para batch processing o sincronización offline.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        return Response({
            'message': 'Registros creados exitosamente',
            'created_count': result['created_count']
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Obtener los últimos datos de cada dispositivo.
        """
        queryset = self.get_queryset()
        
        # Agrupar por dispositivo y obtener el más reciente
        devices = queryset.values('device').distinct()
        latest_data = []
        
        for device_dict in devices:
            latest = queryset.filter(device=device_dict['device']).latest('timestamp')
            serializer = SensorDataDetailSerializer(latest)
            latest_data.append(serializer.data)
        
        return Response(latest_data)


class ProcessedMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para métricas procesadas (solo lectura).
    Las métricas se generan automáticamente por el procesador.
    
    Permisos:
    - Admin: Acceso completo
    - Supervisor: Ver métricas de sus empleados
    - Empleado: Solo ver sus propias métricas
    
    Endpoints:
    - GET /api/processed-metrics/ - Listar métricas
    - GET /api/processed-metrics/{id}/ - Ver detalle
    - GET /api/processed-metrics/stats/ - Estadísticas agregadas
    - GET /api/processed-metrics/latest/ - Últimas métricas por empleado
    - GET /api/processed-metrics/timeline/ - Timeline de fatiga
    """
    
    queryset = ProcessedMetrics.objects.select_related(
        'device',
        'employee',
        'employee__supervisor',
        'device__employee'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['device', 'employee']
    ordering_fields = ['window_start', 'window_end', 'fatigue_index', 'hr_avg', 'spo2_avg']
    ordering = ['-window_end']
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return ProcessedMetricsListSerializer
        elif self.action == 'stats':
            return ProcessedMetricsStatsSerializer
        else:
            return ProcessedMetricsDetailSerializer
    
    def get_queryset(self):
        """
        Filtrar métricas según el rol del usuario.
        """
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'admin':
            # Admin ve todas las métricas
            pass
        elif user.role == 'supervisor':
            # Supervisor ve métricas de sus empleados
            queryset = queryset.filter(device__supervisor=user)
        else:  # employee
            # Empleado solo ve sus propias métricas
            queryset = queryset.filter(employee=user)
        
        # Filtros por query params
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device__device_id=device_id)
        
        employee_id = self.request.query_params.get('employee_id')
        if employee_id and user.role in ['admin', 'supervisor']:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filtro por rango de fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(window_start__gte=start_date)
        if end_date:
            queryset = queryset.filter(window_end__lte=end_date)
        
        # Filtro por nivel de fatiga
        fatigue_level = self.request.query_params.get('fatigue_level')
        if fatigue_level == 'low':
            queryset = queryset.filter(fatigue_index__lt=40)
        elif fatigue_level == 'medium':
            queryset = queryset.filter(fatigue_index__gte=40, fatigue_index__lt=70)
        elif fatigue_level == 'high':
            queryset = queryset.filter(fatigue_index__gte=70)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Estadísticas agregadas de métricas.
        """
        queryset = self.get_queryset()
        
        # Rango de fechas
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(window_start__gte=start_date)
        
        # Calcular estadísticas
        stats = queryset.aggregate(
            avg_fatigue_index=Avg('fatigue_index'),
            max_fatigue_index=Max('fatigue_index'),
            min_fatigue_index=Min('fatigue_index'),
            avg_heart_rate=Avg('hr_avg'),
            avg_spo2=Avg('spo2_avg'),
            total_desaturations=Count('id', filter=Q(desaturation_count__gt=0))
        )
        
        # Conteo por nivel de fatiga
        stats['high_fatigue_count'] = queryset.filter(fatigue_index__gte=70).count()
        stats['medium_fatigue_count'] = queryset.filter(fatigue_index__gte=40, fatigue_index__lt=70).count()
        stats['low_fatigue_count'] = queryset.filter(fatigue_index__lt=40).count()
        stats['period'] = f'last_{days}_days'
        
        serializer = ProcessedMetricsStatsSerializer(data=stats)
        serializer.is_valid()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Obtener las últimas métricas de cada empleado.
        """
        queryset = self.get_queryset()
        
        # Agrupar por empleado y obtener el más reciente
        employees = queryset.values('employee').distinct()
        latest_metrics = []
        
        for employee_dict in employees:
            latest = queryset.filter(employee=employee_dict['employee']).latest('window_end')
            serializer = ProcessedMetricsDetailSerializer(latest)
            latest_metrics.append(serializer.data)
        
        return Response(latest_metrics)
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """
        Timeline de fatiga para visualización.
        Agrupa métricas por intervalos de tiempo.
        """
        queryset = self.get_queryset()
        
        # Parámetros
        hours = int(request.query_params.get('hours', 24))
        interval_minutes = int(request.query_params.get('interval', 60))
        
        start_time = timezone.now() - timedelta(hours=hours)
        queryset = queryset.filter(window_start__gte=start_time)
        
        # Obtener datos ordenados
        data = queryset.values(
            'window_end',
            'fatigue_index',
            'hr_avg',
            'spo2_avg',
            'employee__first_name',
            'employee__last_name',
            'device__device_id'
        ).order_by('window_end')
        
        return Response({
            'start_time': start_time,
            'end_time': timezone.now(),
            'interval_minutes': interval_minutes,
            'data_points': list(data)
        })
