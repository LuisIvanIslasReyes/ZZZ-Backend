"""
Notification serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Notification, 
    NotificationTemplate, 
    NotificationQueue, 
    NotificationPreference,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority',
            'recipient', 'recipient_name', 'sender', 'sender_name',
            'channels', 'is_read', 'read_at', 'delivery_status',
            'related_alert', 'related_recommendation', 'data',
            'scheduled_for', 'sent_at', 'created_at'
        ]
        read_only_fields = ['read_at', 'sent_at', 'created_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'title', 'message', 'notification_type', 'priority',
            'recipient', 'channels', 'related_alert', 'related_recommendation',
            'data', 'scheduled_for'
        ]


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Notification template serializer"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'description', 'title_template', 'message_template',
            'notification_type', 'default_priority', 'default_channels',
            'available_variables', 'is_active', 'created_at', 'updated_at'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Notification preference serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'user_name', 'notification_type',
            'email_enabled', 'push_enabled', 'sms_enabled', 'in_app_enabled',
            'frequency', 'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    notifications_today = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_priority = serializers.DictField()
    delivery_success_rate = serializers.FloatField()


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending notifications"""
    
    title = serializers.CharField(max_length=200)
    message = serializers.TextField()
    notification_type = serializers.ChoiceField(choices=NotificationType.choices)
    priority = serializers.ChoiceField(choices=NotificationPriority.choices, default=NotificationPriority.MEDIUM)
    recipients = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=NotificationChannel.choices),
        default=list
    )
    scheduled_for = serializers.DateTimeField(required=False)
    data = serializers.JSONField(required=False, default=dict)