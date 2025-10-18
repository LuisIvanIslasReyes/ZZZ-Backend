"""
Authentication views
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .models import Employee
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    FCMTokenSerializer,
    EmployeeSerializer
)
from .permissions import IsOwnerOrSupervisor

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Register a new user
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    Change user password
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.data['old_password']):
            return Response(
                {'error': 'Contraseña actual incorrecta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(serializer.data['new_password'])
        user.save()
        
        return Response({'message': 'Contraseña actualizada exitosamente'})


class RegisterFCMTokenView(APIView):
    """
    Register FCM token for push notifications
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update or create employee profile
        employee, created = Employee.objects.get_or_create(
            user=request.user,
            defaults={'employee_id': f'EMP-{request.user.id}'}
        )
        employee.fcm_token = serializer.data['fcm_token']
        employee.save()
        
        return Response({'message': 'Token FCM registrado exitosamente'})


class EmployeeListView(generics.ListAPIView):
    """
    List all employees (for supervisors and admins)
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all employees
        if user.is_admin:
            return User.objects.filter(role=User.Role.EMPLOYEE)
        
        # Supervisor can see their supervised employees
        if user.is_supervisor:
            return User.objects.filter(
                employee_profile__supervisor=user
            )
        
        # Employees can only see themselves
        return User.objects.filter(id=user.id)


class EmployeeDetailView(generics.RetrieveAPIView):
    """
    Get employee details
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSupervisor]
    
    def get_queryset(self):
        return User.objects.filter(role=User.Role.EMPLOYEE)
