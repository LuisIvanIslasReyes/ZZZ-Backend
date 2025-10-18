"""
Recommendation models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class RecommendationType(models.TextChoices):
    """Recommendation types"""
    BREAK = 'break', 'Tomar un Descanso'
    HYDRATION = 'hydration', 'Hidratación'
    EXERCISE = 'exercise', 'Ejercicio'
    BREATHING = 'breathing', 'Ejercicios de Respiración'
    POSTURE = 'posture', 'Corrección de Postura'
    ENVIRONMENT = 'environment', 'Cambio de Ambiente'
    WORKLOAD = 'workload', 'Reducir Carga de Trabajo'
    SLEEP = 'sleep', 'Mejorar Descanso'
    NUTRITION = 'nutrition', 'Alimentación'
    CUSTOM = 'custom', 'Personalizada'


class RecommendationPriority(models.TextChoices):
    """Recommendation priority levels"""
    LOW = 'low', 'Baja'
    MEDIUM = 'medium', 'Media'
    HIGH = 'high', 'Alta'
    URGENT = 'urgent', 'Urgente'


class RecommendationTemplate(models.Model):
    """Template for recommendations"""
    
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField()
    recommendation_type = models.CharField(max_length=20, choices=RecommendationType.choices)
    priority = models.CharField(max_length=10, choices=RecommendationPriority.choices)
    
    # Conditions for auto-generation
    trigger_conditions = models.JSONField(default=dict, blank=True)
    
    # Content
    instructions = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Recommendation(models.Model):
    """Recommendation model"""
    
    # Basic info
    title = models.CharField(max_length=200)
    description = models.TextField()
    recommendation_type = models.CharField(max_length=20, choices=RecommendationType.choices)
    priority = models.CharField(max_length=10, choices=RecommendationPriority.choices)
    
    # Related entities
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    template = models.ForeignKey(
        RecommendationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations'
    )
    
    # Content
    instructions = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    # Feedback
    effectiveness_rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Rating from 1-5"
    )
    feedback_notes = models.TextField(blank=True)
    
    # Metadata
    data = models.JSONField(default=dict, blank=True)  # Additional recommendation data
    source_alert = models.ForeignKey(
        'alerts.Alert',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'is_active']),
            models.Index(fields=['recommendation_type', 'priority']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.employee.get_full_name()}"
    
    def mark_as_applied(self, effectiveness_rating=None, feedback_notes=None):
        """Mark recommendation as applied"""
        self.is_applied = True
        self.applied_at = timezone.now()
        if effectiveness_rating:
            self.effectiveness_rating = effectiveness_rating
        if feedback_notes:
            self.feedback_notes = feedback_notes
        self.save()
    
    @property
    def is_expired(self):
        """Check if recommendation is expired"""
        return self.expires_at and timezone.now() > self.expires_at


class RecommendationFeedback(models.Model):
    """Feedback for recommendations"""
    
    recommendation = models.OneToOneField(
        Recommendation,
        on_delete=models.CASCADE,
        related_name='detailed_feedback'
    )
    
    # Ratings (1-5 scale)
    usefulness_rating = models.PositiveIntegerField()
    ease_of_implementation = models.PositiveIntegerField()
    effectiveness_rating = models.PositiveIntegerField()
    
    # Feedback
    comments = models.TextField(blank=True)
    would_recommend = models.BooleanField()
    
    # Additional data
    implementation_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    obstacles_encountered = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback for {self.recommendation.title}"