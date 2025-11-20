from django.db import models
from django.utils import timezone


class Company(models.Model):
    """
    Modelo para empresas que contratan el servicio.
    Los administradores (equipo de desarrollo) gestionan las empresas.
    Cada empresa tiene supervisores que gestionan empleados.
    """
    name = models.CharField(
        'Nombre de la empresa',
        max_length=255,
        unique=True,
        help_text="Nombre de la empresa cliente"
    )
    
    contact_email = models.EmailField(
        'Email de contacto',
        max_length=255,
        help_text="Email principal de contacto de la empresa"
    )
    
    contact_phone = models.CharField(
        'Teléfono de contacto',
        max_length=20,
        blank=True,
        null=True,
        help_text="Teléfono de contacto de la empresa"
    )
    
    address = models.TextField(
        'Dirección',
        blank=True,
        null=True,
        help_text="Dirección física de la empresa"
    )
    
    is_active = models.BooleanField(
        'Activa',
        default=True,
        help_text="Si la empresa está activa y puede usar el servicio"
    )
    
    subscription_start = models.DateField(
        'Inicio de suscripción',
        default=timezone.now,
        help_text="Fecha de inicio del servicio"
    )
    
    subscription_end = models.DateField(
        'Fin de suscripción',
        null=True,
        blank=True,
        help_text="Fecha de fin del servicio (null = indefinido)"
    )
    
    max_employees = models.IntegerField(
        'Máximo de empleados',
        default=50,
        help_text="Número máximo de empleados permitidos para esta empresa"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        ordering = ['-created_at']
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return self.name
    
    @property
    def employee_count(self):
        """Número actual de empleados en la empresa"""
        from apps.users.models import CustomUser
        return CustomUser.objects.filter(
            company=self,
            role='employee'
        ).count()
    
    @property
    def supervisor_count(self):
        """Número de supervisores en la empresa"""
        from apps.users.models import CustomUser
        return CustomUser.objects.filter(
            company=self,
            role='supervisor'
        ).count()
    
    @property
    def is_subscription_active(self):
        """Verifica si la suscripción está vigente"""
        if not self.is_active:
            return False
        if self.subscription_end:
            return timezone.now().date() <= self.subscription_end
        return True
