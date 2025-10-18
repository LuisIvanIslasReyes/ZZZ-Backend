"""
Department views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Department, DepartmentMembership, WorkShift, ShiftAssignment
from .serializers import (
    DepartmentSerializer,
    DepartmentCreateSerializer,
    DepartmentMembershipSerializer,
    WorkShiftSerializer,
    WorkShiftCreateSerializer,
    ShiftAssignmentSerializer,
    DepartmentStatsSerializer
)
from apps.authentication.permissions import IsSupervisor
from apps.devices.models import StressAggregate, Device
from apps.alerts.models import Alert

User = get_user_model()


class DepartmentListCreateView(generics.ListCreateAPIView):
    """
    List all departments or create a new department
    GET/POST /api/departments/
    """
    permission_classes = [IsSupervisor]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DepartmentCreateSerializer
        return DepartmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Department.objects.filter(is_active=True)
        
        # Filter by user permissions if not admin
        if not user.is_admin:
            # Supervisor can see their managed departments and departments of supervised employees
            managed_departments = queryset.filter(manager=user)
            supervised_employee_departments = queryset.filter(
                employees__employee_profile__supervisor=user
            )
            queryset = (managed_departments | supervised_employee_departments).distinct()
        
        return queryset.select_related('manager', 'parent_department').prefetch_related('sub_departments')


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a department
    GET/PUT/DELETE /api/departments/<id>/
    """
    serializer_class = DepartmentSerializer
    permission_classes = [IsSupervisor]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Department.objects.all()
        
        if not user.is_admin:
            managed_departments = queryset.filter(manager=user)
            supervised_employee_departments = queryset.filter(
                employees__employee_profile__supervisor=user
            )
            queryset = (managed_departments | supervised_employee_departments).distinct()
        
        return queryset.select_related('manager', 'parent_department')


class DepartmentEmployeesView(generics.ListAPIView):
    """
    Get employees of a specific department
    GET /api/departments/<id>/employees/
    """
    serializer_class = DepartmentMembershipSerializer
    permission_classes = [IsSupervisor]
    
    def get_queryset(self):
        department_id = self.kwargs['pk']
        
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return DepartmentMembership.objects.none()
        
        # Check permissions
        user = self.request.user
        if not user.is_admin:
            if department.manager != user and not department.employees.filter(
                employee_profile__supervisor=user
            ).exists():
                return DepartmentMembership.objects.none()
        
        return DepartmentMembership.objects.filter(
            department=department,
            left_at__isnull=True
        ).select_related('user', 'department')


class DepartmentAddEmployeeView(APIView):
    """
    Add employee to department
    POST /api/departments/<id>/employees/
    """
    permission_classes = [IsSupervisor]
    
    def post(self, request, pk):
        try:
            department = Department.objects.get(id=pk)
        except Department.DoesNotExist:
            return Response(
                {'error': 'Departamento no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if not user.is_admin and department.manager != user:
            return Response(
                {'error': 'Sin permisos para gestionar este departamento'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        position = request.data.get('position', '')
        is_primary = request.data.get('is_primary', True)
        
        if not user_id:
            return Response(
                {'error': 'user_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if membership already exists
        membership, created = DepartmentMembership.objects.get_or_create(
            user=employee,
            department=department,
            defaults={
                'position': position,
                'is_primary': is_primary
            }
        )
        
        if not created and membership.left_at is not None:
            # Reactivate membership
            membership.left_at = None
            membership.position = position
            membership.is_primary = is_primary
            membership.save()
        elif not created:
            return Response(
                {'error': 'El empleado ya pertenece a este departamento'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DepartmentMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DepartmentRemoveEmployeeView(APIView):
    """
    Remove employee from department
    DELETE /api/departments/<id>/employees/<user_id>/
    """
    permission_classes = [IsSupervisor]
    
    def delete(self, request, pk, user_id):
        try:
            department = Department.objects.get(id=pk)
            membership = DepartmentMembership.objects.get(
                department=department,
                user_id=user_id,
                left_at__isnull=True
            )
        except (Department.DoesNotExist, DepartmentMembership.DoesNotExist):
            return Response(
                {'error': 'Membership no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if not user.is_admin and department.manager != user:
            return Response(
                {'error': 'Sin permisos para gestionar este departamento'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark as left
        membership.left_at = timezone.now()
        membership.save()
        
        return Response({'message': 'Empleado removido del departamento exitosamente'})


class DepartmentAnalyticsView(APIView):
    """
    Get analytics for a specific department
    GET /api/departments/<id>/analytics/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request, pk):
        try:
            department = Department.objects.get(id=pk)
        except Department.DoesNotExist:
            return Response(
                {'error': 'Departamento no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if not user.is_admin:
            if department.manager != user and not department.employees.filter(
                employee_profile__supervisor=user
            ).exists():
                return Response(
                    {'error': 'Sin permisos para ver analytics de este departamento'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Date range
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # Get department employees
        employees = department.get_all_employees()
        
        # Basic stats
        total_employees = employees.count()
        active_employees = employees.filter(
            devices__last_seen__gte=start_date
        ).distinct().count()
        
        # Stress analytics
        stress_aggregates = StressAggregate.objects.filter(
            employee__in=employees,
            window_start__gte=start_date
        )
        
        avg_stress = stress_aggregates.aggregate(avg=Avg('stress_score'))['avg'] or 0
        high_stress_employees = stress_aggregates.filter(
            stress_score__gte=70
        ).values('employee').distinct().count()
        
        # Alerts
        total_alerts = Alert.objects.filter(
            employee__in=employees,
            created_at__gte=start_date
        ).count()
        
        # Active devices
        active_devices = Device.objects.filter(
            employee__in=employees,
            last_seen__gte=start_date
        ).count()
        
        # Stress distribution
        stress_distribution = {
            'low': stress_aggregates.filter(stress_score__lt=40).count(),
            'medium': stress_aggregates.filter(stress_score__gte=40, stress_score__lt=70).count(),
            'high': stress_aggregates.filter(stress_score__gte=70).count()
        }
        
        # Shift performance
        shift_performance = []
        for shift in department.work_shifts.filter(is_active=True):
            shift_employees = employees.filter(work_shifts=shift)
            shift_aggregates = stress_aggregates.filter(employee__in=shift_employees)
            shift_avg_stress = shift_aggregates.aggregate(avg=Avg('stress_score'))['avg'] or 0
            
            shift_performance.append({
                'shift_name': shift.name,
                'employee_count': shift_employees.count(),
                'avg_stress': round(shift_avg_stress, 2)
            })
        
        # Trends (simplified)
        trends = {
            'stress_trend': 'stable',  # This would be calculated based on historical data
            'alert_trend': 'stable',
            'productivity_trend': 'stable'
        }
        
        data = {
            'department_id': department.id,
            'department_name': department.name,
            'total_employees': total_employees,
            'active_employees': active_employees,
            'avg_stress_level': round(avg_stress, 2),
            'high_stress_employees': high_stress_employees,
            'total_alerts': total_alerts,
            'active_devices': active_devices,
            'stress_distribution': stress_distribution,
            'shift_performance': shift_performance,
            'trends': trends
        }
        
        serializer = DepartmentStatsSerializer(data)
        return Response(serializer.data)


# Work Shift Views
class WorkShiftListCreateView(generics.ListCreateAPIView):
    """
    List all work shifts or create a new shift
    GET/POST /api/workshifts/
    """
    permission_classes = [IsSupervisor]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkShiftCreateSerializer
        return WorkShiftSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = WorkShift.objects.filter(is_active=True)
        
        # Filter by department access
        if not user.is_admin:
            accessible_departments = Department.objects.filter(
                Q(manager=user) | Q(employees__employee_profile__supervisor=user)
            ).distinct()
            queryset = queryset.filter(department__in=accessible_departments)
        
        # Filter by department if specified
        department_id = self.request.query_params.get('department_id')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        return queryset.select_related('department')


class WorkShiftDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a work shift
    GET/PUT/DELETE /api/workshifts/<id>/
    """
    serializer_class = WorkShiftSerializer
    permission_classes = [IsSupervisor]
    
    def get_queryset(self):
        user = self.request.user
        queryset = WorkShift.objects.all()
        
        if not user.is_admin:
            accessible_departments = Department.objects.filter(
                Q(manager=user) | Q(employees__employee_profile__supervisor=user)
            ).distinct()
            queryset = queryset.filter(department__in=accessible_departments)
        
        return queryset.select_related('department')


class WorkShiftEmployeesView(generics.ListAPIView):
    """
    Get employees assigned to a specific work shift
    GET /api/workshifts/<id>/employees/
    """
    serializer_class = ShiftAssignmentSerializer
    permission_classes = [IsSupervisor]
    
    def get_queryset(self):
        shift_id = self.kwargs['pk']
        
        return ShiftAssignment.objects.filter(
            work_shift_id=shift_id,
            is_active=True
        ).select_related('user', 'work_shift')


class WorkShiftAssignEmployeeView(APIView):
    """
    Assign employee to work shift
    POST /api/workshifts/<id>/employees/
    """
    permission_classes = [IsSupervisor]
    
    def post(self, request, pk):
        try:
            work_shift = WorkShift.objects.get(id=pk)
        except WorkShift.DoesNotExist:
            return Response(
                {'error': 'Turno de trabajo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if not user.is_admin and work_shift.department.manager != user:
            return Response(
                {'error': 'Sin permisos para gestionar este turno'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ShiftAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if assignment already exists
        existing = ShiftAssignment.objects.filter(
            user=serializer.validated_data['user'],
            work_shift=work_shift,
            is_active=True
        ).exists()
        
        if existing:
            return Response(
                {'error': 'El empleado ya está asignado a este turno'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        assignment = serializer.save(work_shift=work_shift)
        return Response(
            ShiftAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED
        )