"""
Vistas API para alertas de fatiga y recomendaciones de rutinas.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend

from .models import FatigueAlert, RoutineRecommendation
from .serializers import (
    FatigueAlertListSerializer,
    FatigueAlertDetailSerializer,
    FatigueAlertCreateSerializer,
    FatigueAlertResolveSerializer,
    RoutineRecommendationListSerializer,
    RoutineRecommendationDetailSerializer,
    RoutineRecommendationCreateSerializer,
    RoutineRecommendationApplySerializer,
    AlertStatsSerializer,
    RecommendationStatsSerializer,
)
from apps.users.permissions import IsAdmin, IsAdminOrSupervisor


class FatigueAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar alertas de fatiga.
    
    Permisos:
    - Admin: Todas las alertas
    - Supervisor: Alertas de sus empleados
    - Empleado: Solo sus propias alertas (read-only)
    
    Endpoints:
    - GET /api/alerts/ - Listar alertas
    - POST /api/alerts/ - Crear alerta
    - GET /api/alerts/{id}/ - Ver detalle
    - PUT/PATCH /api/alerts/{id}/ - Actualizar
    - DELETE /api/alerts/{id}/ - Eliminar
    - POST /api/alerts/{id}/resolve/ - Marcar como resuelta
    - POST /api/alerts/{id}/unresolve/ - Reabrir alerta
    - GET /api/alerts/stats/ - Estadísticas
    - GET /api/alerts/my_alerts/ - Alertas del empleado actual
    """
    
    queryset = FatigueAlert.objects.select_related(
        'employee', 'supervisor', 'resolved_by'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['severity', 'is_resolved', 'employee', 'supervisor', 'alert_type']
    search_fields = ['message', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['created_at', 'resolved_at', 'severity', 'fatigue_index', 'timestamp']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return FatigueAlertListSerializer
        elif self.action == 'create':
            return FatigueAlertCreateSerializer
        elif self.action in ['resolve', 'unresolve']:
            return FatigueAlertResolveSerializer
        else:
            return FatigueAlertDetailSerializer
    
    def get_queryset(self):
        """
        Filtrar alertas según el rol del usuario.
        """
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'admin':
            # Admin ve todas las alertas
            pass
        elif user.role == 'supervisor':
            # Supervisor ve alertas de sus empleados
            queryset = queryset.filter(supervisor=user)
        else:  # employee
            # Empleado solo ve sus propias alertas
            queryset = queryset.filter(employee=user)
        
        # Filtros adicionales por query params
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Filtro por últimas N horas
        hours = self.request.query_params.get('hours')
        if hours:
            start_time = timezone.now() - timedelta(hours=int(hours))
            queryset = queryset.filter(created_at__gte=start_time)
        
        return queryset
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'destroy']:
            # Solo Admin y Supervisor pueden crear/eliminar
            return [IsAuthenticated(), IsAdminOrSupervisor()]
        elif self.action in ['update', 'partial_update', 'resolve', 'unresolve']:
            # Solo Admin y Supervisor pueden actualizar/resolver
            return [IsAuthenticated(), IsAdminOrSupervisor()]
        else:
            return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Crear alerta."""
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Marcar alerta como resuelta.
        """
        alert = self.get_object()
        
        if alert.is_resolved:
            return Response(
                {'error': 'La alerta ya está resuelta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.save()
        
        serializer = FatigueAlertDetailSerializer(alert)
        return Response({
            'message': 'Alerta resuelta exitosamente',
            'alert': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def unresolve(self, request, pk=None):
        """
        Reabrir alerta (marcar como no resuelta).
        """
        alert = self.get_object()
        
        if not alert.is_resolved:
            return Response(
                {'error': 'La alerta no está resuelta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert.is_resolved = False
        alert.resolved_at = None
        alert.resolved_by = None
        alert.save()
        
        serializer = FatigueAlertDetailSerializer(alert)
        return Response({
            'message': 'Alerta reabierta exitosamente',
            'alert': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Estadísticas de alertas.
        """
        queryset = self.get_queryset()
        
        # Rango de fechas
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=start_date)
        
        # Estadísticas básicas
        total = queryset.count()
        resolved = queryset.filter(is_resolved=True).count()
        unresolved = queryset.filter(is_resolved=False).count()
        
        # Por severidad
        by_severity = {
            'low': queryset.filter(severity='low').count(),
            'medium': queryset.filter(severity='medium').count(),
            'high': queryset.filter(severity='high').count(),
            'critical': queryset.filter(severity='critical').count(),
        }
        
        # Tiempo promedio de resolución
        resolved_alerts = queryset.filter(is_resolved=True, resolved_at__isnull=False)
        if resolved_alerts.exists():
            total_time = sum([
                (alert.resolved_at - alert.created_at).total_seconds() / 60
                for alert in resolved_alerts
            ])
            avg_resolution_time = total_time / resolved_alerts.count()
        else:
            avg_resolution_time = None
        
        stats = {
            'total': total,
            'resolved': resolved,
            'unresolved': unresolved,
            'by_severity': by_severity,
            'avg_resolution_time_minutes': round(avg_resolution_time, 2) if avg_resolution_time else None
        }
        
        serializer = AlertStatsSerializer(data=stats)
        serializer.is_valid()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_alerts(self, request):
        """
        Obtener alertas del empleado actual.
        """
        user = request.user
        
        if user.role != 'employee':
            return Response(
                {'error': 'Este endpoint es solo para empleados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        alerts = FatigueAlert.objects.filter(employee=user).order_by('-created_at')
        
        # Filtro de resueltas/no resueltas
        resolved_filter = request.query_params.get('resolved')
        if resolved_filter is not None:
            alerts = alerts.filter(resolved=resolved_filter.lower() == 'true')
        
        page = self.paginate_queryset(alerts)
        if page is not None:
            serializer = FatigueAlertListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = FatigueAlertListSerializer(alerts, many=True)
        return Response(serializer.data)


class RoutineRecommendationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar recomendaciones de rutinas.
    
    Permisos:
    - Admin: Todas las recomendaciones
    - Supervisor: Recomendaciones de sus empleados
    - Empleado: Solo sus propias recomendaciones (read-only)
    
    Endpoints:
    - GET /api/recommendations/ - Listar recomendaciones
    - POST /api/recommendations/ - Crear recomendación
    - GET /api/recommendations/{id}/ - Ver detalle
    - PUT/PATCH /api/recommendations/{id}/ - Actualizar
    - DELETE /api/recommendations/{id}/ - Eliminar
    - POST /api/recommendations/{id}/apply/ - Aplicar recomendación
    - POST /api/recommendations/{id}/reject/ - Rechazar recomendación
    - GET /api/recommendations/stats/ - Estadísticas
    - GET /api/recommendations/my_recommendations/ - Recomendaciones del empleado
    """
    
    queryset = RoutineRecommendation.objects.select_related(
        'employee', 'supervisor'
    ).all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['recommendation_type', 'is_applied', 'priority', 'employee', 'supervisor']
    search_fields = ['description', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['created_at', 'applied_at', 'priority']
    ordering = ['priority', '-created_at']
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return RoutineRecommendationListSerializer
        elif self.action == 'create':
            return RoutineRecommendationCreateSerializer
        elif self.action == 'apply':
            return RoutineRecommendationApplySerializer
        else:
            return RoutineRecommendationDetailSerializer
    
    def get_queryset(self):
        """
        Filtrar recomendaciones según el rol del usuario.
        """
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'admin':
            # Admin ve todas
            pass
        elif user.role == 'supervisor':
            # Supervisor ve recomendaciones de sus empleados
            queryset = queryset.filter(supervisor=user)
        else:  # employee
            # Empleado solo ve sus propias recomendaciones
            queryset = queryset.filter(employee=user)
        
        # Filtros adicionales
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Filtro de pendientes (no aplicadas)
        pending = self.request.query_params.get('pending')
        if pending and pending.lower() == 'true':
            queryset = queryset.filter(is_applied=False)
        
        return queryset
    
    def get_permissions(self):
        """Permisos según la acción."""
        if self.action in ['create', 'destroy']:
            return [IsAuthenticated(), IsAdminOrSupervisor()]
        elif self.action in ['update', 'partial_update', 'apply', 'reject']:
            return [IsAuthenticated(), IsAdminOrSupervisor()]
        else:
            return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """
        Aplicar recomendación.
        """
        recommendation = self.get_object()
        
        if recommendation.is_applied:
            return Response(
                {'error': 'La recomendación ya fue aplicada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recommendation.is_applied = True
        recommendation.applied_at = timezone.now()
        recommendation.save()
        
        serializer = RoutineRecommendationDetailSerializer(recommendation)
        return Response({
            'message': 'Recomendación aplicada exitosamente',
            'recommendation': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Estadísticas de recomendaciones.
        """
        queryset = self.get_queryset()
        
        # Rango de fechas
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=start_date)
        
        # Estadísticas básicas
        total = queryset.count()
        applied = queryset.filter(is_applied=True).count()
        pending = queryset.filter(is_applied=False).count()
        
        # Por tipo
        by_type = {
            'break': queryset.filter(recommendation_type='break').count(),
            'task_redistribution': queryset.filter(recommendation_type='task_redistribution').count(),
            'shift_rotation': queryset.filter(recommendation_type='shift_rotation').count(),
        }
        
        # Tiempo promedio de aplicación
        applied_recs = queryset.filter(is_applied=True, applied_at__isnull=False)
        if applied_recs.exists():
            total_time = sum([
                (rec.applied_at - rec.created_at).total_seconds() / 3600
                for rec in applied_recs
            ])
            avg_application_time = total_time / applied_recs.count()
        else:
            avg_application_time = None
        
        stats = {
            'total': total,
            'applied': applied,
            'rejected': 0,  # No longer supported
            'pending': pending,
            'by_type': by_type,
            'avg_application_time_hours': round(avg_application_time, 2) if avg_application_time else None
        }
        
        serializer = RecommendationStatsSerializer(data=stats)
        serializer.is_valid()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_recommendations(self, request):
        """
        Obtener recomendaciones del empleado actual.
        """
        user = request.user
        
        if user.role != 'employee':
            return Response(
                {'error': 'Este endpoint es solo para empleados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        recommendations = RoutineRecommendation.objects.filter(employee=user).order_by('-created_at')
        
        # Filtro de pendientes
        pending_filter = request.query_params.get('pending')
        if pending_filter and pending_filter.lower() == 'true':
            recommendations = recommendations.filter(is_applied=False)
        
        page = self.paginate_queryset(recommendations)
        if page is not None:
            serializer = RoutineRecommendationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = RoutineRecommendationListSerializer(recommendations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generate_all(self, request):
        """
        Genera recomendaciones automáticas para el supervisor actual o todos.
        Solo disponible para supervisores y admins.
        
        POST /api/recommendations/generate_all/
        Body (opcional):
        {
            "all_supervisors": true  // Solo para admins
        }
        """
        from .recommendation_service import RecommendationService
        
        user = request.user
        
        # Solo supervisores y admins pueden generar recomendaciones
        if user.role not in ['supervisor', 'admin']:
            return Response(
                {'error': 'No tienes permisos para generar recomendaciones'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Determinar para quién generar
        all_supervisors = request.data.get('all_supervisors', False)
        
        if all_supervisors and user.role != 'admin':
            return Response(
                {'error': 'Solo admins pueden generar recomendaciones para todos los supervisores'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generar recomendaciones
        if all_supervisors:
            service = RecommendationService()
        else:
            service = RecommendationService(supervisor=user if user.role == 'supervisor' else None)
        
        try:
            result = service.generate_all_recommendations()
            return Response({
                'success': True,
                'message': 'Recomendaciones generadas exitosamente',
                'result': result
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Error al generar recomendaciones: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def analyze_patterns(self, request, pk=None):
        """
        Analiza patrones de fatiga para un empleado específico.
        Solo disponible para supervisores del empleado y admins.
        
        GET /api/recommendations/{id}/analyze_patterns/
        Query params:
        - days: Días a analizar (default: 7)
        """
        from .pattern_analyzer import PatternAnalyzer
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        try:
            recommendation = self.get_object()
            
            if not recommendation.employee:
                return Response(
                    {'error': 'Esta recomendación no está asociada a un empleado específico'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            employee = recommendation.employee
            
            # Verificar permisos
            user = request.user
            if user.role == 'employee' and user != employee:
                return Response(
                    {'error': 'No tienes permisos para ver patrones de otros empleados'},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif user.role == 'supervisor' and employee.supervisor != user:
                return Response(
                    {'error': 'Este empleado no está bajo tu supervisión'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Analizar patrones
            days = int(request.query_params.get('days', 7))
            analyzer = PatternAnalyzer(employee, days=days)
            patterns = analyzer.analyze_all_patterns()
            
            if not patterns:
                return Response(
                    {'error': 'Datos insuficientes para análisis de patrones'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(patterns)
            
        except Exception as e:
            return Response(
                {'error': f'Error al analizar patrones: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
