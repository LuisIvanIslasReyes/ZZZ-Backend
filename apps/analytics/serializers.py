"""
Serializers para alertas de fatiga y recomendaciones de rutinas.
"""

from rest_framework import serializers
from .models import FatigueAlert, RoutineRecommendation, SymptomReport, ScheduledBreak
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


# ==================== SYMPTOM REPORT SERIALIZERS ====================

class SymptomReportCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear reportes de síntomas (empleado).
    
    Lógica automática:
    - Si severidad es 'severe': Auto-aprobar y generar alerta crítica
    - Notificar al supervisor del nuevo reporte
    """
    class Meta:
        model = SymptomReport
        fields = ['symptom_type', 'severity', 'description']
    
    def create(self, validated_data):
        from django.utils import timezone
        from apps.analytics.models import FatigueAlert
        
        # Asignar automáticamente el empleado autenticado
        employee = self.context['request'].user
        validated_data['employee'] = employee
        
        severity = validated_data.get('severity')
        
        # Auto-aprobar síntomas severos
        if severity == 'severe':
            validated_data['is_reviewed'] = True
            validated_data['reviewed_at'] = timezone.now()
            validated_data['reviewed_by'] = employee.supervisor if hasattr(employee, 'supervisor') else None
            validated_data['notes'] = '⚠️ Síntoma severo - Auto-aprobado automáticamente. Se recomienda atención inmediata.'
            
        symptom_report = super().create(validated_data)
        
        # Si es severo, crear alerta crítica (solo si el empleado tiene supervisor)
        if severity == 'severe' and hasattr(employee, 'supervisor') and employee.supervisor:
            FatigueAlert.objects.create(
                employee=employee,
                supervisor=employee.supervisor,
                severity='high',
                alert_type='symptom_report',
                message=f'⚠️ URGENTE: {employee.get_full_name()} reportó síntoma severo: {symptom_report.get_symptom_type_display()}',
                fatigue_index=0.0,  # No aplica para reportes de síntomas
                is_resolved=False
            )
        
        # TODO: Enviar notificación al supervisor (implementar con websockets o email)
        # self._notify_supervisor(employee, symptom_report)
        
        return symptom_report


class SymptomReportListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar reportes de síntomas.
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    symptom_type_display = serializers.CharField(source='get_symptom_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = SymptomReport
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_email',
            'symptom_type',
            'symptom_type_display',
            'severity',
            'severity_display',
            'description',
            'is_reviewed',
            'reviewed_at',
            'reviewed_by',
            'reviewed_by_name',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SymptomReportReviewSerializer(serializers.ModelSerializer):
    """
    Serializer para que el supervisor revise un reporte de síntoma.
    """
    class Meta:
        model = SymptomReport
        fields = ['notes']
    
    def update(self, instance, validated_data):
        from django.utils import timezone
        instance.is_reviewed = True
        instance.reviewed_at = timezone.now()
        instance.reviewed_by = self.context['request'].user
        instance.notes = validated_data.get('notes', instance.notes)
        instance.save()
        return instance


# ==================== SCHEDULED BREAK SERIALIZERS ====================

class ScheduledBreakCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear descansos programados (empleado).
    """
    class Meta:
        model = ScheduledBreak
        fields = ['break_type', 'scheduled_date', 'scheduled_time', 'duration_minutes', 'reason']
    
    def validate_scheduled_date(self, value):
        """Validar que la fecha no sea en el pasado."""
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("No puedes programar un descanso en una fecha pasada.")
        return value
    
    def validate(self, data):
        """Validar fecha y hora combinadas."""
        from datetime import datetime, date
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')
        
        if scheduled_date and scheduled_time:
            scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
            if scheduled_date == date.today() and scheduled_datetime < datetime.now():
                raise serializers.ValidationError({
                    'scheduled_time': 'No puedes programar un descanso en una hora pasada.'
                })
        return data
    
    def create(self, validated_data):
        # Asignar automáticamente el empleado autenticado
        validated_data['employee'] = self.context['request'].user
        return super().create(validated_data)


class ScheduledBreakListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar descansos programados.
    """
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    break_type_display = serializers.CharField(source='get_break_type_display', read_only=True)
    duration_display = serializers.CharField(source='get_duration_minutes_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = ScheduledBreak
        fields = [
            'id',
            'employee',
            'employee_name',
            'employee_email',
            'break_type',
            'break_type_display',
            'scheduled_date',
            'scheduled_time',
            'duration_minutes',
            'duration_display',
            'reason',
            'status',
            'status_display',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'reviewer_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ScheduledBreakReviewSerializer(serializers.ModelSerializer):
    """
    Serializer para que el supervisor revise un descanso programado.
    """
    status = serializers.ChoiceField(choices=[('approved', 'Aprobado'), ('rejected', 'Rechazado')])
    
    class Meta:
        model = ScheduledBreak
        fields = ['status', 'reviewer_notes']
    
    def update(self, instance, validated_data):
        from django.utils import timezone
        
        if instance.status != 'pending':
            raise serializers.ValidationError("Solo se pueden revisar descansos pendientes.")
        
        instance.status = validated_data.get('status')
        instance.reviewed_at = timezone.now()
        instance.reviewed_by = self.context['request'].user
        instance.reviewer_notes = validated_data.get('reviewer_notes', instance.reviewer_notes)
        instance.save()
        return instance


class ScheduledBreakUpdateStatusSerializer(serializers.ModelSerializer):
    """
    Serializer para que el empleado actualice el estado de su descanso.
    """
    status = serializers.ChoiceField(choices=[('completed', 'Completado'), ('cancelled', 'Cancelado')])
    
    class Meta:
        model = ScheduledBreak
        fields = ['status']
    
    def update(self, instance, validated_data):
        new_status = validated_data.get('status')
        
        # Validar que el descanso sea del empleado autenticado
        if instance.employee != self.context['request'].user:
            raise serializers.ValidationError("No tienes permiso para modificar este descanso.")
        
        # Solo puede cancelar si está pendiente, o completar si está aprobado
        if new_status == 'cancelled' and instance.status not in ['pending', 'approved']:
            raise serializers.ValidationError("Solo puedes cancelar descansos pendientes o aprobados.")
        
        if new_status == 'completed' and instance.status != 'approved':
            raise serializers.ValidationError("Solo puedes marcar como completado un descanso aprobado.")
        
        instance.status = new_status
        instance.save()
        return instance
