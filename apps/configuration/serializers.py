"""
Configuration serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Configuration, SystemThreshold, NotificationSettings

User = get_user_model()


class ConfigurationSerializer(serializers.ModelSerializer):
    """Configuration serializer"""
    
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = Configuration
        fields = [
            'id', 'key', 'value', 'category', 'description',
            'data_type', 'min_value', 'max_value', 'allowed_values',
            'is_active', 'is_editable', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['updated_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate configuration data"""
        value = data.get('value')
        data_type = data.get('data_type', 'string')
        min_value = data.get('min_value')
        max_value = data.get('max_value')
        allowed_values = data.get('allowed_values')
        
        # Type validation
        if data_type == 'integer' and not isinstance(value, int):
            raise serializers.ValidationError("Value must be an integer")
        elif data_type == 'float' and not isinstance(value, (int, float)):
            raise serializers.ValidationError("Value must be a number")
        elif data_type == 'boolean' and not isinstance(value, bool):
            raise serializers.ValidationError("Value must be a boolean")
        elif data_type == 'list' and not isinstance(value, list):
            raise serializers.ValidationError("Value must be a list")
        
        # Range validation
        if data_type in ['integer', 'float'] and isinstance(value, (int, float)):
            if min_value is not None and value < min_value:
                raise serializers.ValidationError(f"Value must be >= {min_value}")
            if max_value is not None and value > max_value:
                raise serializers.ValidationError(f"Value must be <= {max_value}")
        
        # Allowed values validation
        if allowed_values and value not in allowed_values:
            raise serializers.ValidationError(f"Value must be one of: {allowed_values}")
        
        return data


class SystemThresholdSerializer(serializers.ModelSerializer):
    """System threshold serializer"""
    
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = SystemThreshold
        fields = [
            'id', 'name', 'description', 'low_threshold', 'medium_threshold',
            'high_threshold', 'critical_threshold', 'metric_type',
            'is_active', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['updated_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate threshold ordering"""
        low = data.get('low_threshold')
        medium = data.get('medium_threshold')
        high = data.get('high_threshold')
        critical = data.get('critical_threshold')
        
        if not (low <= medium <= high <= critical):
            raise serializers.ValidationError(
                "Thresholds must be in ascending order: low <= medium <= high <= critical"
            )
        
        return data


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Notification settings serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'user', 'user_name', 'email_alerts_enabled',
            'email_recommendations_enabled', 'email_reports_enabled',
            'email_frequency', 'push_alerts_enabled', 'push_recommendations_enabled',
            'push_quiet_hours_start', 'push_quiet_hours_end',
            'stress_alert_threshold', 'weekly_report_enabled',
            'monthly_report_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SystemConfigSerializer(serializers.Serializer):
    """Serializer for system configuration overview"""
    
    stress_thresholds = SystemThresholdSerializer()
    heart_rate_thresholds = SystemThresholdSerializer()
    alert_settings = serializers.DictField()
    notification_settings = serializers.DictField()
    device_settings = serializers.DictField()
    analytics_settings = serializers.DictField()