"""
Serializers para gestión de sesiones de simuladores.
"""
from rest_framework import serializers
from apps.analytics.simulator_models import SimulatorSession
from apps.users.models import CustomUser


class SimulatorSessionListSerializer(serializers.ModelSerializer):
    """Serializer para listar sesiones de simuladores."""
    
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fatigue_profile_display = serializers.CharField(source='get_fatigue_profile_display', read_only=True)
    activity_mode_display = serializers.CharField(source='get_activity_mode_display', read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = SimulatorSession
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'device_id', 'status', 'status_display',
            'fatigue_profile', 'fatigue_profile_display',
            'activity_mode', 'activity_mode_display',
            'current_fatigue', 'messages_sent',
            'started_at', 'stopped_at', 'duration_seconds',
        ]
    
    def get_duration_seconds(self, obj):
        """Calcula duración en segundos."""
        from django.utils import timezone
        if obj.stopped_at:
            delta = obj.stopped_at - obj.started_at
        else:
            delta = timezone.now() - obj.started_at
        return int(delta.total_seconds())


class SimulatorSessionDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para sesiones."""
    
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    config = serializers.SerializerMethodField()
    
    class Meta:
        model = SimulatorSession
        fields = '__all__'
    
    def get_config(self, obj):
        """Retorna configuración completa."""
        return obj.get_config_dict()


class SimulatorSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear sesiones de simuladores."""
    
    class Meta:
        model = SimulatorSession
        fields = [
            'employee', 'device_id', 'fatigue_profile', 'activity_mode',
            'base_heart_rate', 'base_spo2', 'initial_fatigue', 'fatigue_rate',
            'mqtt_broker', 'mqtt_port', 'publish_interval'
        ]
    
    def validate_employee(self, value):
        """Validar que el empleado exista y tenga rol employee."""
        if value.role != 'employee':
            raise serializers.ValidationError("El usuario debe tener rol de empleado")
        if not value.is_active:
            raise serializers.ValidationError("El empleado debe estar activo")
        return value
    
    def validate_device_id(self, value):
        """Validar formato de device_id."""
        if not value.startswith('ESP32-'):
            raise serializers.ValidationError("El device_id debe comenzar con 'ESP32-'")
        return value
    
    def validate_initial_fatigue(self, value):
        """Validar rango de fatiga inicial."""
        if not 0 <= value <= 100:
            raise serializers.ValidationError("La fatiga debe estar entre 0 y 100")
        return value
    
    def validate(self, attrs):
        """Validaciones cruzadas."""
        # Verificar que no exista una sesión activa para este empleado
        employee = attrs['employee']
        active_session = SimulatorSession.objects.filter(
            employee=employee,
            status='running'
        ).exists()
        
        if active_session:
            raise serializers.ValidationError({
                'employee': 'Ya existe un simulador activo para este empleado'
            })
        
        # Ajustar fatiga inicial según perfil
        profile = attrs.get('fatigue_profile', 'normal')
        fatigue_ranges = {
            'rested': (0, 30),
            'normal': (30, 50),
            'tired': (50, 70),
            'fatigued': (70, 85),
            'critical': (85, 100),
        }
        
        if profile in fatigue_ranges:
            min_f, max_f = fatigue_ranges[profile]
            if 'initial_fatigue' not in attrs:
                # Usar punto medio del rango
                attrs['initial_fatigue'] = (min_f + max_f) / 2
        
        return attrs
    
    def create(self, validated_data):
        """Crear sesión y registrar quién la creó."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class SimulatorSessionUpdateConfigSerializer(serializers.Serializer):
    """Serializer para actualizar configuración en caliente."""
    
    # Mapeo de valores en español a inglés
    ACTIVITY_TRANSLATION = {
        'reposo': 'rest',
        'ligera': 'light',
        'moderada': 'moderate',
        'intensa': 'intense',
        # También aceptar valores en inglés
        'rest': 'rest',
        'light': 'light',
        'moderate': 'moderate',
        'intense': 'intense'
    }
    
    activity_mode = serializers.CharField(required=False)
    fatigue_level = serializers.FloatField(
        min_value=0,
        max_value=100,
        required=False
    )
    fatigue_rate = serializers.FloatField(
        min_value=0,
        max_value=10,
        required=False
    )
    
    def validate_activity_mode(self, value):
        """Traducir activity_mode de español a inglés si es necesario."""
        if not value:
            return value
        
        # Convertir a minúsculas para comparar
        value_lower = value.lower()
        
        # Traducir si está en el diccionario
        translated = self.ACTIVITY_TRANSLATION.get(value_lower)
        
        if not translated:
            valid_options = list(self.ACTIVITY_TRANSLATION.keys())
            raise serializers.ValidationError(
                f"'{value}' no es un modo de actividad válido. "
                f"Opciones válidas: {', '.join(valid_options)}"
            )
        
        return translated
    
    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Debe proporcionar al menos un parámetro para actualizar")
        return attrs


class EmployeeForSimulatorSerializer(serializers.ModelSerializer):
    """Serializer simple para listar empleados disponibles."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    has_active_simulator = serializers.SerializerMethodField()
    device_id = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'supervisor', 'supervisor_name',
            'has_active_simulator', 'device_id'
        ]
    
    def get_has_active_simulator(self, obj):
        """Verifica si tiene simulador activo."""
        return SimulatorSession.objects.filter(
            employee=obj,
            status='running'
        ).exists()
    
    def get_device_id(self, obj):
        """Obtiene device_id del dispositivo asignado o genera uno."""
        try:
            device = obj.assigned_device
            return device.device_id
        except:
            # Generar ID basado en employee ID
            return f"ESP32-{str(obj.id).zfill(3)}"


class SimulatorStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del simulador en tiempo real."""
    
    session_id = serializers.IntegerField()
    device_id = serializers.CharField()
    running = serializers.BooleanField()
    messages_sent = serializers.IntegerField()
    current_fatigue = serializers.FloatField()
    activity_mode = serializers.CharField()
