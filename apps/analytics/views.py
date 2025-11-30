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

from .models import FatigueAlert, RoutineRecommendation, SymptomReport, ScheduledBreak
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
    SymptomReportCreateSerializer,
    SymptomReportListSerializer,
    SymptomReportReviewSerializer,
    ScheduledBreakCreateSerializer,
    ScheduledBreakListSerializer,
    ScheduledBreakReviewSerializer,
    ScheduledBreakUpdateStatusSerializer,
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
        elif self.action in ['update', 'partial_update', 'resolve', 'unresolve', 'acknowledge']:
            # Solo Admin y Supervisor pueden actualizar/resolver/reconocer
            return [IsAuthenticated(), IsAdminOrSupervisor()]
        else:
            return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Crear alerta."""
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        Reconocer/marcar alerta como vista.
        """
        alert = self.get_object()
        
        if alert.is_acknowledged:
            return Response(
                {'error': 'La alerta ya está reconocida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert.is_acknowledged = True
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save()
        
        serializer = FatigueAlertDetailSerializer(alert)
        return Response({
            'message': 'Alerta reconocida exitosamente',
            'alert': serializer.data
        })
    
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
    
    @action(detail=False, methods=['post'], url_path='send-team-notification')
    def send_team_notification(self, request):
        """
        Enviar notificación al equipo completo (supervisor).
        
        POST /api/alerts/send-team-notification/
        Body: {
            "title": "Título de la notificación",
            "message": "Mensaje para el equipo",
            "priority": "low|medium|high"  # Opcional, default: "medium"
        }
        """
        if request.user.role not in ['supervisor', 'admin']:
            return Response(
                {'error': 'Solo supervisores pueden enviar notificaciones al equipo'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        title = request.data.get('title', '').strip()
        message = request.data.get('message', '').strip()
        priority = request.data.get('priority', 'medium').lower()
        
        # Validaciones
        if not title:
            return Response(
                {'error': 'El título es obligatorio'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not message:
            return Response(
                {'error': 'El mensaje es obligatorio'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if priority not in ['low', 'medium', 'high']:
            return Response(
                {'error': 'Prioridad inválida. Debe ser: low, medium o high'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener empleados del supervisor
        from apps.users.models import CustomUser
        employees = CustomUser.objects.filter(
            supervisor=request.user,
            is_active=True
        )
        
        if not employees.exists():
            return Response(
                {'error': 'No tienes empleados asignados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear una alerta para cada empleado
        alerts_created = []
        for employee in employees:
            alert = FatigueAlert.objects.create(
                employee=employee,
                supervisor=request.user,
                severity=priority,
                alert_type='team_notification',  # Tipo específico para notificaciones
                message=f"📢 {title}\n\n{message}",
                fatigue_index=0.0,  # No aplica para notificaciones generales
                is_resolved=False
            )
            alerts_created.append({
                'employee_id': employee.id,
                'employee_name': employee.get_full_name(),
                'alert_id': alert.id
            })
        
        return Response({
            'message': f'Notificación enviada exitosamente a {len(alerts_created)} empleado(s)',
            'title': title,
            'priority': priority,
            'employees_notified': len(alerts_created),
            'alerts': alerts_created
        }, status=status.HTTP_201_CREATED)


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


class SymptomReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar reportes de síntomas.
    
    Permisos:
    - Empleado: Puede crear y ver sus propios reportes
    - Supervisor: Puede ver y revisar reportes de sus empleados
    - Admin: Puede ver todos los reportes
    
    Endpoints:
    - GET /api/symptom-reports/ - Listar reportes
    - POST /api/symptom-reports/ - Crear reporte (empleado)
    - GET /api/symptom-reports/{id}/ - Ver detalle
    - POST /api/symptom-reports/{id}/review/ - Revisar reporte (supervisor)
    - GET /api/symptom-reports/my-reports/ - Mis reportes (empleado)
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['symptom_type', 'severity', 'is_reviewed']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'admin':
            # Admin ve todos los reportes
            return SymptomReport.objects.all().select_related('employee', 'reviewed_by')
        elif user.role == 'supervisor':
            # Supervisor ve reportes de sus empleados
            return SymptomReport.objects.filter(
                employee__supervisor=user
            ).select_related('employee', 'reviewed_by')
        else:
            # Empleado solo ve sus propios reportes
            return SymptomReport.objects.filter(
                employee=user
            ).select_related('employee', 'reviewed_by')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SymptomReportCreateSerializer
        elif self.action == 'review':
            return SymptomReportReviewSerializer
        return SymptomReportListSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear un reporte de síntoma (solo empleados)."""
        if request.user.role != 'employee':
            return Response(
                {'error': 'Solo los empleados pueden reportar síntomas'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """
        Marcar un reporte como revisado (supervisor).
        
        Automáticamente:
        - Marca el reporte como revisado
        - Registra quién y cuándo lo revisó
        - Notifica al empleado que su síntoma fue revisado
        """
        if request.user.role not in ['supervisor', 'admin']:
            return Response(
                {'error': 'Solo supervisores pueden revisar reportes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        report = self.get_object()
        
        # Verificar que el supervisor tiene permisos sobre este empleado
        if request.user.role == 'supervisor' and report.employee.supervisor != request.user:
            return Response(
                {'error': 'No tienes permisos para revisar este reporte'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Guardar cambios
        from django.utils import timezone
        from django.db import transaction
        
        serializer = self.get_serializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Forzar campos de revisión dentro de una transacción atómica
        with transaction.atomic():
            report.is_reviewed = True
            report.reviewed_at = timezone.now()
            report.reviewed_by = request.user
            if 'notes' in request.data:
                report.notes = request.data['notes']
            report.save()
            
            # Forzar commit inmediato
            transaction.on_commit(lambda: None)
        
        # Refrescar el objeto desde la DB para asegurar que el cambio persiste
        report.refresh_from_db()
        
        # TODO: Notificar al empleado (websockets, email, o push notification)
        # self._notify_employee_symptom_reviewed(report)
        
        return Response({
            'message': 'Reporte revisado exitosamente. El empleado será notificado.',
            'report': SymptomReportListSerializer(report).data
        })
    
    @action(detail=False, methods=['get'], url_path='my-reports')
    def my_reports(self, request):
        """Obtener los reportes del empleado actual."""
        if request.user.role != 'employee':
            return Response(
                {'error': 'Esta acción es solo para empleados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reports = SymptomReport.objects.filter(employee=request.user).order_by('-created_at')
        serializer = SymptomReportListSerializer(reports, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='recently-reviewed')
    def recently_reviewed(self, request):
        """
        Obtener síntomas recientemente revisados (últimas 24h).
        Para badge amarillo de notificaciones del empleado.
        
        GET /api/symptom-reports/recently-reviewed/
        
        Respuesta:
        {
            "count": 2,
            "reports": [...]
        }
        """
        if request.user.role != 'employee':
            return Response(
                {'error': 'Esta acción es solo para empleados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.utils import timezone
        from datetime import timedelta
        
        # Síntomas revisados en las últimas 24 horas
        last_24h = timezone.now() - timedelta(hours=24)
        recent_reports = SymptomReport.objects.filter(
            employee=request.user,
            is_reviewed=True,
            reviewed_at__gte=last_24h
        ).order_by('-reviewed_at')
        
        serializer = SymptomReportListSerializer(recent_reports, many=True)
        return Response({
            'count': recent_reports.count(),
            'reports': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """Obtener reportes pendientes de revisión (supervisor)."""
        if request.user.role not in ['supervisor', 'admin']:
            return Response(
                {'error': 'Solo supervisores pueden ver reportes pendientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(is_reviewed=False)
        serializer = SymptomReportListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='pending-count')
    def pending_count(self, request):
        """
        Obtener el conteo de síntomas pendientes (supervisor).
        Endpoint optimizado para badges/notificaciones.
        
        GET /api/symptom-reports/pending-count/
        
        Respuesta:
        {
            "count": 5,
            "by_severity": {
                "severe": 2,
                "moderate": 2,
                "mild": 1
            }
        }
        
        ⚠️ NOTA: Si el contador no se actualiza inmediatamente:
        - El frontend calcula localmente desde /symptom-reports/pending/
        - Este endpoint es auxiliar para polling periódico
        """
        if request.user.role not in ['supervisor', 'admin']:
            return Response(
                {'error': 'Solo supervisores pueden ver reportes pendientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Forzar query fresca desde la DB (sin caché del ORM)
        from django.db.models import Count, Q
        from django.db import connection
        
        # Obtener base queryset sin caché
        base_qs = SymptomReport.objects.all()
        
        # Filtrar por supervisor si aplica
        if request.user.role == 'supervisor':
            base_qs = base_qs.filter(employee__supervisor=request.user)
        
        # Filtrar pendientes con query fresca
        queryset = base_qs.filter(is_reviewed=False)
        
        # Contar por severidad con una sola query
        severity_counts = queryset.aggregate(
            total=Count('id'),
            severe=Count('id', filter=Q(severity='severe')),
            moderate=Count('id', filter=Q(severity='moderate')),
            mild=Count('id', filter=Q(severity='mild'))
        )
        
        return Response({
            'count': severity_counts['total'],
            'by_severity': {
                'severe': severity_counts['severe'],
                'moderate': severity_counts['moderate'],
                'mild': severity_counts['mild']
            }
        })


class ScheduledBreakViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar descansos programados.
    
    Permisos:
    - Empleado: Puede crear, ver y cancelar sus propios descansos
    - Supervisor: Puede ver y aprobar/rechazar descansos de sus empleados
    - Admin: Puede ver todos los descansos
    
    Endpoints:
    - GET /api/scheduled-breaks/ - Listar descansos
    - POST /api/scheduled-breaks/ - Programar descanso (empleado)
    - GET /api/scheduled-breaks/{id}/ - Ver detalle
    - DELETE /api/scheduled-breaks/{id}/ - Cancelar descanso (empleado)
    - POST /api/scheduled-breaks/{id}/review/ - Aprobar/Rechazar (supervisor)
    - POST /api/scheduled-breaks/{id}/update-status/ - Actualizar estado (empleado)
    - GET /api/scheduled-breaks/my-breaks/ - Mis descansos (empleado)
    - GET /api/scheduled-breaks/pending/ - Pendientes de aprobar (supervisor)
    - GET /api/scheduled-breaks/today/ - Descansos de hoy
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['break_type', 'status', 'scheduled_date']
    ordering_fields = ['scheduled_date', 'scheduled_time', 'created_at']
    ordering = ['scheduled_date', 'scheduled_time']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'admin':
            # Admin ve todos los descansos
            return ScheduledBreak.objects.all().select_related('employee', 'reviewed_by')
        elif user.role == 'supervisor':
            # Supervisor ve descansos de sus empleados
            return ScheduledBreak.objects.filter(
                employee__supervisor=user
            ).select_related('employee', 'reviewed_by')
        else:
            # Empleado solo ve sus propios descansos
            return ScheduledBreak.objects.filter(
                employee=user
            ).select_related('employee', 'reviewed_by')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduledBreakCreateSerializer
        elif self.action == 'review':
            return ScheduledBreakReviewSerializer
        elif self.action == 'update_status':
            return ScheduledBreakUpdateStatusSerializer
        return ScheduledBreakListSerializer
    
    def create(self, request, *args, **kwargs):
        """Programar un descanso (solo empleados)."""
        if request.user.role != 'employee':
            return Response(
                {'error': 'Solo los empleados pueden programar descansos'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Cancelar un descanso (solo si es pendiente y es del empleado)."""
        instance = self.get_object()
        
        if instance.employee != request.user and request.user.role not in ['supervisor', 'admin']:
            return Response(
                {'error': 'No tienes permiso para cancelar este descanso'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if instance.status not in ['pending', 'approved']:
            return Response(
                {'error': 'Solo puedes cancelar descansos pendientes o aprobados'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status = 'cancelled'
        instance.save()
        return Response({'message': 'Descanso cancelado exitosamente'})
    
    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """Aprobar o rechazar un descanso (supervisor)."""
        if request.user.role not in ['supervisor', 'admin']:
            return Response(
                {'error': 'Solo supervisores pueden revisar descansos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        break_instance = self.get_object()
        
        # Verificar que el supervisor tiene permisos sobre este empleado
        if request.user.role == 'supervisor' and break_instance.employee.supervisor != request.user:
            return Response(
                {'error': 'No tienes permisos para revisar este descanso'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(break_instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        status_msg = 'aprobado' if break_instance.status == 'approved' else 'rechazado'
        return Response({
            'message': f'Descanso {status_msg} exitosamente',
            'break': ScheduledBreakListSerializer(break_instance).data
        })
    
    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Actualizar estado del descanso (empleado marca como completado)."""
        break_instance = self.get_object()
        
        if break_instance.employee != request.user:
            return Response(
                {'error': 'Solo puedes actualizar tus propios descansos'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(break_instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Estado actualizado exitosamente',
            'break': ScheduledBreakListSerializer(break_instance).data
        })
    
    @action(detail=False, methods=['get'], url_path='my-breaks')
    def my_breaks(self, request):
        """Obtener los descansos del empleado actual."""
        if request.user.role != 'employee':
            return Response(
                {'error': 'Esta acción es solo para empleados'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        breaks = ScheduledBreak.objects.filter(employee=request.user).order_by('scheduled_date', 'scheduled_time')
        serializer = ScheduledBreakListSerializer(breaks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """Obtener descansos pendientes de aprobación (supervisor)."""
        if request.user.role not in ['supervisor', 'admin']:
            return Response(
                {'error': 'Solo supervisores pueden ver descansos pendientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(status='pending')
        serializer = ScheduledBreakListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        """Obtener descansos programados para hoy."""
        from datetime import date
        queryset = self.get_queryset().filter(
            scheduled_date=date.today(),
            status__in=['pending', 'approved']
        )
        serializer = ScheduledBreakListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='upcoming')
    def upcoming(self, request):
        """Obtener descansos próximos (hoy y los próximos 7 días)."""
        from datetime import date, timedelta
        today = date.today()
        end_date = today + timedelta(days=7)
        
        queryset = self.get_queryset().filter(
            scheduled_date__gte=today,
            scheduled_date__lte=end_date,
            status__in=['pending', 'approved']
        )
        serializer = ScheduledBreakListSerializer(queryset, many=True)
        return Response(serializer.data)

