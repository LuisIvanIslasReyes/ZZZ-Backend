"""
User and Employee models
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        SUPERVISOR = 'SUPERVISOR', 'Supervisor'
        EMPLOYEE = 'EMPLOYEE', 'Empleado'
    
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name='Rol'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override username to use email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_supervisor(self):
        return self.role == self.Role.SUPERVISOR
    
    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE


class Employee(models.Model):
    """
    Employee profile with additional information
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name='Usuario'
    )
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='ID de empleado'
    )
    position = models.CharField(
        max_length=100,
        verbose_name='Puesto',
        blank=True
    )
    department = models.CharField(
        max_length=100,
        verbose_name='Departamento',
        blank=True
    )
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_employees',
        verbose_name='Supervisor',
        limit_choices_to={'role': User.Role.SUPERVISOR}
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    timezone = models.CharField(
        max_length=50,
        default='America/Mexico_City',
        verbose_name='Zona horaria'
    )
    
    # Notification settings
    fcm_token = models.TextField(
        blank=True,
        verbose_name='FCM Token',
        help_text='Token de Firebase Cloud Messaging para notificaciones push'
    )
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name='Notificaciones habilitadas'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['employee_id']
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"
