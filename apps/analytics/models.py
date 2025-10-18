"""
Analytics models
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AnalyticsReport(models.Model):
    """Store generated analytics reports"""
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50)
    parameters = models.JSONField(default=dict)
    results = models.JSONField(default=dict)
    
    # Optional employee filter
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analytics_reports'
    )
    
    # Optional department filter
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analytics_reports'
    )
    
    # Metadata
    generated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d')}"