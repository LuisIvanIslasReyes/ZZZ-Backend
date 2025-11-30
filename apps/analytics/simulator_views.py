"""
ViewSet para gestión de simuladores ESP32.
Permite a los administradores iniciar y controlar múltiples simuladores.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from apps.analytics.simulator_models import SimulatorSession
from apps.analytics.simulator_serializers import (
    SimulatorSessionListSerializer,
    SimulatorSessionDetailSerializer,
    SimulatorSessionCreateSerializer,
    SimulatorSessionUpdateConfigSerializer,
    EmployeeForSimulatorSerializer,
    SimulatorStatsSerializer,
)
from apps.analytics.simulator_manager import simulator_manager
from apps.users.models import CustomUser

logger = logging.getLogger(__name__)


class SimulatorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de sesiones de simuladores.
    
    Endpoints:
    - GET /api/simulators/ - Listar todas las sesiones
    - POST /api/simulators/ - Crear y arrancar nuevo simulador
    - GET /api/simulators/{id}/ - Detalle de sesión
    - POST /api/simulators/{id}/stop/ - Detener simulador
    - POST /api/simulators/{id}/update_config/ - Actualizar configuración
    - GET /api/simulators/active/ - Listar sesiones activas
    - GET /api/simulators/available_employees/ - Empleados disponibles
    - POST /api/simulators/stop_all/ - Detener todos los simuladores
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar según rol del usuario."""
        user = self.request.user
        
        if user.role == 'admin':
            # Admin ve todos los simuladores
            return SimulatorSession.objects.all()
        elif user.role == 'supervisor':
            # Supervisor ve simuladores de sus empleados
            return SimulatorSession.objects.filter(
                employee__supervisor=user
            )
        else:
            # Empleado ve solo sus propios simuladores
            return SimulatorSession.objects.filter(employee=user)
    
    def get_serializer_class(self):
        """Seleccionar serializer según acción."""
        if self.action == 'list':
            return SimulatorSessionListSerializer
        elif self.action == 'create':
            return SimulatorSessionCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return SimulatorSessionDetailSerializer
        return SimulatorSessionDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crear y arrancar un nuevo simulador.
        Solo administradores pueden crear simuladores.
        """
        if request.user.role != 'admin':
            return Response(
                {'error': 'Solo administradores pueden iniciar simuladores'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Crear sesión
        session = serializer.save()
        
        # Iniciar simulador en thread separado
        success = simulator_manager.start_simulator(session.id)
        
        if not success:
            session.delete()
            return Response(
                {'error': 'No se pudo iniciar el simulador'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        logger.info(f"✅ Simulador iniciado por {request.user.email} para {session.employee.email}")
        
        return Response(
            SimulatorSessionDetailSerializer(session).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Detener un simulador específico."""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Solo administradores pueden detener simuladores'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session = self.get_object()
        
        # Permitir detener simuladores en 'running' o 'error'
        if session.status not in ['running', 'error']:
            return Response(
                {'error': f'El simulador no se puede detener (estado: {session.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Detener simulador si está en memoria
        was_running = simulator_manager.stop_simulator(session.id)
        
        # Actualizar estado en BD independientemente
        session.status = 'stopped'
        session.stopped_at = timezone.now()
        session.save()
        
        logger.info(f"🛑 Simulador detenido por {request.user.email}: {session.device_id} (estaba en memoria: {was_running})")
        
        return Response(
            SimulatorSessionDetailSerializer(session).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """Reiniciar un simulador que fue detenido."""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Solo administradores pueden reiniciar simuladores'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session = self.get_object()
        
        # Solo se pueden reiniciar simuladores detenidos o con error
        if session.status not in ['stopped', 'error']:
            return Response(
                {'error': f'El simulador no se puede reiniciar (estado actual: {session.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Resetear estado de la sesión
        session.status = 'running'
        session.started_at = timezone.now()
        session.stopped_at = None
        session.error_message = None
        session.messages_sent = 0
        session.save()
        
        # Iniciar simulador en thread separado
        success = simulator_manager.start_simulator(session.id)
        
        if not success:
            session.status = 'error'
            session.error_message = 'No se pudo reiniciar el simulador'
            session.save()
            return Response(
                {'error': 'No se pudo reiniciar el simulador'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        logger.info(f"🔄 Simulador reiniciado por {request.user.email}: {session.device_id}")
        
        return Response(
            SimulatorSessionDetailSerializer(session).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def update_config(self, request, pk=None):
        """Actualizar configuración de un simulador en ejecución."""
        logger.info(f"📥 update_config - Usuario: {request.user.email}, Data recibida: {request.data}")
        
        if request.user.role != 'admin':
            return Response(
                {'error': 'Solo administradores pueden actualizar configuración'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session = self.get_object()
        
        # Permitir actualizar si está en 'running' o 'error' (MQTT no disponible)
        if session.status not in ['running', 'error']:
            logger.warning(f"⚠️  Intento de actualizar simulador no disponible. Estado: {session.status}")
            return Response(
                {'error': f'El simulador no está disponible (estado: {session.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SimulatorSessionUpdateConfigSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"❌ Error de validación: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.is_valid(raise_exception=True)
        
        # Actualizar configuración en tiempo real
        config = serializer.validated_data
        success = simulator_manager.update_simulator_config(session.id, config)
        
        if not success:
            return Response(
                {'error': 'No se pudo actualizar la configuración'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Actualizar en BD
        for key, value in config.items():
            if key == 'fatigue_level':
                session.current_fatigue = value
            elif key == 'activity_mode':
                session.activity_mode = value
            elif key == 'fatigue_rate':
                session.fatigue_rate = value
        
        session.save()
        
        logger.info(f"⚙️  Configuración actualizada por {request.user.email}: {session.device_id}")
        
        return Response(
            SimulatorSessionDetailSerializer(session).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Listar solo sesiones activas con estadísticas en tiempo real."""
        active_sessions = self.get_queryset().filter(status='running')
        
        # Enriquecer con estadísticas del manager
        sessions_data = []
        for session in active_sessions:
            session_data = SimulatorSessionListSerializer(session).data
            
            # Agregar stats en tiempo real del manager
            stats = simulator_manager.get_simulator_stats(session.id)
            if stats:
                session_data['live_stats'] = stats
            
            sessions_data.append(session_data)
        
        return Response(sessions_data)
    
    @action(detail=False, methods=['get'])
    def available_employees(self, request):
        """Listar empleados disponibles para asignar simuladores."""
        if request.user.role == 'admin':
            # Admin ve todos los empleados
            employees = CustomUser.objects.filter(
                role='employee',
                is_active=True
            ).select_related('supervisor')
        elif request.user.role == 'supervisor':
            # Supervisor ve solo sus empleados
            employees = CustomUser.objects.filter(
                role='employee',
                supervisor=request.user,
                is_active=True
            ).select_related('supervisor')
        else:
            return Response(
                {'error': 'No tiene permisos para ver esta información'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EmployeeForSimulatorSerializer(employees, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def stop_all(self, request):
        """Detener todos los simuladores activos."""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Solo administradores pueden detener todos los simuladores'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Detener todos en el manager
        simulator_manager.stop_all_simulators()
        
        # Actualizar todas las sesiones en BD
        active_sessions = SimulatorSession.objects.filter(status='running')
        count = active_sessions.update(
            status='stopped',
            stopped_at=timezone.now()
        )
        
        logger.info(f"🛑 Todos los simuladores detenidos por {request.user.email} ({count} sesiones)")
        
        return Response({
            'message': f'Se detuvieron {count} simuladores',
            'count': count
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas generales de simuladores."""
        queryset = self.get_queryset()
        
        total = queryset.count()
        running = queryset.filter(status='running').count()
        stopped = queryset.filter(status='stopped').count()
        errors = queryset.filter(status='error').count()
        
        # Estadísticas de los activos
        active_ids = simulator_manager.get_active_sessions()
        live_stats = []
        for session_id in active_ids:
            stats = simulator_manager.get_simulator_stats(session_id)
            if stats:
                stats['session_id'] = session_id
                live_stats.append(stats)
        
        return Response({
            'total_sessions': total,
            'running': running,
            'stopped': stopped,
            'errors': errors,
            'active_in_memory': len(active_ids),
            'live_stats': live_stats
        })
