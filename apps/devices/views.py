"""
Views for devices and sensors
"""
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Avg, Min, Max, Count
from datetime import timedelta
from .models import Device, SensorPacket, SensorSample, StressAggregate
from .serializers import (
    DeviceSerializer,
    SensorPacketSerializer,
    BatchSensorDataSerializer,
    StressAggregateSerializer,
    StressSummarySerializer,
)
from apps.authentication.permissions import IsOwnerOrSupervisor, IsSupervisor

User = get_user_model()


class DeviceListCreateView(generics.ListCreateAPIView):
    """
    List all devices or create a new device
    """
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_supervisor:
            return Device.objects.all()
        return Device.objects.filter(employee=user)
    
    def perform_create(self, serializer):
        # Employee can only register devices for themselves
        if not (self.request.user.is_admin or self.request.user.is_supervisor):
            serializer.save(employee=self.request.user)
        else:
            serializer.save()


class DeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a device
    """
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin or user.is_supervisor:
            return Device.objects.all()
        return Device.objects.filter(employee=user)


class BatchSensorDataView(APIView):
    """
    Batch ingestion endpoint for sensor data
    POST /api/sensor-data/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BatchSensorDataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        device_id = serializer.validated_data['device_id']
        firmware_version = serializer.validated_data.get('firmware_version', '')
        samples = serializer.validated_data['samples']
        
        # Get device
        device = Device.objects.get(hardware_id=device_id)
        
        # Check authorization (employee can only upload for their own devices)
        if not (request.user.is_admin or request.user.is_supervisor):
            if device.employee != request.user:
                return Response(
                    {'error': 'No autorizado para este dispositivo'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Update device last_seen and firmware
        device.last_seen = timezone.now()
        if firmware_version:
            device.firmware_version = firmware_version
        device.save()
        
        # Create sensor packet
        packet = SensorPacket.objects.create(
            device=device,
            packet_timestamp=timezone.now(),
            raw_payload={
                'samples': samples,
                'firmware_version': firmware_version,
                'received_count': len(samples)
            }
        )
        
        # Create sensor samples
        sample_objects = []
        for sample_data in samples:
            sample = SensorSample(
                packet=packet,
                sample_time=sample_data['timestamp'],
                heart_rate=sample_data.get('hr'),
                spo2=sample_data.get('spo2'),
                accel_x=sample_data.get('accel_x'),
                accel_y=sample_data.get('accel_y'),
                accel_z=sample_data.get('accel_z'),
                steps=sample_data.get('steps'),
                battery_level=sample_data.get('battery')
            )
            sample_objects.append(sample)
        
        # Bulk create for efficiency
        SensorSample.objects.bulk_create(sample_objects)
        
        # Trigger async processing
        from .tasks import process_sensor_packet
        process_sensor_packet.delay(packet.id)
        
        return Response({
            'message': 'Datos recibidos exitosamente',
            'packet_id': packet.id,
            'samples_count': len(sample_objects)
        }, status=status.HTTP_201_CREATED)


class EmployeeStressView(generics.ListAPIView):
    """
    Get stress aggregates for an employee
    GET /api/employees/{employee_id}/stress/
    """
    serializer_class = StressAggregateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        
        # Date range filter
        days = int(self.request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        return StressAggregate.objects.filter(
            employee_id=employee_id,
            window_start__gte=start_date
        ).order_by('-window_start')


class EmployeeStressSummaryView(APIView):
    """
    Get stress summary statistics for an employee
    GET /api/employees/{employee_id}/stress/summary/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get(self, request, employee_id):
        # Date range filter
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get aggregates
        aggregates = StressAggregate.objects.filter(
            employee_id=employee_id,
            window_start__gte=start_date
        )
        
        if not aggregates.exists():
            return Response({
                'message': 'No hay datos de estrés disponibles',
                'data_points': 0
            })
        
        # Calculate statistics
        stats = aggregates.aggregate(
            avg_stress=Avg('stress_score'),
            min_stress=Min('stress_score'),
            max_stress=Max('stress_score'),
            count=Count('id')
        )
        
        # Get current stress (most recent)
        current = aggregates.order_by('-window_start').first()
        
        # Calculate trend (simple: compare first half vs second half)
        half_date = start_date + (timezone.now() - start_date) / 2
        first_half_avg = aggregates.filter(
            window_start__lt=half_date
        ).aggregate(avg=Avg('stress_score'))['avg'] or 0
        second_half_avg = aggregates.filter(
            window_start__gte=half_date
        ).aggregate(avg=Avg('stress_score'))['avg'] or 0
        
        if second_half_avg > first_half_avg + 5:
            trend = 'increasing'
        elif second_half_avg < first_half_avg - 5:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        summary = {
            'avg_stress': stats['avg_stress'],
            'min_stress': stats['min_stress'],
            'max_stress': stats['max_stress'],
            'current_stress': current.stress_score,
            'trend': trend,
            'data_points': stats['count']
        }
        
        serializer = StressSummarySerializer(summary)
        return Response(serializer.data)


class SupervisorReportsView(APIView):
    """
    Get aggregated reports for supervisor
    GET /api/supervisor/reports/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request):
        user = request.user
        
        # Get supervised employees
        if user.is_admin:
            employees = User.objects.filter(role=User.Role.EMPLOYEE)
        else:
            employees = User.objects.filter(employee_profile__supervisor=user)
        
        # Date range
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Build report
        report = []
        for employee in employees:
            aggregates = StressAggregate.objects.filter(
                employee=employee,
                window_start__gte=start_date
            )
            
            if aggregates.exists():
                stats = aggregates.aggregate(
                    avg_stress=Avg('stress_score'),
                    max_stress=Max('stress_score')
                )
                current = aggregates.order_by('-window_start').first()
                
                report.append({
                    'employee_id': employee.id,
                    'employee_name': employee.get_full_name(),
                    'avg_stress': round(stats['avg_stress'], 2),
                    'max_stress': round(stats['max_stress'], 2),
                    'current_stress': round(current.stress_score, 2),
                    'data_points': aggregates.count()
                })
        
        # Sort by current stress (highest first)
        report.sort(key=lambda x: x.get('current_stress', 0), reverse=True)
        
        return Response({
            'employees_count': len(report),
            'date_range_days': days,
            'reports': report
        })
