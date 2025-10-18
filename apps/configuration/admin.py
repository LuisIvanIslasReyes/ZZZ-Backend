"""
Configuration admin
"""
from django.contrib import admin
from .models import Configuration, SystemThreshold, NotificationSettings


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'data_type', 'is_active', 'is_editable', 'updated_by', 'updated_at']
    list_filter = ['category', 'data_type', 'is_active', 'is_editable', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('key', 'value', 'category', 'description')
        }),
        ('Tipo y Validación', {
            'fields': ('data_type', 'min_value', 'max_value', 'allowed_values')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_editable')
        }),
        ('Metadata', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SystemThreshold)
class SystemThresholdAdmin(admin.ModelAdmin):
    list_display = ['name', 'metric_type', 'low_threshold', 'medium_threshold', 'high_threshold', 'critical_threshold', 'is_active', 'updated_at']
    list_filter = ['metric_type', 'is_active', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_alerts_enabled', 'push_alerts_enabled', 'email_frequency', 'stress_alert_threshold', 'updated_at']
    list_filter = ['email_alerts_enabled', 'push_alerts_enabled', 'email_frequency', 'stress_alert_threshold', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']