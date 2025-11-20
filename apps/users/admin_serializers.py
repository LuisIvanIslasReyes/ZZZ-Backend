# apps/users/admin_serializers.py
"""
Serializers para el panel de administración.
Permiten gestionar supervisores y visualizar estadísticas del sistema.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from apps.devices.models import Device
from apps.sensors.models import ProcessedMetrics
from apps.analytics.models import FatigueAlert, RoutineRecommendation

User = get_user_model()


class SupervisorListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar supervisores con información resumida.
    """
    full_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    employees_count = serializers.SerializerMethodField()
    active_alerts_count = serializers.SerializerMethodField()
    devices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'company',
            'company_name',
            'is_active',
            'employees_count',
            'devices_count',
            'active_alerts_count',
            'created_at',
            'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'last_login']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_employees_count(self, obj):
        """Cantidad de empleados bajo su supervisión."""
        return obj.employees.count()
    
    def get_devices_count(self, obj):
        """Cantidad de dispositivos que gestiona."""
        return Device.objects.filter(supervisor=obj).count()
    
    def get_active_alerts_count(self, obj):
        """Alertas activas de sus empleados."""
        return FatigueAlert.objects.filter(
            supervisor=obj,
            is_resolved=False
        ).count()


class SupervisorDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para un supervisor específico.
    Incluye lista de empleados y estadísticas completas.
    """
    full_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    employees = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'company',
            'company_name',
            'is_active',
            'created_at',
            'updated_at',
            'last_login',
            'employees',
            'statistics',
            'recent_activity'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_employees(self, obj):
        """Lista de empleados con información básica."""
        employees = obj.employees.all()
        return [
            {
                'id': emp.id,
                'email': emp.email,
                'full_name': f"{emp.first_name} {emp.last_name}".strip(),
                'is_active': emp.is_active,
                'has_device': hasattr(emp, 'device') and emp.device is not None
            }
            for emp in employees
        ]
    
    def get_statistics(self, obj):
        """Estadísticas del supervisor."""
        employees = obj.employees.all()
        employee_ids = [emp.id for emp in employees]
        
        # Alertas
        total_alerts = FatigueAlert.objects.filter(supervisor=obj).count()
        active_alerts = FatigueAlert.objects.filter(
            supervisor=obj,
            is_resolved=False
        ).count()
        resolved_alerts = total_alerts - active_alerts
        
        # Dispositivos
        total_devices = Device.objects.filter(supervisor=obj).count()
        active_devices = Device.objects.filter(
            supervisor=obj,
            is_active=True
        ).count()
        
        # Recomendaciones
        total_recommendations = RoutineRecommendation.objects.filter(
            supervisor=obj
        ).count()
        applied_recommendations = RoutineRecommendation.objects.filter(
            supervisor=obj,
            is_applied=True
        ).count()
        
        # Métricas promedio de empleados
        avg_metrics = ProcessedMetrics.objects.filter(
            employee_id__in=employee_ids
        ).aggregate(
            avg_fatigue=Avg('fatigue_index'),
            avg_hr=Avg('hr_avg'),
            avg_spo2=Avg('spo2_avg')
        )
        
        return {
            'employees_count': len(employee_ids),
            'devices': {
                'total': total_devices,
                'active': active_devices,
                'inactive': total_devices - active_devices
            },
            'alerts': {
                'total': total_alerts,
                'active': active_alerts,
                'resolved': resolved_alerts
            },
            'recommendations': {
                'total': total_recommendations,
                'applied': applied_recommendations,
                'pending': total_recommendations - applied_recommendations
            },
            'average_metrics': {
                'fatigue_index': round(avg_metrics['avg_fatigue'] or 0, 2),
                'heart_rate': round(avg_metrics['avg_hr'] or 0, 2),
                'spo2': round(avg_metrics['avg_spo2'] or 0, 2)
            }
        }
    
    def get_recent_activity(self, obj):
        """Actividad reciente del supervisor."""
        # Últimas 5 alertas resueltas
        recent_resolved_alerts = FatigueAlert.objects.filter(
            supervisor=obj,
            is_resolved=True,
            resolved_by=obj
        ).order_by('-resolved_at')[:5]
        
        # Últimas 5 recomendaciones aplicadas
        recent_recommendations = RoutineRecommendation.objects.filter(
            supervisor=obj,
            is_applied=True
        ).order_by('-applied_at')[:5]
        
        return {
            'resolved_alerts': [
                {
                    'id': alert.id,
                    'employee_name': f"{alert.employee.first_name} {alert.employee.last_name}",
                    'severity': alert.severity,
                    'resolved_at': alert.resolved_at
                }
                for alert in recent_resolved_alerts
            ],
            'applied_recommendations': [
                {
                    'id': rec.id,
                    'employee_name': f"{rec.employee.first_name} {rec.employee.last_name}",
                    'type': rec.recommendation_type,
                    'applied_at': rec.applied_at
                }
                for rec in recent_recommendations
            ]
        }


class SupervisorCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevos supervisores.
    Solo el admin puede crear supervisores.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'company',
            'is_active'
        ]
    
    def validate_email(self, value):
        """Validar que el email no exista."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado.")
        return value
    
    def validate(self, data):
        """Validar que las contraseñas coincidan y que company esté presente."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        
        if not data.get('company'):
            raise serializers.ValidationError({
                'company': 'Debe especificar una empresa para el supervisor.'
            })
        
        return data
    
    def create(self, validated_data):
        """Crear supervisor asociado a una empresa."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Establecer rol de supervisor
        validated_data['role'] = 'supervisor'
        
        # Crear usuario
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class SupervisorUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar información de supervisores.
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'company',
            'is_active'
        ]
    
    def update(self, instance, validated_data):
        """Actualizar supervisor."""
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance


class SystemStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas generales del sistema.
    Vista exclusiva para administradores.
    """
    users = serializers.DictField()
    devices = serializers.DictField()
    alerts = serializers.DictField()
    recommendations = serializers.DictField()
    metrics = serializers.DictField()
    activity = serializers.DictField()


class ActivityLogSerializer(serializers.Serializer):
    """
    Serializer para logs de actividad del sistema.
    Registra todas las acciones importantes.
    """
    id = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
    user = serializers.SerializerMethodField()
    action = serializers.CharField()
    resource_type = serializers.CharField()
    resource_id = serializers.IntegerField(allow_null=True)
    details = serializers.JSONField()
    ip_address = serializers.CharField(allow_null=True, allow_blank=True)
    
    def get_user(self, obj):
        """Información del usuario que realizó la acción."""
        if hasattr(obj, 'user') and obj.user:
            return {
                'id': obj.user.id,
                'email': obj.user.email,
                'full_name': f"{obj.user.first_name} {obj.user.last_name}".strip(),
                'role': obj.user.role
            }
        return None
