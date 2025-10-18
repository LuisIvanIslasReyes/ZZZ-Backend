"""
Alert serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Alert, AlertRule, AlertType, AlertSeverity

User = get_user_model()


class AlertSerializer(serializers.ModelSerializer):
    """Alert serializer"""
    
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    device_name = serializers.CharField(source='device.name', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.get_full_name', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'message', 'alert_type', 'severity',
            'employee', 'employee_name', 'device', 'device_name',
            'is_active', 'is_acknowledged', 'acknowledged_at', 
            'acknowledged_by', 'acknowledged_by_name', 'data',
            'created_at', 'resolved_at'
        ]
        read_only_fields = ['acknowledged_at', 'acknowledged_by', 'resolved_at']


class AlertCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alerts"""
    
    class Meta:
        model = Alert
        fields = [
            'title', 'message', 'alert_type', 'severity',
            'employee', 'device', 'data'
        ]


class AlertAcknowledgeSerializer(serializers.Serializer):
    """Serializer for acknowledging alerts"""
    
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)


class AlertRuleSerializer(serializers.ModelSerializer):
    """Alert rule serializer"""
    
    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'alert_type', 'severity',
            'conditions', 'is_active', 'created_at', 'updated_at'
        ]


class AlertStatsSerializer(serializers.Serializer):
    """Serializer for alert statistics"""
    
    total_alerts = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    acknowledged_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    alerts_by_type = serializers.DictField()
    alerts_by_severity = serializers.DictField()