# apps/users/admin_views.py
"""
ViewSet para el panel de administración.
Permite gestionar supervisores, ver estadísticas del sistema y logs de actividad.
Solo accesible para usuarios con rol 'admin'.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
import csv

from apps.users.permissions import IsAdmin
from apps.users.admin_serializers import (
    SupervisorListSerializer,
    SupervisorDetailSerializer,
    SupervisorCreateSerializer,
    SupervisorUpdateSerializer,
    SystemStatsSerializer,
    ActivityLogSerializer
)
from apps.users.models import ActivityLog
from apps.devices.models import Device
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation

User = get_user_model()


class AdminViewSet(viewsets.ViewSet):
    """
    ViewSet para funcionalidades del panel de administración.
    
    Endpoints:
    - GET /api/admin/supervisors/ - Lista de supervisores
    - POST /api/admin/supervisors/ - Crear supervisor
    - GET /api/admin/supervisors/{id}/ - Detalle de supervisor
    - PUT /api/admin/supervisors/{id}/ - Actualizar supervisor
    - DELETE /api/admin/supervisors/{id}/ - Eliminar supervisor
    - GET /api/admin/dashboard/ - Dashboard del admin
    - GET /api/admin/system-stats/ - Estadísticas del sistema
    - GET /api/admin/activity-logs/ - Logs de actividad
    """
    
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['get'], url_path='supervisors')
    def list_supervisors(self, request):
        """
        Lista todos los supervisores.
        Admin puede ver supervisores de todas las empresas.
        
        Query params:
        - company: Filtrar por empresa específica
        - is_active: Filtrar por estado (true/false)
        - search: Buscar por nombre o email
        """
        supervisors = User.objects.filter(
            role='supervisor'
        ).select_related('company').prefetch_related('employees')
        
        # Filtro por empresa
        company_id = request.query_params.get('company')
        if company_id:
            supervisors = supervisors.filter(company_id=company_id)
        
        # Filtros
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            supervisors = supervisors.filter(is_active=is_active_bool)
        
        search = request.query_params.get('search')
        if search:
            supervisors = supervisors.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        serializer = SupervisorListSerializer(supervisors, many=True)
        
        # Registrar actividad
        ActivityLog.log_action(
            user=request.user,
            action='other',
            resource_type='supervisor',
            details={'action_type': 'list_supervisors'},
            request=request
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='supervisors')
    def create_supervisor(self, request):
        """
        Crea un nuevo supervisor.
        
        Body:
        {
            "email": "supervisor@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "first_name": "Juan",
            "last_name": "Pérez",
            "is_active": true
        }
        """
        serializer = SupervisorCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            supervisor = serializer.save()
            
            # Registrar actividad
            ActivityLog.log_action(
                user=request.user,
                action='create',
                resource_type='supervisor',
                resource_id=supervisor.id,
                details={
                    'email': supervisor.email,
                    'name': supervisor.get_full_name()
                },
                request=request
            )
            
            # Retornar datos del supervisor creado
            response_serializer = SupervisorDetailSerializer(supervisor)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='supervisors')
    def retrieve_supervisor(self, request, pk=None):
        """
        Obtiene detalles de un supervisor específico.
        """
        try:
            supervisor = User.objects.get(
                id=pk,
                role='supervisor',
                admin=request.user
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'Supervisor no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SupervisorDetailSerializer(supervisor)
        return Response(serializer.data)
    
    @action(detail=True, methods=['put', 'patch'], url_path='supervisors')
    def update_supervisor(self, request, pk=None):
        """
        Actualiza información de un supervisor.
        
        Body:
        {
            "first_name": "Juan",
            "last_name": "Pérez",
            "is_active": true
        }
        """
        try:
            supervisor = User.objects.get(
                id=pk,
                role='supervisor',
                admin=request.user
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'Supervisor no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SupervisorUpdateSerializer(
            supervisor,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        
        if serializer.is_valid():
            updated_supervisor = serializer.save()
            
            # Registrar actividad
            ActivityLog.log_action(
                user=request.user,
                action='update',
                resource_type='supervisor',
                resource_id=supervisor.id,
                details={
                    'email': supervisor.email,
                    'changes': request.data
                },
                request=request
            )
            
            response_serializer = SupervisorDetailSerializer(updated_supervisor)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='supervisors')
    def delete_supervisor(self, request, pk=None):
        """
        Elimina (desactiva) un supervisor.
        No se eliminan registros, solo se marca como inactivo.
        """
        try:
            supervisor = User.objects.get(
                id=pk,
                role='supervisor',
                admin=request.user
            )
        except User.DoesNotExist:
            return Response(
                {'detail': 'Supervisor no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si tiene empleados activos
        active_employees_count = supervisor.employees.filter(is_active=True).count()
        if active_employees_count > 0:
            return Response(
                {
                    'detail': f'No se puede eliminar el supervisor. Tiene {active_employees_count} empleados activos asignados.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Desactivar en lugar de eliminar
        supervisor.is_active = False
        supervisor.save()
        
        # Registrar actividad
        ActivityLog.log_action(
            user=request.user,
            action='delete',
            resource_type='supervisor',
            resource_id=supervisor.id,
            details={
                'email': supervisor.email,
                'name': supervisor.get_full_name()
            },
            request=request
        )
        
        return Response(
            {'message': 'Supervisor desactivado exitosamente.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='dashboard')
    def admin_dashboard(self, request):
        """
        Dashboard completo para el administrador.
        Incluye resumen de todos los supervisores y estadísticas generales.
        """
        # Supervisores del admin
        supervisors = User.objects.filter(
            role='supervisor',
            admin=request.user
        )
        
        supervisor_ids = [s.id for s in supervisors]
        
        # Total de empleados bajo supervisión
        total_employees = User.objects.filter(
            role='employee',
            supervisor_id__in=supervisor_ids
        ).count()
        
        # Total de dispositivos
        total_devices = Device.objects.filter(
            supervisor_id__in=supervisor_ids
        ).count()
        
        # Alertas activas
        active_alerts = FatigueAlert.objects.filter(
            supervisor_id__in=supervisor_ids,
            is_resolved=False
        ).count()
        
        # Recomendaciones pendientes
        pending_recommendations = RoutineRecommendation.objects.filter(
            supervisor_id__in=supervisor_ids,
            is_applied=False
        ).count()
        
        # Supervisores con estadísticas
        supervisor_stats = []
        for supervisor in supervisors:
            employees_count = supervisor.employees.count()
            alerts_count = FatigueAlert.objects.filter(
                supervisor=supervisor,
                is_resolved=False
            ).count()
            
            supervisor_stats.append({
                'id': supervisor.id,
                'email': supervisor.email,
                'full_name': supervisor.get_full_name(),
                'is_active': supervisor.is_active,
                'employees_count': employees_count,
                'active_alerts_count': alerts_count
            })
        
        # Actividad reciente
        recent_logs = ActivityLog.objects.filter(
            user__in=supervisors
        ).order_by('-timestamp')[:10]
        
        recent_activity = [
            {
                'timestamp': log.timestamp,
                'user': log.user.get_full_name() if log.user else 'Sistema',
                'action': log.get_action_display(),
                'resource': log.get_resource_type_display(),
                'details': log.details
            }
            for log in recent_logs
        ]
        
        dashboard_data = {
            'summary': {
                'total_supervisors': supervisors.count(),
                'active_supervisors': supervisors.filter(is_active=True).count(),
                'total_employees': total_employees,
                'total_devices': total_devices,
                'active_alerts': active_alerts,
                'pending_recommendations': pending_recommendations
            },
            'supervisors': supervisor_stats,
            'recent_activity': recent_activity
        }
        
        # Registrar actividad
        ActivityLog.log_action(
            user=request.user,
            action='other',
            resource_type='system',
            details={'action_type': 'view_dashboard'},
            request=request
        )
        
        return Response(dashboard_data)
    
    @action(detail=False, methods=['get'], url_path='system-stats')
    def system_stats(self, request):
        """
        Estadísticas completas del sistema.
        
        Query params:
        - period: 'day', 'week', 'month' (default: 'week')
        """
        period = request.query_params.get('period', 'week')
        
        # Calcular fecha de inicio según período
        now = timezone.now()
        if period == 'day':
            start_date = now - timedelta(days=1)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        else:  # week
            start_date = now - timedelta(days=7)
        
        # Supervisores del admin
        supervisors = User.objects.filter(
            role='supervisor',
            admin=request.user
        )
        supervisor_ids = [s.id for s in supervisors]
        
        # Empleados bajo supervisión
        employees = User.objects.filter(
            role='employee',
            supervisor_id__in=supervisor_ids
        )
        employee_ids = [e.id for e in employees]
        
        # Estadísticas de usuarios
        user_stats = {
            'supervisors': {
                'total': supervisors.count(),
                'active': supervisors.filter(is_active=True).count(),
                'inactive': supervisors.filter(is_active=False).count()
            },
            'employees': {
                'total': employees.count(),
                'active': employees.filter(is_active=True).count(),
                'inactive': employees.filter(is_active=False).count(),
                'with_devices': Device.objects.filter(
                    employee_id__in=employee_ids,
                    is_active=True
                ).count()
            }
        }
        
        # Estadísticas de dispositivos
        devices = Device.objects.filter(supervisor_id__in=supervisor_ids)
        device_stats = {
            'total': devices.count(),
            'active': devices.filter(is_active=True).count(),
            'inactive': devices.filter(is_active=False).count(),
            'connected_last_24h': devices.filter(
                last_connection__gte=now - timedelta(hours=24)
            ).count()
        }
        
        # Estadísticas de alertas
        alerts = FatigueAlert.objects.filter(supervisor_id__in=supervisor_ids)
        alerts_period = alerts.filter(timestamp__gte=start_date)
        
        alert_stats = {
            'total_all_time': alerts.count(),
            'total_period': alerts_period.count(),
            'active': alerts.filter(is_resolved=False).count(),
            'resolved': alerts.filter(is_resolved=True).count(),
            'by_severity': {
                'low': alerts_period.filter(severity='low').count(),
                'medium': alerts_period.filter(severity='medium').count(),
                'high': alerts_period.filter(severity='high').count(),
                'critical': alerts_period.filter(severity='critical').count()
            }
        }
        
        # Estadísticas de recomendaciones
        recommendations = RoutineRecommendation.objects.filter(
            supervisor_id__in=supervisor_ids
        )
        recommendations_period = recommendations.filter(created_at__gte=start_date)
        
        recommendation_stats = {
            'total_all_time': recommendations.count(),
            'total_period': recommendations_period.count(),
            'applied': recommendations.filter(is_applied=True).count(),
            'pending': recommendations.filter(is_applied=False).count(),
            'by_type': {
                'break': recommendations_period.filter(recommendation_type='break').count(),
                'task_redistribution': recommendations_period.filter(recommendation_type='task_redistribution').count(),
                'shift_rotation': recommendations_period.filter(recommendation_type='shift_rotation').count()
            }
        }
        
        # Estadísticas de métricas procesadas
        metrics_period = ProcessedMetrics.objects.filter(
            employee_id__in=employee_ids,
            window_start__gte=start_date
        )
        
        avg_metrics = metrics_period.aggregate(
            avg_fatigue=Avg('fatigue_index'),
            avg_hr=Avg('hr_avg'),
            avg_spo2=Avg('spo2_avg')
        )
        
        metric_stats = {
            'total_readings_period': metrics_period.count(),
            'averages': {
                'fatigue_index': round(avg_metrics['avg_fatigue'] or 0, 2),
                'heart_rate': round(avg_metrics['avg_hr'] or 0, 2),
                'spo2': round(avg_metrics['avg_spo2'] or 0, 2)
            },
            'high_fatigue_readings': metrics_period.filter(fatigue_index__gte=70).count()
        }
        
        # Actividad del sistema
        activity_stats = {
            'total_logs': ActivityLog.objects.filter(
                user__in=supervisors
            ).count(),
            'logs_period': ActivityLog.objects.filter(
                user__in=supervisors,
                timestamp__gte=start_date
            ).count(),
            'active_users_today': ActivityLog.objects.filter(
                user__in=supervisors,
                timestamp__gte=now - timedelta(days=1)
            ).values('user').distinct().count()
        }
        
        stats_data = {
            'period': period,
            'start_date': start_date,
            'end_date': now,
            'users': user_stats,
            'devices': device_stats,
            'alerts': alert_stats,
            'recommendations': recommendation_stats,
            'metrics': metric_stats,
            'activity': activity_stats
        }
        
        serializer = SystemStatsSerializer(stats_data)
        
        # Registrar actividad
        ActivityLog.log_action(
            user=request.user,
            action='other',
            resource_type='system',
            details={'action_type': 'view_system_stats', 'period': period},
            request=request
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='activity-logs')
    def activity_logs(self, request):
        """
        Logs de actividad del sistema.
        
        Query params:
        - action: Filtrar por tipo de acción
        - resource_type: Filtrar por tipo de recurso
        - user_id: Filtrar por usuario
        - days: Últimos N días (default: 7)
        - limit: Límite de resultados (default: 100)
        """
        # Supervisores del admin
        supervisors = User.objects.filter(
            role='supervisor',
            admin=request.user
        )
        
        # Logs de los supervisores y del admin
        logs = ActivityLog.objects.filter(
            Q(user__in=supervisors) | Q(user=request.user)
        )
        
        # Filtros
        action = request.query_params.get('action')
        if action:
            logs = logs.filter(action=action)
        
        resource_type = request.query_params.get('resource_type')
        if resource_type:
            logs = logs.filter(resource_type=resource_type)
        
        user_id = request.query_params.get('user_id')
        if user_id:
            logs = logs.filter(user_id=user_id)
        
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        logs = logs.filter(timestamp__gte=start_date)
        
        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]
        
        serializer = ActivityLogSerializer(logs, many=True)
        
        return Response({
            'count': logs.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='export-my-data')
    def export_my_data(self, request):
        """
        Exporta los datos personales del administrador actual en formato CSV.
        
        Endpoint: GET /api/admin/export-my-data/
        
        Retorna un archivo CSV descargable con:
        - Información personal (nombre, email, rol, etc.)
        - Fecha de creación de cuenta
        - Estado de la cuenta
        - Información de contacto
        - Compañía asociada (si aplica)
        
        Seguridad:
        - Solo usuarios autenticados con rol 'admin'
        - Solo puede exportar sus propios datos
        - Se registra la acción en el log de actividad
        """
        user = request.user
        
        # Crear respuesta HTTP con tipo CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="mis_datos_{user.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Agregar BOM para compatibilidad con Excel en Windows
        response.write('\ufeff')
        
        # Crear escritor CSV
        writer = csv.writer(response)
        
        # Encabezado del archivo
        writer.writerow(['Campo', 'Valor'])
        writer.writerow([])  # Línea en blanco
        
        # Información personal
        writer.writerow(['=== INFORMACIÓN PERSONAL ===', ''])
        writer.writerow(['ID de Usuario', user.id])
        writer.writerow(['Nombre', user.first_name or 'N/A'])
        writer.writerow(['Apellido', user.last_name or 'N/A'])
        writer.writerow(['Nombre Completo', user.get_full_name() or 'N/A'])
        writer.writerow(['Correo Electrónico', user.email])
        writer.writerow(['Rol', user.get_role_display()])
        writer.writerow([])  # Línea en blanco
        
        # Información de contacto
        writer.writerow(['=== INFORMACIÓN DE CONTACTO ===', ''])
        writer.writerow(['Teléfono', user.phone or 'N/A'])
        writer.writerow(['Departamento', user.department or 'N/A'])
        writer.writerow(['Posición', user.position or 'N/A'])
        writer.writerow([])  # Línea en blanco
        
        # Información de cuenta
        writer.writerow(['=== INFORMACIÓN DE CUENTA ===', ''])
        writer.writerow(['Estado de Cuenta', 'Activa' if user.is_active else 'Inactiva'])
        writer.writerow(['Es Staff', 'Sí' if user.is_staff else 'No'])
        writer.writerow(['Es Superusuario', 'Sí' if user.is_superuser else 'No'])
        writer.writerow(['Fecha de Creación', user.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'created_at') and user.created_at else 'N/A'])
        writer.writerow(['Último Inicio de Sesión', user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Nunca'])
        writer.writerow(['Última Actualización', user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'updated_at') and user.updated_at else 'N/A'])
        writer.writerow([])  # Línea en blanco
        
        # Información organizacional
        writer.writerow(['=== INFORMACIÓN ORGANIZACIONAL ===', ''])
        if hasattr(user, 'company') and user.company:
            writer.writerow(['Compañía', user.company.name])
            writer.writerow(['Email de Compañía', user.company.contact_email])
        else:
            writer.writerow(['Compañía', 'N/A'])
        writer.writerow([])  # Línea en blanco
        
        # Estadísticas (solo para admins que gestionan empresas)
        writer.writerow(['=== ESTADÍSTICAS ===', ''])
        if user.role == 'admin':
            # Contar supervisores en todas las empresas
            supervisors_count = User.objects.filter(role='supervisor').count()
            active_supervisors_count = User.objects.filter(role='supervisor', is_active=True).count()
            writer.writerow(['Total de Supervisores en el Sistema', supervisors_count])
            writer.writerow(['Supervisores Activos', active_supervisors_count])
            
            # Empleados totales en el sistema
            employees_count = User.objects.filter(role='employee').count()
            active_employees_count = User.objects.filter(role='employee', is_active=True).count()
            writer.writerow(['Total de Empleados en el Sistema', employees_count])
            writer.writerow(['Empleados Activos', active_employees_count])
        elif user.role == 'supervisor':
            # Para supervisores: contar sus empleados
            employees_count = user.employees.count()
            active_employees_count = user.employees.filter(is_active=True).count()
            writer.writerow(['Total de Empleados Asignados', employees_count])
            writer.writerow(['Empleados Activos', active_employees_count])
        else:
            writer.writerow(['Estadísticas', 'No disponible para este rol'])
        writer.writerow([])  # Línea en blanco
        
        # Información de privacidad
        writer.writerow(['=== INFORMACIÓN SOBRE PRIVACIDAD ===', ''])
        writer.writerow(['Generado el', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Nota', 'Este archivo contiene información personal. Manténgalo seguro.'])
        
        # Registrar actividad
        ActivityLog.log_action(
            user=request.user,
            action='other',
            resource_type='user',
            resource_id=user.id,
            details={
                'action_type': 'export_personal_data',
                'format': 'csv'
            },
            request=request
        )
        
        return response
    
    @action(detail=False, methods=['get', 'post'], url_path='admin-users')
    def manage_admin_users(self, request):
        """
        GET: Lista todos los usuarios administradores.
        POST: Crea un nuevo usuario administrador.
        
        Solo accesible para superusuarios.
        """
        # Verificar que sea superusuario
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Solo superusuarios pueden gestionar administradores.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            # Listar administradores
            from apps.users.admin_serializers import AdminUserListSerializer
            
            admins = User.objects.filter(
                role='admin'
            ).order_by('-created_at')
            
            # Filtros
            is_active = request.query_params.get('is_active')
            if is_active is not None:
                is_active_bool = is_active.lower() == 'true'
                admins = admins.filter(is_active=is_active_bool)
            
            search = request.query_params.get('search')
            if search:
                admins = admins.filter(
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(email__icontains=search)
                )
            
            serializer = AdminUserListSerializer(admins, many=True)
            
            # Registrar actividad
            ActivityLog.log_action(
                user=request.user,
                action='other',
                resource_type='admin_user',
                details={'action_type': 'list_admin_users'},
                request=request
            )
            
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Crear administrador
            from apps.users.admin_serializers import AdminUserCreateSerializer, AdminUserDetailSerializer
            
            serializer = AdminUserCreateSerializer(data=request.data)
            
            if serializer.is_valid():
                admin_user = serializer.save()
                
                # Registrar actividad
                ActivityLog.log_action(
                    user=request.user,
                    action='create',
                    resource_type='admin_user',
                    resource_id=admin_user.id,
                    details={
                        'email': admin_user.email,
                        'name': admin_user.get_full_name()
                    },
                    request=request
                )
                
                # Retornar datos del admin creado
                response_serializer = AdminUserDetailSerializer(admin_user)
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'put', 'patch', 'delete'], url_path='admin-users')
    def admin_user_detail(self, request, pk=None):
        """
        GET: Obtiene detalles de un administrador.
        PUT/PATCH: Actualiza información de un administrador.
        DELETE: Elimina un administrador.
        
        Solo accesible para superusuarios.
        """
        # Verificar que sea superusuario
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Solo superusuarios pueden gestionar administradores.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            admin_user = User.objects.get(id=pk, role='admin')
        except User.DoesNotExist:
            return Response(
                {'detail': 'Administrador no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'GET':
            # Obtener detalles
            from apps.users.admin_serializers import AdminUserDetailSerializer
            serializer = AdminUserDetailSerializer(admin_user)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'PATCH']:
            # Actualizar administrador
            from apps.users.admin_serializers import AdminUserUpdateSerializer, AdminUserDetailSerializer
            
            # No permitir que el admin se desactive a sí mismo
            if admin_user.id == request.user.id and 'is_active' in request.data:
                if not request.data['is_active']:
                    return Response(
                        {'detail': 'No puedes desactivarte a ti mismo.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            serializer = AdminUserUpdateSerializer(
                admin_user,
                data=request.data,
                partial=(request.method == 'PATCH')
            )
            
            if serializer.is_valid():
                updated_admin = serializer.save()
                
                # Registrar actividad
                ActivityLog.log_action(
                    user=request.user,
                    action='update',
                    resource_type='admin_user',
                    resource_id=updated_admin.id,
                    details={
                        'updated_fields': list(request.data.keys()),
                        'name': updated_admin.get_full_name()
                    },
                    request=request
                )
                
                # Retornar datos actualizados
                response_serializer = AdminUserDetailSerializer(updated_admin)
                return Response(response_serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Eliminar administrador
            
            # No permitir que el admin se elimine a sí mismo
            if admin_user.id == request.user.id:
                return Response(
                    {'detail': 'No puedes eliminarte a ti mismo.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar que no sea el último superusuario
            if admin_user.is_superuser:
                superuser_count = User.objects.filter(is_superuser=True, is_active=True).count()
                if superuser_count <= 1:
                    return Response(
                        {'detail': 'No puedes eliminar el último superusuario activo.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            admin_email = admin_user.email
            admin_name = admin_user.get_full_name()
            
            # Registrar actividad antes de eliminar
            ActivityLog.log_action(
                user=request.user,
                action='delete',
                resource_type='admin_user',
                resource_id=admin_user.id,
                details={
                    'email': admin_email,
                    'name': admin_name
                },
                request=request
            )
            
            admin_user.delete()
            
            return Response(
                {'detail': f'Administrador {admin_name} eliminado exitosamente.'},
                status=status.HTTP_200_OK
            )
