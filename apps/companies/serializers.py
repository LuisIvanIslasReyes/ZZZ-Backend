from rest_framework import serializers
from .models import Company
from apps.users.models import CustomUser


class CompanySerializer(serializers.ModelSerializer):
    """Serializer para listar y crear empresas"""
    employee_count = serializers.ReadOnlyField()
    supervisor_count = serializers.ReadOnlyField()
    is_subscription_active = serializers.ReadOnlyField()
    
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'contact_email',
            'contact_phone',
            'address',
            'is_active',
            'subscription_start',
            'subscription_end',
            'max_employees',
            'employee_count',
            'supervisor_count',
            'is_subscription_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para una empresa específica"""
    employee_count = serializers.ReadOnlyField()
    supervisor_count = serializers.ReadOnlyField()
    is_subscription_active = serializers.ReadOnlyField()
    
    supervisors = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'contact_email',
            'contact_phone',
            'address',
            'is_active',
            'subscription_start',
            'subscription_end',
            'max_employees',
            'employee_count',
            'supervisor_count',
            'is_subscription_active',
            'supervisors',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_supervisors(self, obj):
        """Retorna lista de supervisores de la empresa"""
        supervisors = CustomUser.objects.filter(
            company=obj,
            role='supervisor'
        )
        return [{
            'id': s.id,
            'email': s.email,
            'full_name': s.get_full_name(),
            'is_active': s.is_active
        } for s in supervisors]


class CompanyStatsSerializer(serializers.ModelSerializer):
    """Serializer con estadísticas de la empresa"""
    employee_count = serializers.ReadOnlyField()
    supervisor_count = serializers.ReadOnlyField()
    is_subscription_active = serializers.ReadOnlyField()
    
    active_devices = serializers.SerializerMethodField()
    active_alerts = serializers.SerializerMethodField()
    avg_fatigue_index = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'employee_count',
            'supervisor_count',
            'active_devices',
            'active_alerts',
            'avg_fatigue_index',
            'is_subscription_active',
            'subscription_end'
        ]
    
    def get_active_devices(self, obj):
        """Número de dispositivos activos"""
        from apps.devices.models import Device
        return Device.objects.filter(company=obj, is_active=True).count()
    
    def get_active_alerts(self, obj):
        """Número de alertas activas"""
        from apps.analytics.models import FatigueAlert
        return FatigueAlert.objects.filter(
            employee__company=obj,
            is_resolved=False
        ).count()
    
    def get_avg_fatigue_index(self, obj):
        """Índice de fatiga promedio de empleados"""
        from apps.sensors.models import ProcessedMetrics
        from django.db.models import Avg
        from datetime import timedelta
        from django.utils import timezone
        
        recent_time = timezone.now() - timedelta(hours=1)
        avg = ProcessedMetrics.objects.filter(
            employee__company=obj,
            window_start__gte=recent_time
        ).aggregate(avg_fatigue=Avg('fatigue_index'))
        
        return round(avg['avg_fatigue'], 2) if avg['avg_fatigue'] else 0
