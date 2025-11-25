from django.contrib import admin
from .models import FatigueAlert, RoutineRecommendation
from .simulator_models import SimulatorSession


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


@admin.register(SimulatorSession)
class SimulatorSessionAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'employee', 'status', 'fatigue_profile', 'activity_mode', 'current_fatigue', 'messages_sent', 'started_at']
    list_filter = ['status', 'fatigue_profile', 'activity_mode', 'started_at']
    search_fields = ['device_id', 'employee__email', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['started_at', 'stopped_at', 'created_by', 'updated_at', 'messages_sent', 'current_fatigue']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('employee', 'device_id', 'status', 'created_by')
        }),
        ('Configuración de Simulación', {
            'fields': ('fatigue_profile', 'activity_mode', 'base_heart_rate', 'base_spo2', 'initial_fatigue', 'fatigue_rate')
        }),
        ('Configuración MQTT', {
            'fields': ('mqtt_broker', 'mqtt_port', 'publish_interval'),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': ('current_fatigue', 'messages_sent', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'stopped_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['stop_simulators']
    
    def stop_simulators(self, request, queryset):
        from apps.analytics.simulator_manager import simulator_manager
        from django.utils import timezone
        
        count = 0
        for session in queryset.filter(status='running'):
            if simulator_manager.stop_simulator(session.id):
                count += 1
        
        self.message_user(request, f'{count} simulador(es) detenido(s) exitosamente.')
    
    stop_simulators.short_description = "Detener simuladores seleccionados"
