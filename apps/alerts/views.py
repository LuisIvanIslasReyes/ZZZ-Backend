"""
Alert views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Alert, AlertRule, AlertType, AlertSeverity
from .serializers import (
    AlertSerializer,
    AlertCreateSerializer,
    AlertAcknowledgeSerializer,
    AlertRuleSerializer,
    AlertStatsSerializer
)
from apps.authentication.permissions import IsOwnerOrSupervisor, IsSupervisor

User = get_user_model()


class AlertListCreateView(generics.ListCreateAPIView):
    """
    List all alerts or create a new alert
    GET/POST /api/alerts/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AlertCreateSerializer
        return AlertSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Alert.objects.select_related('employee', 'device', 'acknowledged_by')
        
        # Filter by user role
        if user.is_admin:
            # Admin can see all alerts
            pass
        elif user.is_supervisor:
            # Supervisor can see alerts of supervised employees
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            queryset = queryset.filter(employee__in=supervised_employees)
        else:
            # Employee can only see their own alerts
            queryset = queryset.filter(employee=user)
        
        # Query parameters
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        is_acknowledged = self.request.query_params.get('is_acknowledged')
        if is_acknowledged is not None:
            queryset = queryset.filter(is_acknowledged=is_acknowledged.lower() == 'true')
        
        alert_type = self.request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        return queryset.order_by('-created_at')


class AlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an alert
    GET/PUT/DELETE /api/alerts/<id>/
    """
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Alert.objects.select_related('employee', 'device', 'acknowledged_by')
        
        if user.is_admin:
            return queryset
        elif user.is_supervisor:
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            return queryset.filter(employee__in=supervised_employees)
        else:
            return queryset.filter(employee=user)


class AlertAcknowledgeView(APIView):
    """
    Acknowledge an alert
    PUT /api/alerts/<id>/acknowledge/
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def put(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response(
                {'error': 'Alerta no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        user = request.user
        if not (user.is_admin or user.is_supervisor or alert.employee == user):
            return Response(
                {'error': 'Sin permisos para esta alerta'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if alert.is_acknowledged:
            return Response(
                {'error': 'La alerta ya fue reconocida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AlertAcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Acknowledge the alert
        alert.acknowledge(acknowledged_by=user)
        
        # Add notes to data if provided
        notes = serializer.validated_data.get('notes')
        if notes:
            alert.data = alert.data or {}
            alert.data['acknowledgment_notes'] = notes
            alert.save()
        
        return Response({
            'message': 'Alerta reconocida exitosamente',
            'acknowledged_at': alert.acknowledged_at,
            'acknowledged_by': alert.acknowledged_by.get_full_name()
        })


class AlertResolveView(APIView):
    """
    Resolve an alert
    PUT /api/alerts/<id>/resolve/
    """
    permission_classes = [permissions.IsAuthenticated, IsSupervisor]
    
    def put(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response(
                {'error': 'Alerta no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not alert.is_active:
            return Response(
                {'error': 'La alerta ya fue resuelta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert.resolve()
        
        return Response({
            'message': 'Alerta resuelta exitosamente',
            'resolved_at': alert.resolved_at
        })


class AlertActiveView(generics.ListAPIView):
    """
    List only active alerts
    GET /api/alerts/active/
    """
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Alert.objects.filter(is_active=True).select_related('employee', 'device')
        
        if user.is_admin:
            return queryset
        elif user.is_supervisor:
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            return queryset.filter(employee__in=supervised_employees)
        else:
            return queryset.filter(employee=user)


class EmployeeAlertsView(generics.ListAPIView):
    """
    Get alerts for a specific employee
    GET /api/employees/<employee_id>/alerts/
    """
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        user = self.request.user
        
        # Check permissions
        if not (user.is_admin or user.is_supervisor or str(user.id) == str(employee_id)):
            return Alert.objects.none()
        
        return Alert.objects.filter(employee_id=employee_id).select_related('device')


class AlertStatsView(APIView):
    """
    Get alert statistics
    GET /api/alerts/stats/
    """
    permission_classes = [IsSupervisor]
    
    def get(self, request):
        user = request.user
        
        # Base queryset based on permissions
        if user.is_admin:
            queryset = Alert.objects.all()
        else:
            supervised_employees = User.objects.filter(employee_profile__supervisor=user)
            queryset = Alert.objects.filter(employee__in=supervised_employees)
        
        # Date filter
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=start_date)
        
        # Calculate stats
        total_alerts = queryset.count()
        active_alerts = queryset.filter(is_active=True).count()
        acknowledged_alerts = queryset.filter(is_acknowledged=True).count()
        critical_alerts = queryset.filter(severity=AlertSeverity.CRITICAL).count()
        
        # Alerts by type
        alerts_by_type = dict(
            queryset.values('alert_type').annotate(count=Count('id')).values_list('alert_type', 'count')
        )
        
        # Alerts by severity
        alerts_by_severity = dict(
            queryset.values('severity').annotate(count=Count('id')).values_list('severity', 'count')
        )
        
        stats = {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'acknowledged_alerts': acknowledged_alerts,
            'critical_alerts': critical_alerts,
            'alerts_by_type': alerts_by_type,
            'alerts_by_severity': alerts_by_severity
        }
        
        serializer = AlertStatsSerializer(stats)
        return Response(serializer.data)


# Alert Rules Views
class AlertRuleListCreateView(generics.ListCreateAPIView):
    """
    List all alert rules or create a new rule
    GET/POST /api/alerts/rules/
    """
    serializer_class = AlertRuleSerializer
    permission_classes = [IsSupervisor]
    queryset = AlertRule.objects.all()


class AlertRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an alert rule
    GET/PUT/DELETE /api/alerts/rules/<id>/
    """
    serializer_class = AlertRuleSerializer
    permission_classes = [IsSupervisor]
    queryset = AlertRule.objects.all()