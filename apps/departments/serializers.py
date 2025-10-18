"""
Department serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Department, DepartmentMembership, WorkShift, ShiftAssignment

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    """Department serializer"""
    
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    parent_department_name = serializers.CharField(source='parent_department.name', read_only=True)
    employee_count = serializers.ReadOnlyField()
    sub_departments = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'description', 'code', 'parent_department',
            'parent_department_name', 'manager', 'manager_name',
            'employee_count', 'sub_departments', 'is_active',
            'location', 'email', 'phone', 'created_at', 'updated_at'
        ]


class DepartmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating departments"""
    
    class Meta:
        model = Department
        fields = [
            'name', 'description', 'code', 'parent_department',
            'manager', 'location', 'email', 'phone'
        ]


class DepartmentMembershipSerializer(serializers.ModelSerializer):
    """Department membership serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = DepartmentMembership
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'department', 'department_name', 'position',
            'is_primary', 'joined_at', 'left_at'
        ]
        read_only_fields = ['joined_at']


class WorkShiftSerializer(serializers.ModelSerializer):
    """Work shift serializer"""
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    duration_hours = serializers.ReadOnlyField()
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkShift
        fields = [
            'id', 'name', 'description', 'start_time', 'end_time',
            'work_days', 'department', 'department_name',
            'duration_hours', 'employee_count', 'is_active',
            'break_duration_minutes', 'created_at', 'updated_at'
        ]
    
    def get_employee_count(self, obj):
        return obj.employees.filter(shiftassignment__is_active=True).count()


class WorkShiftCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating work shifts"""
    
    class Meta:
        model = WorkShift
        fields = [
            'name', 'description', 'start_time', 'end_time',
            'work_days', 'department', 'break_duration_minutes'
        ]


class ShiftAssignmentSerializer(serializers.ModelSerializer):
    """Shift assignment serializer"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    shift_name = serializers.CharField(source='work_shift.name', read_only=True)
    department_name = serializers.CharField(source='work_shift.department.name', read_only=True)
    
    class Meta:
        model = ShiftAssignment
        fields = [
            'id', 'user', 'user_name', 'work_shift', 'shift_name',
            'department_name', 'start_date', 'end_date',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class DepartmentStatsSerializer(serializers.Serializer):
    """Serializer for department statistics"""
    
    department_id = serializers.IntegerField()
    department_name = serializers.CharField()
    total_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    avg_stress_level = serializers.FloatField()
    high_stress_employees = serializers.IntegerField()
    total_alerts = serializers.IntegerField()
    active_devices = serializers.IntegerField()
    
    # Analytics data
    stress_distribution = serializers.DictField()
    shift_performance = serializers.ListField()
    trends = serializers.DictField()