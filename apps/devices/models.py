from django.db import models
from django.conf import settings


class Device(models.Model):
    """
    Modelo para dispositivos ESP32 wearables.
    Cada empleado tiene asignado 1 dispositivo.
    """
    device_identifier = models.CharField(
        max_length=50,
        unique=True,
        help_text="Identificador único del dispositivo (ej: ESP32-001)"
    )
    
    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado al que está asignado el dispositivo"
    )
    
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='managed_devices',
        limit_choices_to={'role': 'supervisor'},
        help_text="Supervisor que gestiona este dispositivo"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Si el dispositivo está activo y en uso"
    )
    
    last_connection = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que el dispositivo envió datos"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'devices'
        ordering = ['-created_at']
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        indexes = [
            models.Index(fields=['employee']),
            models.Index(fields=['supervisor']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.device_identifier} - {self.employee.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Validar que el employee sea realmente un empleado
        if self.employee and self.employee.role != 'employee':
            raise ValueError("Solo se pueden asignar dispositivos a usuarios con rol 'employee'")
        
        # Validar que el supervisor sea realmente un supervisor
        if self.supervisor and self.supervisor.role != 'supervisor':
            raise ValueError("Solo usuarios con rol 'supervisor' pueden gestionar dispositivos")
        
        # El supervisor del dispositivo debe ser el mismo que el supervisor del empleado
        if self.employee and self.employee.supervisor != self.supervisor:
            raise ValueError("El supervisor del dispositivo debe coincidir con el supervisor del empleado")
        
        super().save(*args, **kwargs)
