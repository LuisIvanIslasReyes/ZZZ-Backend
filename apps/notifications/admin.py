"""
Notification admin
"""
from django.contrib import admin
from .models import Notification, NotificationTemplate, NotificationQueue, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'priority', 'is_read', 'sent_at', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__email', 'recipient__first_name', 'recipient__last_name']
    readonly_fields = ['created_at', 'read_at', 'sent_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Destinatarios', {
            'fields': ('recipient', 'sender')
        }),
        ('Entrega', {
            'fields': ('channels', 'delivery_status', 'scheduled_for', 'sent_at')
        }),
        ('Estado', {
            'fields': ('is_read', 'read_at')
        }),
        ('Relaciones', {
            'fields': ('related_alert', 'related_recommendation'),
            'classes': ('collapse',)
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


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'notification_type', 'default_priority', 'is_active', 'created_at']
    list_filter = ['notification_type', 'default_priority', 'is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = ['notification', 'status', 'attempts', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at', 'processed_at', 'last_attempt_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'email_enabled', 'push_enabled', 'frequency', 'updated_at']
    list_filter = ['notification_type', 'email_enabled', 'push_enabled', 'frequency', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']