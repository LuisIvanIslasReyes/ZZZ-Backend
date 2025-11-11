from django.contrib import admin
from .models import SensorData, ProcessedMetrics


@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ['device', 'timestamp', 'heart_rate', 'spo2', 'created_at']
    list_filter = ['device', 'timestamp']
    search_fields = ['device__device_identifier', 'device__employee__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Dispositivo y Tiempo', {
            'fields': ('device', 'timestamp')
        }),
        ('Datos del Sensor', {
            'fields': ('heart_rate', 'spo2', 'accel_x', 'accel_y', 'accel_z')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProcessedMetrics)
class ProcessedMetricsAdmin(admin.ModelAdmin):
    list_display = ['employee', 'window_start', 'fatigue_index', 'hr_avg', 'spo2_avg', 'activity_level']
    list_filter = ['employee', 'window_start', 'hr_trend']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['created_at']
    date_hierarchy = 'window_start'
    
    fieldsets = (
        ('Información General', {
            'fields': ('device', 'employee', 'window_start', 'window_end')
        }),
        ('Métricas de Ritmo Cardíaco', {
            'fields': ('hr_avg', 'hr_max', 'hr_min', 'hrv_rmssd', 'hrv_sdnn', 'hr_trend')
        }),
        ('Métricas de Oxigenación', {
            'fields': ('spo2_avg', 'spo2_min', 'spo2_variance', 'desaturation_count')
        }),
        ('Métricas de Movimiento', {
            'fields': ('activity_level', 'movement_variance', 'movement_entropy', 'posture_angle')
        }),
        ('Features Combinados', {
            'fields': ('fatigue_index', 'hr_activity_ratio', 'recovery_time')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
