"""
Serializers para dispositivos ESP32.
"""

from rest_framework import serializers
from .models import Device
from apps.users.models import CustomUser


class DeviceListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar dispositivos (sin detalles completos).
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id',
            'device_identifier',
            'employee',
            'employee_name',
            'employee_email',
            'supervisor',
            'supervisor_name',
            'company',
            'company_name',
            'is_active',
            'last_connection',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'last_connection']


class DeviceDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para dispositivos (incluye información completa).
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_role = serializers.CharField(source='employee.get_role_display', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    supervisor_email = serializers.EmailField(source='supervisor.email', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    # Estadísticas adicionales
    total_sensor_data = serializers.SerializerMethodField()
    total_processed_metrics = serializers.SerializerMethodField()
    latest_fatigue_index = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id',
            'device_identifier',
            'employee',
            'employee_name',
            'employee_email',
            'employee_role',
            'supervisor',
            'supervisor_name',
            'supervisor_email',
            'company',
            'company_name',
            'is_active',
            'last_connection',
            'created_at',
            'updated_at',
            # Estadísticas
            'total_sensor_data',
            'total_processed_metrics',
            'latest_fatigue_index',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_connection']
    
    def get_total_sensor_data(self, obj):
        """Cuenta total de registros de sensores."""
        return obj.sensor_data.count()
    
    def get_total_processed_metrics(self, obj):
        """Cuenta total de métricas procesadas."""
        return obj.processed_metrics.count()
    
    def get_latest_fatigue_index(self, obj):
        """Último índice de fatiga registrado."""
        latest = obj.processed_metrics.order_by('-window_end').first()
        if latest:
            return {
                'value': latest.fatigue_index,
                'timestamp': latest.window_end,
                'severity': 'low' if latest.fatigue_index < 40 else 'medium' if latest.fatigue_index < 70 else 'high'
            }
        return None


class DeviceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear dispositivos.
    Valida que el empleado sea válido.
    El supervisor se asigna automáticamente desde el empleado.
    """
    
    class Meta:
        model = Device
        fields = [
            'device_identifier',
            'employee',
            'is_active',
        ]
    
    def validate_device_identifier(self, value):
        """Validar que el device_identifier sea único."""
        if Device.objects.filter(device_identifier=value).exists():
            raise serializers.ValidationError(
                f"Ya existe un dispositivo con el identificador '{value}'"
            )
        return value
    
    def validate_employee(self, value):
        """Validar que el usuario sea un empleado y tenga supervisor."""
        if value.role != 'employee':
            raise serializers.ValidationError(
                "El usuario debe tener rol de 'Empleado'"
            )
        
        # Verificar que el empleado tenga un supervisor asignado
        if not value.supervisor:
            raise serializers.ValidationError(
                f"El empleado '{value.get_full_name()}' no tiene un supervisor asignado. "
                "Debe asignarle un supervisor antes de crear un dispositivo."
            )
        
        # Verificar que el empleado no tenga ya un dispositivo asignado
        if hasattr(value, 'device') and value.device:
            raise serializers.ValidationError(
                f"El empleado '{value.get_full_name()}' ya tiene un dispositivo asignado"
            )
        
        return value


class DeviceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar dispositivos.
    Permite actualizar campos específicos sin requerir todos los datos.
    """
    
    class Meta:
        model = Device
        fields = [
            'employee',
            'supervisor',
            'is_active',
        ]
    
    def validate_employee(self, value):
        """Validar que el usuario sea un empleado."""
        if value and value.role != 'employee':
            raise serializers.ValidationError(
                "El usuario debe tener rol de 'Empleado'"
            )
        return value
    
    def validate_supervisor(self, value):
        """Validar que el usuario sea un supervisor."""
        if value and value.role != 'supervisor':
            raise serializers.ValidationError(
                "El usuario debe tener rol de 'Supervisor'"
            )
        return value
    
    def validate(self, data):
        """Validar que el empleado pertenezca al supervisor."""
        # Obtener valores actuales si no se proporcionan nuevos
        employee = data.get('employee', self.instance.employee)
        supervisor = data.get('supervisor', self.instance.supervisor)
        
        if employee and supervisor:
            if hasattr(employee, 'supervisor') and employee.supervisor != supervisor:
                raise serializers.ValidationError(
                    f"El empleado '{employee.get_full_name()}' no pertenece al "
                    f"supervisor '{supervisor.get_full_name()}'"
                )
        
        return data


class DeviceStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer simple para actualizar solo el estado del dispositivo.
    Útil para operaciones rápidas.
    """
    
    class Meta:
        model = Device
        fields = ['is_active']
