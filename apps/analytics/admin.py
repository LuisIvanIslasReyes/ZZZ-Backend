from django.contrib import admin
from .models import FatigueAlert, RoutineRecommendation


@admin.register(FatigueAlert)
class FatigueAlertAdmin(admin.ModelAdmin):
    list_display = ['employee', 'severity', 'alert_type', 'fatigue_index', 'is_resolved', 'timestamp']
    list_filter = ['severity', 'is_resolved', 'alert_type', 'timestamp']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name', 'message']
    readonly_fields = ['timestamp', 'created_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Información de la Alerta', {
            'fields': ('employee', 'supervisor', 'severity', 'alert_type', 'message', 'fatigue_index')
        }),
        ('Estado', {
            'fields': ('is_resolved', 'resolved_at', 'resolved_by')
        }),
        ('Metadata', {
            'fields': ('timestamp', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
    mark_as_resolved.short_description = "Marcar como resuelta"


@admin.register(RoutineRecommendation)
class RoutineRecommendationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'supervisor', 'recommendation_type', 'priority', 'is_applied', 'created_at']
    list_filter = ['recommendation_type', 'priority', 'is_applied', 'created_at']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información de la Recomendación', {
            'fields': ('supervisor', 'employee', 'recommendation_type', 'priority', 'description')
        }),
        ('Datos Base', {
            'fields': ('based_on_data',)
        }),
        ('Estado', {
            'fields': ('is_applied', 'applied_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_applied']
    
    def mark_as_applied(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_applied=True, applied_at=timezone.now())
    mark_as_applied.short_description = "Marcar como aplicada"
