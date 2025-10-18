"""
Alert admin
"""
from django.contrib import admin
from .models import Alert, AlertRule


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'alert_type', 'severity', 'is_active', 'is_acknowledged', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_active', 'is_acknowledged', 'created_at']
    search_fields = ['title', 'employee__email', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['created_at', 'acknowledged_at', 'resolved_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'message', 'alert_type', 'severity')
        }),
        ('Relaciones', {
            'fields': ('employee', 'device')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_acknowledged', 'acknowledged_by', 'acknowledged_at', 'resolved_at')
        }),
        ('Datos Adicionales', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'alert_type', 'severity', 'is_active', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_active', 'created_at']
    search_fields = ['name', 'description']