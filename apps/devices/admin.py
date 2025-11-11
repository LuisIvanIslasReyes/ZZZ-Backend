from django.contrib import admin
from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_identifier', 'employee', 'supervisor', 'is_active', 'last_connection', 'created_at']
    list_filter = ['is_active', 'supervisor', 'created_at']
    search_fields = ['device_identifier', 'employee__email', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información del Dispositivo', {
            'fields': ('device_identifier', 'is_active', 'last_connection')
        }),
        ('Asignación', {
            'fields': ('employee', 'supervisor')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
