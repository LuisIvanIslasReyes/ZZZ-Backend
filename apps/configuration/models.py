"""
Configuration models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class ConfigurationCategory(models.TextChoices):
    """Configuration categories"""
    THRESHOLDS = 'thresholds', 'Umbrales'
    SYSTEM = 'system', 'Sistema'
    ALERTS = 'alerts', 'Alertas'
    NOTIFICATIONS = 'notifications', 'Notificaciones'
    ANALYTICS = 'analytics', 'Análisis'
    DEVICES = 'devices', 'Dispositivos'


class Configuration(models.Model):
    """System configuration model"""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    category = models.CharField(max_length=20, choices=ConfigurationCategory.choices)
    description = models.TextField(blank=True)
    
    # Validation
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
            ('list', 'List'),
        ],
        default='string'
    )
    
    # Constraints
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    allowed_values = models.JSONField(null=True, blank=True)  # List of allowed values
    
    # Status
    is_active = models.BooleanField(default=True)
    is_editable = models.BooleanField(default=True)
    
    # Metadata
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_configurations'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['key']),
        ]
    
    def __str__(self):
        return f"{self.category}.{self.key}"
    
    def clean(self):
        """Validate configuration value"""
        from django.core.exceptions import ValidationError
        
        # Type validation
        if self.data_type == 'integer' and not isinstance(self.value, int):
            raise ValidationError(f"Value must be an integer")
        elif self.data_type == 'float' and not isinstance(self.value, (int, float)):
            raise ValidationError(f"Value must be a number")
        elif self.data_type == 'boolean' and not isinstance(self.value, bool):
            raise ValidationError(f"Value must be a boolean")
        elif self.data_type == 'list' and not isinstance(self.value, list):
            raise ValidationError(f"Value must be a list")
        
        # Range validation
        if self.data_type in ['integer', 'float'] and isinstance(self.value, (int, float)):
            if self.min_value is not None and self.value < self.min_value:
                raise ValidationError(f"Value must be >= {self.min_value}")
            if self.max_value is not None and self.value > self.max_value:
                raise ValidationError(f"Value must be <= {self.max_value}")
        
        # Allowed values validation
        if self.allowed_values and self.value not in self.allowed_values:
            raise ValidationError(f"Value must be one of: {self.allowed_values}")


class SystemThreshold(models.Model):
    """System thresholds for alerts and recommendations"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Threshold values
    low_threshold = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    medium_threshold = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    high_threshold = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    critical_threshold = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Metadata
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('stress_score', 'Puntuación de Estrés'),
            ('heart_rate', 'Ritmo Cardíaco'),
            ('activity_level', 'Nivel de Actividad'),
            ('battery_level', 'Nivel de Batería'),
            ('custom', 'Personalizado'),
        ]
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate threshold ordering"""
        from django.core.exceptions import ValidationError
        
        if not (self.low_threshold <= self.medium_threshold <= self.high_threshold <= self.critical_threshold):
            raise ValidationError("Thresholds must be in ascending order: low <= medium <= high <= critical")
    
    def get_level(self, value):
        """Get the threshold level for a given value"""
        if value >= self.critical_threshold:
            return 'critical'
        elif value >= self.high_threshold:
            return 'high'
        elif value >= self.medium_threshold:
            return 'medium'
        else:
            return 'low'


class NotificationSettings(models.Model):
    """Notification settings for different user types"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )
    
    # Email notifications
    email_alerts_enabled = models.BooleanField(default=True)
    email_recommendations_enabled = models.BooleanField(default=True)
    email_reports_enabled = models.BooleanField(default=True)
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Inmediato'),
            ('hourly', 'Cada Hora'),
            ('daily', 'Diario'),
            ('weekly', 'Semanal'),
        ],
        default='immediate'
    )
    
    # Push notifications
    push_alerts_enabled = models.BooleanField(default=True)
    push_recommendations_enabled = models.BooleanField(default=True)
    push_quiet_hours_start = models.TimeField(null=True, blank=True)
    push_quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Alert preferences
    stress_alert_threshold = models.CharField(
        max_length=10,
        choices=[
            ('medium', 'Medio'),
            ('high', 'Alto'),
            ('critical', 'Crítico'),
        ],
        default='high'
    )
    
    # Report preferences
    weekly_report_enabled = models.BooleanField(default=True)
    monthly_report_enabled = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Settings"
        verbose_name_plural = "Notification Settings"
    
    def __str__(self):
        return f"Notification settings for {self.user.get_full_name()}"