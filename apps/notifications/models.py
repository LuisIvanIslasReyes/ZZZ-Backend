"""
Notification models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class NotificationType(models.TextChoices):
    """Notification types"""
    ALERT = 'alert', 'Alerta'
    RECOMMENDATION = 'recommendation', 'Recomendación'
    REPORT = 'report', 'Reporte'
    SYSTEM = 'system', 'Sistema'
    REMINDER = 'reminder', 'Recordatorio'
    UPDATE = 'update', 'Actualización'


class NotificationChannel(models.TextChoices):
    """Notification delivery channels"""
    EMAIL = 'email', 'Email'
    PUSH = 'push', 'Push Notification'
    SMS = 'sms', 'SMS'
    IN_APP = 'in_app', 'In-App'


class NotificationPriority(models.TextChoices):
    """Notification priority levels"""
    LOW = 'low', 'Baja'
    MEDIUM = 'medium', 'Media'
    HIGH = 'high', 'Alta'
    URGENT = 'urgent', 'Urgente'


class Notification(models.Model):
    """Notification model"""
    
    # Basic info
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    priority = models.CharField(max_length=10, choices=NotificationPriority.choices, default=NotificationPriority.MEDIUM)
    
    # Recipients
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )
    
    # Delivery
    channels = models.JSONField(default=list)  # List of channels to send to
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery status per channel
    delivery_status = models.JSONField(default=dict)  # {channel: {status, timestamp, error}}
    
    # Related objects
    related_alert = models.ForeignKey(
        'alerts.Alert',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_recommendation = models.ForeignKey(
        'recommendations.Recommendation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Metadata
    data = models.JSONField(default=dict, blank=True)  # Additional notification data
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['scheduled_for']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def update_delivery_status(self, channel, status, error=None):
        """Update delivery status for a channel"""
        if not self.delivery_status:
            self.delivery_status = {}
        
        self.delivery_status[channel] = {
            'status': status,  # 'pending', 'sent', 'delivered', 'failed'
            'timestamp': timezone.now().isoformat(),
            'error': error
        }
        self.save()


class NotificationTemplate(models.Model):
    """Notification templates"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Template content
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    
    # Template settings
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    default_priority = models.CharField(max_length=10, choices=NotificationPriority.choices, default=NotificationPriority.MEDIUM)
    default_channels = models.JSONField(default=list)
    
    # Variables that can be used in template
    available_variables = models.JSONField(default=list)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def render(self, context):
        """Render template with context variables"""
        title = self.title_template
        message = self.message_template
        
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            title = title.replace(placeholder, str(value))
            message = message.replace(placeholder, str(value))
        
        return title, message


class NotificationQueue(models.Model):
    """Queue for scheduled and batch notifications"""
    
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='queue_item'
    )
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('processing', 'Procesando'),
            ('sent', 'Enviado'),
            ('failed', 'Falló'),
            ('cancelled', 'Cancelado'),
        ],
        default='pending'
    )
    
    # Retry logic
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['notification__scheduled_for']),
        ]
    
    def __str__(self):
        return f"Queue item for {self.notification.title}"


class NotificationPreference(models.Model):
    """User notification preferences by type"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    in_app_enabled = models.BooleanField(default=True)
    
    # Frequency settings
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Inmediato'),
            ('hourly', 'Cada Hora'),
            ('daily', 'Diario'),
            ('weekly', 'Semanal'),
            ('disabled', 'Deshabilitado'),
        ],
        default='immediate'
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'notification_type']
        ordering = ['user', 'notification_type']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.notification_type}"
    
    def get_enabled_channels(self):
        """Get list of enabled channels for this preference"""
        channels = []
        if self.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if self.push_enabled:
            channels.append(NotificationChannel.PUSH)
        if self.sms_enabled:
            channels.append(NotificationChannel.SMS)
        if self.in_app_enabled:
            channels.append(NotificationChannel.IN_APP)
        return channels