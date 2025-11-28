from django.db import models
from django.conf import settings


class FatigueAlert(models.Model):
    """
    Modelo para alertas de fatiga generadas automáticamente.
    Se crean cuando se detectan condiciones peligrosas o niveles altos de fatiga.
    """
    SEVERITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fatigue_alerts',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado al que se le generó la alerta"
    )
    
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='supervised_alerts',
        limit_choices_to={'role': 'supervisor'},
        help_text="Supervisor que debe atender la alerta"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Momento en que se generó la alerta"
    )
    
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        db_index=True,
        help_text="Nivel de severidad de la alerta"
    )
    
    alert_type = models.CharField(
        max_length=50,
        help_text="Tipo de alerta (high_fatigue, low_spo2, high_hr, etc.)"
    )
    
    message = models.TextField(
        help_text="Mensaje descriptivo de la alerta"
    )
    
    fatigue_index = models.FloatField(
        help_text="Índice de fatiga en el momento de la alerta"
    )
    
    is_acknowledged = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Si la alerta fue reconocida/vista"
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se reconoció la alerta"
    )
    
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts',
        help_text="Usuario que reconoció la alerta"
    )
    
    is_resolved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Si la alerta fue resuelta"
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se resolvió la alerta"
    )
    
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        help_text="Usuario que resolvió la alerta"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fatigue_alerts'
        ordering = ['-timestamp']
        verbose_name = 'Alerta de Fatiga'
        verbose_name_plural = 'Alertas de Fatiga'
        indexes = [
            models.Index(fields=['employee', 'is_resolved']),
            models.Index(fields=['supervisor', 'is_resolved']),
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        status = "Resuelta" if self.is_resolved else "Activa"
        return f"{self.get_severity_display()} - {self.employee.get_full_name()} [{status}]"


class RoutineRecommendation(models.Model):
    """
    Modelo para recomendaciones de optimización de rutinas laborales.
    Generadas para supervisores basándose en patrones de fatiga.
    """
    RECOMMENDATION_TYPES = [
        ('break', 'Descanso'),
        ('task_redistribution', 'Redistribución de Tareas'),
        ('shift_rotation', 'Rotación de Turnos'),
    ]
    
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendations',
        limit_choices_to={'role': 'supervisor'},
        help_text="Supervisor que recibe la recomendación"
    )
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_recommendations',
        limit_choices_to={'role': 'employee'},
        help_text="Empleado para el cual es la recomendación"
    )
    
    recommendation_type = models.CharField(
        max_length=30,
        choices=RECOMMENDATION_TYPES,
        help_text="Tipo de recomendación"
    )
    
    description = models.TextField(
        help_text="Descripción detallada de la recomendación"
    )
    
    priority = models.IntegerField(
        default=3,
        help_text="Prioridad de 1 (más urgente) a 5 (menos urgente)"
    )
    
    based_on_data = models.JSONField(
        help_text="Métricas y datos que generaron esta recomendación"
    )
    
    is_applied = models.BooleanField(
        default=False,
        help_text="Si la recomendación fue aplicada"
    )
    
    applied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se aplicó la recomendación"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'routine_recommendations'
        ordering = ['priority', '-created_at']
        verbose_name = 'Recomendación de Rutina'
        verbose_name_plural = 'Recomendaciones de Rutinas'
        indexes = [
            models.Index(fields=['supervisor', 'is_applied']),
            models.Index(fields=['employee', 'is_applied']),
            models.Index(fields=['priority', '-created_at']),
        ]
    
    def __str__(self):
        status = "Aplicada" if self.is_applied else "Pendiente"
        return f"{self.get_recommendation_type_display()} - {self.employee.get_full_name()} [{status}]"
