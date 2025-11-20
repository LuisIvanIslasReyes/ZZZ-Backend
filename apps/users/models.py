from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para el modelo CustomUser.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario regular con el email y password dados.
        """
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el email y password dados.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado con roles y jerarquía.
    
    Roles:
    - admin: Equipo de desarrollo, gestiona empresas (clientes)
    - supervisor: Cuenta de empresa, gestiona empleados de su empresa
    - employee: Empleado que usa el wearable, pertenece a una empresa
    
    Jerarquía:
    Admin (equipo dev) → Companies (N)
    Company (1) → Supervisors (N) → Employees (N)
    """
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('supervisor', 'Supervisor'),
        ('employee', 'Empleado'),
    ]
    
    # Campos básicos
    email = models.EmailField(
        verbose_name='Correo electrónico',
        max_length=255,
        unique=True,
    )
    first_name = models.CharField('Nombre', max_length=100)
    last_name = models.CharField('Apellido', max_length=100)
    
    # Información adicional del empleado
    phone = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    department = models.CharField('Departamento', max_length=100, blank=True, null=True)
    position = models.CharField('Puesto', max_length=100, blank=True, null=True)
    
    # Rol del usuario
    role = models.CharField(
        'Rol',
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee'
    )
    
    # Relación con empresa (para supervisores y empleados)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Empresa',
        help_text='Empresa a la que pertenece (supervisores y empleados)'
    )
    
    # Relaciones jerárquicas
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        limit_choices_to={'role': 'supervisor'},
        verbose_name='Supervisor',
        help_text='Supervisor asignado (solo para empleados)'
    )
    
    # Campos de estado
    is_active = models.BooleanField('Activo', default=True)
    is_staff = models.BooleanField('Es staff', default=False)
    
    # Timestamps
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    last_login = models.DateTimeField('Último login', null=True, blank=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['supervisor']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        """
        Retorna el nombre completo del usuario.
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """
        Retorna el nombre corto del usuario.
        """
        return self.first_name
    
    def is_admin(self):
        """
        Verifica si el usuario es administrador.
        """
        return self.role == 'admin'
    
    def is_supervisor(self):
        """
        Verifica si el usuario es supervisor.
        """
        return self.role == 'supervisor'
    
    def is_employee(self):
        """
        Verifica si el usuario es empleado.
        """
        return self.role == 'employee'
    
    def get_supervised_employees(self):
        """
        Retorna los empleados supervisados por este usuario (si es supervisor).
        """
        if self.is_supervisor():
            return self.employees.filter(is_active=True)
        return CustomUser.objects.none()
    
    def get_supervisor_count(self):
        """
        Retorna el número de supervisores bajo este admin (si es admin).
        """
        if self.is_admin():
            return self.supervisors.filter(is_active=True).count()
        return 0
    
    def save(self, *args, **kwargs):
        """
        Override del método save para validaciones adicionales.
        """
        # Validar jerarquía
        if self.role == 'supervisor' and self.supervisor:
            # Los supervisores no deben tener supervisor asignado
            self.supervisor = None
        
        if self.role == 'admin' and self.supervisor:
            # Los admins no deben tener supervisor asignado
            self.supervisor = None
        
        # Si es admin o supervisor, marcar como staff
        if self.role in ['admin', 'supervisor']:
            self.is_staff = True
        
        super().save(*args, **kwargs)


class ActivityLog(models.Model):
    """
    Modelo para registrar todas las acciones administrativas del sistema.
    Permite auditoría completa de cambios y acciones realizadas por usuarios.
    """
    
    ACTION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('login', 'Iniciar sesión'),
        ('logout', 'Cerrar sesión'),
        ('resolve_alert', 'Resolver alerta'),
        ('apply_recommendation', 'Aplicar recomendación'),
        ('assign_device', 'Asignar dispositivo'),
        ('other', 'Otra acción'),
    ]
    
    RESOURCE_CHOICES = [
        ('user', 'Usuario'),
        ('supervisor', 'Supervisor'),
        ('employee', 'Empleado'),
        ('device', 'Dispositivo'),
        ('alert', 'Alerta'),
        ('recommendation', 'Recomendación'),
        ('system', 'Sistema'),
    ]
    
    # Usuario que realizó la acción
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
        verbose_name='Usuario'
    )
    
    # Tipo de acción
    action = models.CharField(
        'Acción',
        max_length=50,
        choices=ACTION_CHOICES
    )
    
    # Tipo de recurso afectado
    resource_type = models.CharField(
        'Tipo de recurso',
        max_length=50,
        choices=RESOURCE_CHOICES
    )
    
    # ID del recurso afectado (genérico)
    resource_id = models.IntegerField(
        'ID del recurso',
        null=True,
        blank=True
    )
    
    # Detalles de la acción en JSON
    details = models.JSONField(
        'Detalles',
        default=dict,
        blank=True,
        help_text='Información adicional sobre la acción realizada'
    )
    
    # Información de la solicitud
    ip_address = models.GenericIPAddressField(
        'Dirección IP',
        null=True,
        blank=True
    )
    
    user_agent = models.TextField(
        'User Agent',
        null=True,
        blank=True
    )
    
    # Timestamp
    timestamp = models.DateTimeField(
        'Fecha y hora',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Registro de Actividad'
        verbose_name_plural = 'Registros de Actividad'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'Sistema'
        return f"{user_name} - {self.get_action_display()} - {self.get_resource_type_display()} - {self.timestamp}"
    
    @classmethod
    def log_action(cls, user, action, resource_type, resource_id=None, details=None, request=None):
        """
        Método de conveniencia para crear un log de actividad.
        
        Args:
            user: Usuario que realiza la acción
            action: Tipo de acción (ver ACTION_CHOICES)
            resource_type: Tipo de recurso afectado (ver RESOURCE_CHOICES)
            resource_id: ID del recurso (opcional)
            details: Dict con información adicional (opcional)
            request: Objeto request de Django para extraer IP y user-agent (opcional)
        """
        log_data = {
            'user': user,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details or {}
        }
        
        # Extraer información del request si está disponible
        if request:
            log_data['ip_address'] = cls._get_client_ip(request)
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(**log_data)
    
    @staticmethod
    def _get_client_ip(request):
        """
        Obtiene la IP real del cliente, considerando proxies.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


