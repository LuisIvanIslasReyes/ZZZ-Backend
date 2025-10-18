"""
Serializers for authentication
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Employee

User = get_user_model()


class EmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer for Employee profile
    """
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'position', 'department',
            'supervisor', 'phone', 'timezone', 'notifications_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    """
    employee_profile = EmployeeSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'employee_profile', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    employee_id = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'employee_id'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        employee_id = validated_data.pop('employee_id')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Create employee profile
        Employee.objects.create(
            user=user,
            employee_id=employee_id
        )
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("Las contraseñas nuevas no coinciden")
        return data


class FCMTokenSerializer(serializers.Serializer):
    """
    Serializer for FCM token registration
    """
    fcm_token = serializers.CharField(required=True)
