"""
Serializers para datos de sensores y métricas procesadas.
"""

from rest_framework import serializers
from .models import SensorData, ProcessedMetrics
from apps.devices.models import Device


class SensorDataListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar datos de sensores (vista resumida).
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    
    class Meta:
        model = SensorData
        fields = [
            'id',
            'device',
            'device_name',
            'device_id',
            'heart_rate',
            'spo2',
            'accel_x',
            'accel_y',
            'accel_z',
            'timestamp',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class SensorDataDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para datos de sensores.
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    employee_name = serializers.CharField(source='device.employee.get_full_name', read_only=True)
    
    # Calcular magnitud de aceleración
    acceleration_magnitude = serializers.SerializerMethodField()
    
    class Meta:
        model = SensorData
        fields = [
            'id',
            'device',
            'device_name',
            'device_id',
            'employee_name',
            'heart_rate',
            'spo2',
            'accel_x',
            'accel_y',
            'accel_z',
            'acceleration_magnitude',
            'timestamp',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_acceleration_magnitude(self, obj):
        """Calcula la magnitud del vector de aceleración."""
        import math
        return round(math.sqrt(obj.accel_x**2 + obj.accel_y**2 + obj.accel_z**2), 3)


class SensorDataCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear datos de sensores.
    Usado por el cliente MQTT y simuladores.
    """
    
    class Meta:
        model = SensorData
        fields = [
            'device',
            'heart_rate',
            'spo2',
            'accel_x',
            'accel_y',
            'accel_z',
            'timestamp',
        ]
    
    def validate_heart_rate(self, value):
        """Validar rango de frecuencia cardíaca."""
        if value < 30 or value > 220:
            raise serializers.ValidationError(
                "Frecuencia cardíaca fuera de rango válido (30-220 bpm)"
            )
        return value
    
    def validate_spo2(self, value):
        """Validar rango de SpO2."""
        if value < 70 or value > 100:
            raise serializers.ValidationError(
                "SpO2 fuera de rango válido (70-100%)"
            )
        return value
    
    def validate_device(self, value):
        """Validar que el dispositivo esté activo."""
        if not value.is_active:
            raise serializers.ValidationError(
                f"El dispositivo '{value.device_id}' está inactivo"
            )
        return value


class ProcessedMetricsListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar métricas procesadas (vista resumida).
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    fatigue_severity = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessedMetrics
        fields = [
            'id',
            'device',
            'device_name',
            'device_id',
            'employee',
            'employee_name',
            'window_start',
            'window_end',
            'hr_avg',
            'spo2_avg',
            'activity_level',
            'fatigue_index',
            'fatigue_severity',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_fatigue_severity(self, obj):
        """Clasifica el nivel de fatiga."""
        if obj.fatigue_index < 40:
            return 'low'
        elif obj.fatigue_index < 70:
            return 'medium'
        else:
            return 'high'


class ProcessedMetricsDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para métricas procesadas.
    Incluye todos los campos calculados.
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_id = serializers.CharField(source='device.device_id', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    fatigue_severity = serializers.SerializerMethodField()
    window_duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessedMetrics
        fields = [
            'id',
            'device',
            'device_name',
            'device_id',
            'employee',
            'employee_name',
            'employee_email',
            'window_start',
            'window_end',
            'window_duration_minutes',
            # Heart Rate metrics
            'hr_avg',
            'hr_max',
            'hr_min',
            'hrv_rmssd',
            'hrv_sdnn',
            'hr_trend',
            # SpO2 metrics
            'spo2_avg',
            'spo2_min',
            'spo2_variance',
            'desaturation_count',
            # Activity metrics
            'activity_level',
            'movement_variance',
            'movement_entropy',
            # Combined metrics
            'fatigue_index',
            'fatigue_severity',
            'hr_activity_ratio',
            'recovery_time',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_fatigue_severity(self, obj):
        """Clasifica el nivel de fatiga."""
        if obj.fatigue_index < 40:
            return 'low'
        elif obj.fatigue_index < 70:
            return 'medium'
        else:
            return 'high'
    
    def get_window_duration_minutes(self, obj):
        """Calcula la duración de la ventana en minutos."""
        if obj.window_start and obj.window_end:
            duration = obj.window_end - obj.window_start
            return round(duration.total_seconds() / 60, 2)
        return None


class ProcessedMetricsStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas agregadas de métricas.
    """
    period = serializers.CharField()
    avg_fatigue_index = serializers.FloatField()
    max_fatigue_index = serializers.FloatField()
    min_fatigue_index = serializers.FloatField()
    avg_heart_rate = serializers.FloatField()
    avg_spo2 = serializers.FloatField()
    total_desaturations = serializers.IntegerField()
    high_fatigue_count = serializers.IntegerField()
    medium_fatigue_count = serializers.IntegerField()
    low_fatigue_count = serializers.IntegerField()


class SensorDataBulkCreateSerializer(serializers.Serializer):
    """
    Serializer para crear múltiples registros de sensores a la vez.
    Útil para batch processing.
    """
    device_id = serializers.CharField()
    data = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=1000
    )
    
    def validate_device_id(self, value):
        """Validar que el dispositivo exista."""
        try:
            device = Device.objects.get(device_id=value, is_active=True)
        except Device.DoesNotExist:
            raise serializers.ValidationError(
                f"No existe un dispositivo activo con ID '{value}'"
            )
        return value
    
    def validate_data(self, value):
        """Validar estructura de cada registro."""
        required_fields = ['heart_rate', 'spo2', 'accel_x', 'accel_y', 'accel_z', 'timestamp']
        
        for i, record in enumerate(value):
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                raise serializers.ValidationError(
                    f"Registro {i+1}: faltan campos {missing_fields}"
                )
        
        return value
    
    def create(self, validated_data):
        """Crear múltiples registros de sensores."""
        device = Device.objects.get(device_id=validated_data['device_id'])
        sensor_data_list = []
        
        for record in validated_data['data']:
            sensor_data_list.append(
                SensorData(
                    device=device,
                    heart_rate=record['heart_rate'],
                    spo2=record['spo2'],
                    accel_x=record['accel_x'],
                    accel_y=record['accel_y'],
                    accel_z=record['accel_z'],
                    timestamp=record['timestamp']
                )
            )
        
        created = SensorData.objects.bulk_create(sensor_data_list)
        return {'created_count': len(created)}
