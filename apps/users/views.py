from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .models import CustomUser
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    LoginSerializer, ChangePasswordSerializer,
    EmployeeListSerializer, SupervisorListSerializer
)
from .permissions import (
    IsAdmin, IsSupervisor, IsAdminOrSupervisor,
    CanManageEmployees, CanManageSupervisors,
    IsOwnerOrSupervisor
)

User = get_user_model()


class LoginView(views.APIView):
    """
    Vista para login de usuarios.
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    """
    Vista para logout de usuarios.
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'detail': 'Sesión cerrada exitosamente'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': 'Error al cerrar sesión'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(views.APIView):
    """
    Vista para cambiar contraseña del usuario actual.
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Contraseña cambiada exitosamente'}, status=status.HTTP_200_OK)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Vista para obtener y actualizar el perfil del usuario actual.
    GET/PUT /api/auth/me/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


# ==================== VISTAS PARA ADMINISTRADOR ====================

class SupervisorListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar y crear supervisores (solo Admin).
    GET/POST /api/admin/supervisors/
    """
    permission_classes = [CanManageSupervisors]
    
    def get_queryset(self):
        return User.objects.filter(role='supervisor').select_related('admin').prefetch_related('employees')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return SupervisorListSerializer
    
    def perform_create(self, serializer):
        # Asignar el admin actual al supervisor
        serializer.save(admin=self.request.user, role='supervisor')


class SupervisorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para ver, actualizar y eliminar supervisores (solo Admin).
    GET/PUT/DELETE /api/admin/supervisors/{id}/
    """
    permission_classes = [CanManageSupervisors]
    
    def get_queryset(self):
        return User.objects.filter(role='supervisor').select_related('admin').prefetch_related('employees')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()


class AdminStatsView(views.APIView):
    """
    Vista para estadísticas generales del sistema (solo Admin).
    GET /api/admin/stats/
    """
    permission_classes = [IsAdmin]
    
    def get(self, request):
        stats = {
            'total_supervisors': User.objects.filter(role='supervisor', is_active=True).count(),
            'total_employees': User.objects.filter(role='employee', is_active=True).count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'inactive_users': User.objects.filter(is_active=False).count(),
        }
        return Response(stats, status=status.HTTP_200_OK)


# ==================== VISTAS PARA SUPERVISOR ====================

class EmployeeListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar y crear empleados (Supervisor).
    GET/POST /api/supervisor/employees/
    """
    permission_classes = [CanManageEmployees]
    pagination_class = None  # Deshabilitar paginación para esta vista
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            # Admin ve todos los empleados de todas las empresas
            return User.objects.filter(role='employee').select_related('supervisor', 'company')
        elif user.is_supervisor():
            # Supervisor solo ve SUS empleados (donde él es el supervisor)
            return User.objects.filter(
                role='employee',
                supervisor=user
            ).select_related('supervisor', 'company')
        return User.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return EmployeeListSerializer
    
    def perform_create(self, serializer):
        # Asignar el supervisor actual y la empresa al empleado
        serializer.save(
            supervisor=self.request.user,
            company=self.request.user.company,
            role='employee'
        )


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para ver, actualizar y eliminar empleados (Supervisor).
    GET/PUT/DELETE /api/supervisor/employees/{id}/
    """
    permission_classes = [CanManageEmployees]
    pagination_class = None  # Deshabilitar paginación
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return User.objects.filter(role='employee').select_related('supervisor', 'company')
        elif user.is_supervisor():
            # Supervisor solo ve SUS empleados (donde él es el supervisor)
            return User.objects.filter(
                role='employee',
                supervisor=user
            ).select_related('supervisor', 'company')
        return User.objects.none()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        # Para GET (detalle), usar EmployeeListSerializer para incluir todos los campos
        from .serializers import EmployeeListSerializer
        return EmployeeListSerializer
    
    def perform_destroy(self, instance):
        # Verificar que el empleado pertenezca a la empresa del supervisor
        if self.request.user.is_supervisor() and instance.company != self.request.user.company:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No puedes eliminar empleados de otra empresa")
        # Soft delete
        instance.is_active = False
        instance.save()


# ==================== VISTAS PARA EMPLEADO ====================

class EmployeeProfileView(generics.RetrieveAPIView):
    """
    Vista para que el empleado vea su perfil.
    GET /api/employee/me/
    """
    permission_classes = [IsAuthenticated]
    from .serializers import EmployeeListSerializer
    serializer_class = EmployeeListSerializer
    
    def get_object(self):
        return self.request.user

