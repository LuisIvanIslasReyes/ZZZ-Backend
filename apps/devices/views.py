"""
Vistas API para dispositivos ESP32.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Max, Q
from django.utils import timezone
from datetime import timedelta

from .models import Device
from .serializers import (
    DeviceListSerializer,
    DeviceDetailSerializer,
    DeviceCreateSerializer,
    DeviceUpdateSerializer,
    DeviceStatusUpdateSerializer,
)
from apps.users.permissions import IsAdmin, IsAdminOrSupervisor, IsOwnerOrSupervisor


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar dispositivos ESP32.
    
    Permisos:
    - Admin: Puede ver y gestionar todos los dispositivos
    - Supervisor: Puede ver y gestionar dispositivos de sus empleados
    - Empleado: Solo puede ver su propio dispositivo (read-only)
    
    Endpoints:
    - GET /api/devices/ - Listar dispositivos
    - POST /api/devices/ - Crear dispositivo (Admin, Supervisor)
    - GET /api/devices/{id}/ - Ver detalle de dispositivo
    - PUT/PATCH /api/devices/{id}/ - Actualizar dispositivo
    - DELETE /api/devices/{id}/ - Eliminar dispositivo
    - POST /api/devices/{id}/activate/ - Activar dispositivo
    - POST /api/devices/{id}/deactivate/ - Desactivar dispositivo
    - GET /api/devices/{id}/stats/ - Estadísticas del dispositivo
    - GET /api/devices/my_device/ - Obtener dispositivo del empleado actual
    """
    
    queryset = Device.objects.select_related('employee', 'supervisor').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['device_id', 'name', 'employee__first_name', 'employee__last_name', 'employee__email']
    ordering_fields = ['created_at', 'last_connection', 'status', 'battery_level']
    ordering = ['-created_at']
    pagination_class = None  # Deshabilitar paginación
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return DeviceListSerializer
        elif self.action in ['create']:
            return DeviceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DeviceUpdateSerializer
        elif self.action in ['activate', 'deactivate']:
            return DeviceStatusUpdateSerializer
        else:
            return DeviceDetailSerializer
    
    def get_queryset(self):
        """
        Filtrar dispositivos según el rol del usuario y la empresa.
        """
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'admin':
            # Admin ve todos los dispositivos de todas las empresas
            pass
        elif user.role == 'supervisor':
            # Supervisor ve dispositivos de empleados de su empresa
            queryset = queryset.filter(company=user.company)
        else:  # employee
            # Empleado solo ve su propio dispositivo
            queryset = queryset.filter(employee=user)
        
        # Filtros adicionales por query params
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        company_id = self.request.query_params.get('company')
        if company_id and user.role == 'admin':
            queryset = queryset.filter(company_id=company_id)
        
        employee_id = self.request.query_params.get('employee')
        if employee_id and user.role in ['admin', 'supervisor']:
            queryset = queryset.filter(employee_id=employee_id)
        
        supervisor_id = self.request.query_params.get('supervisor')
        if supervisor_id and user.role == 'admin':
            queryset = queryset.filter(supervisor_id=supervisor_id)
        
        return queryset
    
    def get_permissions(self):
        """
        Permisos según la acción.
        """
        if self.action in ['create', 'destroy']:
            # Solo Admin y Supervisor pueden crear/eliminar
            return [IsAuthenticated(), IsAdminOrSupervisor()]
        elif self.action in ['update', 'partial_update', 'activate', 'deactivate']:
            # Solo Admin y Supervisor propietario pueden actualizar
            return [IsAuthenticated(), IsOwnerOrSupervisor()]
        else:
            # Listar y ver detalles requiere autenticación
            return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """
        Crear dispositivo y asignar supervisor y empresa automáticamente.
        El dispositivo hereda la empresa del supervisor/empleado.
        """
        employee = serializer.validated_data.get('employee')
        user = self.request.user
        
        # Determinar empresa y supervisor
        if user.role == 'supervisor':
            # Supervisor crea dispositivo para empleado de su empresa
            if employee.company != user.company:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("No puedes asignar dispositivos a empleados de otra empresa")
            serializer.save(
                supervisor=user,
                company=user.company
            )
        elif user.role == 'admin':
            # Admin debe especificar o usa la empresa del empleado
            if employee:
                serializer.save(
                    supervisor=employee.supervisor,
                    company=employee.company
                )
            else:
                serializer.save()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permisos para crear dispositivos")
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activar un dispositivo.
        """
        device = self.get_object()
        device.is_active = True
        device.status = 'idle'
        device.save()
        
        serializer = self.get_serializer(device)
        return Response({
            'message': f'Dispositivo {device.device_id} activado exitosamente',
            'device': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Desactivar un dispositivo.
        """
        device = self.get_object()
        device.is_active = False
        device.status = 'idle'
        device.save()
        
        serializer = self.get_serializer(device)
        return Response({
            'message': f'Dispositivo {device.device_id} desactivado exitosamente',
            'device': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Obtener estadísticas del dispositivo.
        """
        device = self.get_object()
        
        # Rango de fechas (últimos 7 días por defecto)
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Estadísticas de datos de sensores
        sensor_stats = device.sensor_data.filter(
            timestamp__gte=start_date
        ).aggregate(
            total_records=Count('id'),
            avg_heart_rate=Avg('heart_rate'),
            max_heart_rate=Max('heart_rate'),
            avg_spo2=Avg('spo2'),
            min_spo2=Avg('spo2')
        )
        
        # Estadísticas de métricas procesadas
        metrics_stats = device.processed_metrics.filter(
            window_start__gte=start_date
        ).aggregate(
            total_windows=Count('id'),
            avg_fatigue=Avg('fatigue_index'),
            max_fatigue=Max('fatigue_index'),
            avg_hrv=Avg('hrv_rmssd'),
            total_desaturations=Count('id', filter=Q(desaturation_count__gt=0))
        )
        
        # Conteo de niveles de fatiga
        fatigue_distribution = {
            'low': device.processed_metrics.filter(
                window_start__gte=start_date,
                fatigue_index__lt=40
            ).count(),
            'medium': device.processed_metrics.filter(
                window_start__gte=start_date,
                fatigue_index__gte=40,
                fatigue_index__lt=70
            ).count(),
            'high': device.processed_metrics.filter(
                window_start__gte=start_date,
                fatigue_index__gte=70
            ).count(),
        }
        
        # Conteo de alertas
        alerts_count = device.employee.fatigue_alerts.filter(
            created_at__gte=start_date
        ).count()
        
        return Response({
            'device_id': device.device_id,
            'period_days': days,
            'sensor_data': sensor_stats,
            'processed_metrics': metrics_stats,
            'fatigue_distribution': fatigue_distribution,
            'alerts_count': alerts_count,
            'uptime_hours': round((timezone.now() - device.created_at).total_seconds() / 3600, 2),
            'last_connection': device.last_connection,
        })
    
    @action(detail=False, methods=['get'])
    def my_device(self, request):
        """
        Obtener el dispositivo del empleado actual.
        Útil para empleados que solo tienen un dispositivo.
        """
        user = request.user
        
        if user.role != 'employee':
            return Response(
                {'error': 'Este endpoint es solo para empleados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            device = Device.objects.get(employee=user, is_active=True)
            serializer = DeviceDetailSerializer(device)
            return Response(serializer.data)
        except Device.DoesNotExist:
            return Response(
                {'error': 'No tienes un dispositivo asignado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Device.MultipleObjectsReturned:
            # Si hay múltiples, devolver el más reciente
            device = Device.objects.filter(employee=user, is_active=True).latest('created_at')
            serializer = DeviceDetailSerializer(device)
            return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Resumen de dispositivos según el rol del usuario.
        """
        queryset = self.get_queryset()
        
        summary = {
            'total': queryset.count(),
            'active': queryset.filter(is_active=True).count(),
            'inactive': queryset.filter(is_active=False).count(),
            'by_status': {
                'idle': queryset.filter(status='idle').count(),
                'active': queryset.filter(status='active').count(),
                'maintenance': queryset.filter(status='maintenance').count(),
                'error': queryset.filter(status='error').count(),
            },
            'online': queryset.filter(
                last_connection__gte=timezone.now() - timedelta(minutes=5)
            ).count(),
            'low_battery': queryset.filter(battery_level__lt=20).count(),
        }
        
        return Response(summary)
