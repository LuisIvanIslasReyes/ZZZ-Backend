"""
Serializers for devices and sensors
"""
from rest_framework import serializers
from .models import Device, SensorPacket, SensorSample, StressAggregate
from django.utils import timezone


class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for Device model
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'employee', 'employee_name', 'device_type', 'hardware_id',
            'model_name', 'firmware_version', 'is_active', 'last_seen',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_seen']


class SensorSampleSerializer(serializers.ModelSerializer):
    """
    Serializer for SensorSample model
    """
    class Meta:
        model = SensorSample
        fields = [
            'id', 'sample_time', 'heart_rate', 'spo2',
            'accel_x', 'accel_y', 'accel_z', 'steps', 'battery_level'
        ]


class SensorPacketSerializer(serializers.ModelSerializer):
    """
    Serializer for SensorPacket model
    """
    samples = SensorSampleSerializer(many=True, read_only=True)
    
    class Meta:
        model = SensorPacket
        fields = [
            'id', 'device', 'received_at', 'packet_timestamp',
            'raw_payload', 'processed', 'samples'
        ]
        read_only_fields = ['id', 'received_at', 'processed']


class BatchSensorDataSerializer(serializers.Serializer):
    """
    Serializer for batch sensor data ingestion
    Expected format:
    {
        "device_id": "hardware_id",
        "firmware_version": "1.0.0",
        "samples": [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "hr": 75,
                "spo2": 98.5,
                "accel_x": 0.1,
                "accel_y": 0.2,
                "accel_z": 9.8,
                "steps": 1500,
                "battery": 85
            },
            ...
        ]
    }
    """
    device_id = serializers.CharField(required=True)
    firmware_version = serializers.CharField(required=False, allow_blank=True)
    samples = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        min_length=1,
        max_length=10000  # Limit batch size
    )
    
    def validate_device_id(self, value):
        """Validate that device exists"""
        if not Device.objects.filter(hardware_id=value, is_active=True).exists():
            raise serializers.ValidationError("Dispositivo no encontrado o inactivo")
        return value
    
    def validate_samples(self, value):
        """Validate sample structure"""
        required_fields = ['timestamp']
        for idx, sample in enumerate(value):
            for field in required_fields:
                if field not in sample:
                    raise serializers.ValidationError(
                        f"Sample {idx}: campo requerido '{field}' faltante"
                    )
        return value


class StressAggregateSerializer(serializers.ModelSerializer):
    """
    Serializer for StressAggregate model
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    
    class Meta:
        model = StressAggregate
        fields = [
            'id', 'employee', 'employee_name', 'window_start', 'window_end',
            'stress_score', 'confidence', 'avg_heart_rate',
            'heart_rate_variability', 'movement_intensity',
            'sample_count', 'method_version', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StressSummarySerializer(serializers.Serializer):
    """
    Serializer for stress summary statistics
    """
    avg_stress = serializers.FloatField()
    min_stress = serializers.FloatField()
    max_stress = serializers.FloatField()
    current_stress = serializers.FloatField()
    trend = serializers.CharField()  # 'increasing', 'decreasing', 'stable'
    data_points = serializers.IntegerField()
