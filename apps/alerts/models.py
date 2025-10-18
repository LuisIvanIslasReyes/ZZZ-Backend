"""
Alert models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AlertType(models.TextChoices):
    """Alert types"""
    FATIGUE_HIGH = 'fatigue_high', 'Fatiga Alta'
    FATIGUE_CRITICAL = 'fatigue_critical', 'Fatiga Crítica'
    HEART_RATE_ABNORMAL = 'hr_abnormal', 'Ritmo Cardíaco Anormal'
    STRESS_HIGH = 'stress_high', 'Estrés Alto'
    DEVICE_OFFLINE = 'device_offline', 'Dispositivo Desconectado'
    BATTERY_LOW = 'battery_low', 'Batería Baja'
    INACTIVITY = 'inactivity', 'Inactividad Prolongada'
    CUSTOM = 'custom', 'Personalizada'


class AlertSeverity(models.TextChoices):
    """Alert severity levels"""
    LOW = 'low', 'Baja'
    MEDIUM = 'medium', 'Media'
    HIGH = 'high', 'Alta'
    CRITICAL = 'critical', 'Crítica'


class Alert(models.Model):
    """Alert model"""
    
    # Basic info
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=AlertSeverity.choices)
    
    # Related entities
    employee = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='alerts'
    )
    device = models.ForeignKey(
        'devices.Device', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='alerts'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    
    # Metadata
    data = models.JSONField(default=dict, blank=True)  # Additional alert data
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.employee.get_full_name()}"
    
    def acknowledge(self, acknowledged_by):
        """Mark alert as acknowledged"""
        self.is_acknowledged = True
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = acknowledged_by
        self.save()
    
    def resolve(self):
        """Mark alert as resolved"""
        self.is_active = False
        self.resolved_at = timezone.now()
        self.save()


class AlertRule(models.Model):
    """Alert rules for automatic alert generation"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=AlertSeverity.choices)
    
    # Rule conditions (stored as JSON)
    conditions = models.JSONField(default=dict)
    
    # Rule status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name