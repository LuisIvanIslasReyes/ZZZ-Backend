"""
Serializers para alertas de fatiga y recomendaciones de rutinas.
"""

from rest_framework import serializers
from .models import FatigueAlert, RoutineRecommendation
from apps.users.models import CustomUser

class FatigueAlertListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar alertas (vista resumida).
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = FatigueAlert
        fields = [
            'id',
            'employee',
            'employee_name',
            'supervisor',
            'supervisor_name',
            'timestamp',
            'severity',
            'severity_display',
            'alert_type',
            'message',
            'fatigue_index',
            'is_acknowledged',
            'acknowledged_at',
            'is_resolved',
            'resolved_at',
            'created_at',
        ]
        read_only_fields = ['id', 'timestamp', 'created_at']


class FatigueAlertDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para alertas.
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    supervisor_email = serializers.EmailField(source='supervisor.email', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.get_full_name', read_only=True, allow_null=True)
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', read_only=True, allow_null=True)
    
    # Información adicional
    time_since_created = serializers.SerializerMethodField()
    time_to_resolve = serializers.SerializerMethodField()
    
    class Meta:
        model = FatigueAlert
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_email',
            'supervisor',
            'supervisor_name',
            'supervisor_email',
            'timestamp',
            'severity',
            'severity_display',
            'alert_type',
            'message',
            'fatigue_index',
            'is_acknowledged',
            'acknowledged_at',
            'acknowledged_by',
            'acknowledged_by_name',
            'is_resolved',
            'resolved_at',
            'resolved_by',
            'resolved_by_name',
            'created_at',
            'time_since_created',
            'time_to_resolve',
        ]
        read_only_fields = ['id', 'timestamp', 'created_at']
    
    def get_time_since_created(self, obj):
        """Tiempo transcurrido desde la creación."""
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        hours = delta.total_seconds() / 3600
        
        if hours < 1:
            return f"{int(delta.total_seconds() / 60)} minutos"
        elif hours < 24:
            return f"{int(hours)} horas"
        else:
            return f"{int(hours / 24)} días"
    
    def get_time_to_resolve(self, obj):
        """Tiempo que tomó resolver la alerta."""
        if obj.is_resolved and obj.resolved_at:
            delta = obj.resolved_at - obj.created_at
            minutes = delta.total_seconds() / 60
            
            if minutes < 60:
                return f"{int(minutes)} minutos"
            else:
                return f"{int(minutes / 60)} horas"
        return None


class FatigueAlertCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear alertas.
    """
    
    class Meta:
        model = FatigueAlert
        fields = [
            'employee',
            'supervisor',
            'severity',
            'alert_type',
            'message',
            'fatigue_index',
        ]
    
    def validate_employee(self, value):
        """Validar que el usuario sea un empleado."""
        if value.role != 'employee':
            raise serializers.ValidationError(
                "El usuario debe tener rol de 'Empleado'"
            )
        return value
    
    def validate_supervisor(self, value):
        """Validar que el usuario sea un supervisor."""
        if value.role != 'supervisor':
            raise serializers.ValidationError(
                "El usuario debe tener rol de 'Supervisor'"
            )
        return value
    
    def validate(self, data):
        """Validar relaciones entre employee y supervisor."""
        employee = data.get('employee')
        supervisor = data.get('supervisor')
        
        # Validar que el employee pertenezca al supervisor
        if employee and supervisor:
            if hasattr(employee, 'supervisor') and employee.supervisor != supervisor:
                raise serializers.ValidationError(
                    f"El empleado '{employee.get_full_name()}' no pertenece al supervisor '{supervisor.get_full_name()}'"
                )
        
        return data


class FatigueAlertResolveSerializer(serializers.ModelSerializer):
    """
    Serializer para resolver alertas.
    """
    
    class Meta:
        model = FatigueAlert
        fields = ['is_resolved', 'resolved_at', 'resolved_by']
        read_only_fields = ['resolved_at', 'resolved_by']
    
    def validate_is_resolved(self, value):
        """Solo permitir marcar como resuelto (True)."""
        if not value:
            raise serializers.ValidationError(
                "Use este endpoint solo para marcar como resuelto. Para reabrir, use unresolve."
            )
        return value
    
    def update(self, instance, validated_data):
        """Actualizar los campos de resolución."""
        from django.utils import timezone
        instance.is_resolved = validated_data.get('is_resolved', instance.is_resolved)
        if instance.is_resolved and not instance.resolved_at:
            instance.resolved_at = timezone.now()
            instance.resolved_by = self.context['request'].user
        instance.save()
        return instance


class RoutineRecommendationListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar recomendaciones (vista resumida).
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    recommendation_type_display = serializers.CharField(source='get_recommendation_type_display', read_only=True)
    
    class Meta:
        model = RoutineRecommendation
        fields = [
            'id',
            'employee',
            'employee_name',
            'supervisor',
            'supervisor_name',
            'recommendation_type',
            'recommendation_type_display',
            'description',
            'priority',
            'is_applied',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class RoutineRecommendationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para recomendaciones.
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    supervisor_name = serializers.CharField(source='supervisor.get_full_name', read_only=True)
    supervisor_email = serializers.EmailField(source='supervisor.email', read_only=True)
    recommendation_type_display = serializers.CharField(source='get_recommendation_type_display', read_only=True)
    
    # Información adicional
    time_since_created = serializers.SerializerMethodField()
    time_to_apply = serializers.SerializerMethodField()
    
    class Meta:
        model = RoutineRecommendation
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_email',
            'supervisor',
            'supervisor_name',
            'supervisor_email',
            'recommendation_type',
            'recommendation_type_display',
            'description',
            'priority',
            'based_on_data',
            'is_applied',
            'applied_at',
            'created_at',
            'updated_at',
            'time_since_created',
            'time_to_apply',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_time_since_created(self, obj):
        """Tiempo transcurrido desde la creación."""
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        hours = delta.total_seconds() / 3600
        
        if hours < 1:
            return f"{int(delta.total_seconds() / 60)} minutos"
        elif hours < 24:
            return f"{int(hours)} horas"
        else:
            return f"{int(hours / 24)} días"
    
    def get_time_to_apply(self, obj):
        """Tiempo que tomó aplicar la recomendación."""
        if obj.is_applied and obj.applied_at:
            delta = obj.applied_at - obj.created_at
            hours = delta.total_seconds() / 3600
            
            if hours < 24:
                return f"{int(hours)} horas"
            else:
                return f"{int(hours / 24)} días"
        return None


class RoutineRecommendationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear recomendaciones.
    """
    
    class Meta:
        model = RoutineRecommendation
        fields = [
            'employee',
            'supervisor',
            'recommendation_type',
            'description',
            'priority',
            'based_on_data',
        ]
    
    def validate_employee(self, value):
        """Validar que el usuario sea un empleado."""
        if value.role != 'employee':
            raise serializers.ValidationError(
                "El usuario debe tener rol de 'Empleado'"
            )
        return value
    
    def validate_supervisor(self, value):
        """Validar que el usuario sea un supervisor."""
        if value.role != 'supervisor':
            raise serializers.ValidationError(
                "El usuario debe tener rol de 'Supervisor'"
            )
        return value
    
    def validate(self, data):
        """Validar que el employee pertenezca al supervisor."""
        employee = data.get('employee')
        supervisor = data.get('supervisor')
        
        if employee and supervisor:
            if hasattr(employee, 'supervisor') and employee.supervisor != supervisor:
                raise serializers.ValidationError(
                    f"El empleado '{employee.get_full_name()}' no pertenece al supervisor '{supervisor.get_full_name()}'"
                )
        
        return data


class RoutineRecommendationApplySerializer(serializers.ModelSerializer):
    """
    Serializer para aplicar recomendaciones.
    """
    
    class Meta:
        model = RoutineRecommendation
        fields = ['is_applied', 'applied_at']
        read_only_fields = ['applied_at']
    
    def update(self, instance, validated_data):
        """Actualizar los campos de aplicación."""
        from django.utils import timezone
        instance.is_applied = validated_data.get('is_applied', instance.is_applied)
        if instance.is_applied and not instance.applied_at:
            instance.applied_at = timezone.now()
        instance.save()
        return instance


class AlertStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de alertas.
    """
    total = serializers.IntegerField()
    resolved = serializers.IntegerField()
    unresolved = serializers.IntegerField()
    by_severity = serializers.DictField()
    avg_resolution_time_minutes = serializers.FloatField(allow_null=True)


class RecommendationStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de recomendaciones.
    """
    total = serializers.IntegerField()
    applied = serializers.IntegerField()
    rejected = serializers.IntegerField()
    pending = serializers.IntegerField()
    by_type = serializers.DictField()
    avg_application_time_hours = serializers.FloatField(allow_null=True)
