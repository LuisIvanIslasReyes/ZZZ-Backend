from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo CustomUser (lectura).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'supervisor', 'admin',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear usuarios.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role',
            'supervisor', 'admin'
        ]
    
    def validate(self, attrs):
        """
        Validar que las contraseñas coincidan y la jerarquía sea correcta.
        """
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Las contraseñas no coinciden'})
        
        role = attrs.get('role')
        supervisor = attrs.get('supervisor')
        admin = attrs.get('admin')
        
        # Validar jerarquía
        if role == 'employee' and not supervisor:
            raise serializers.ValidationError({'supervisor': 'Los empleados deben tener un supervisor asignado'})
        
        if role == 'supervisor' and not admin:
            raise serializers.ValidationError({'admin': 'Los supervisores deben tener un administrador asignado'})
        
        if role == 'admin' and (supervisor or admin):
            raise serializers.ValidationError('Los administradores no deben tener supervisor ni admin asignado')
        
        return attrs
    
    def create(self, validated_data):
        """
        Crear usuario con contraseña hasheada.
        """
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar usuarios (sin cambiar contraseña).
    """
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'role',
            'supervisor', 'admin', 'is_active'
        ]
    
    def validate(self, attrs):
        """
        Validar jerarquía al actualizar.
        """
        instance = self.instance
        role = attrs.get('role', instance.role)
        supervisor = attrs.get('supervisor', instance.supervisor)
        admin = attrs.get('admin', instance.admin)
        
        # Validar jerarquía
        if role == 'employee' and admin:
            attrs['admin'] = None
        
        if role == 'supervisor' and supervisor:
            attrs['supervisor'] = None
        
        if role == 'admin':
            attrs['supervisor'] = None
            attrs['admin'] = None
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar contraseña.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, write_only=True, min_length=8)
    
    def validate_old_password(self, value):
        """
        Validar que la contraseña actual sea correcta.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta')
        return value
    
    def validate(self, attrs):
        """
        Validar que las nuevas contraseñas coincidan.
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Las contraseñas no coinciden'})
        return attrs
    
    def save(self):
        """
        Cambiar la contraseña del usuario.
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login de usuarios.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """
        Validar credenciales del usuario.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError('Credenciales inválidas')
            
            if not user.is_active:
                raise serializers.ValidationError('Usuario inactivo')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Debe incluir email y contraseña')


class EmployeeListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar empleados (para supervisores).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'is_active', 'created_at']
        read_only_fields = fields


class SupervisorListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar supervisores (para admins).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'employee_count', 'is_active', 'created_at']
        read_only_fields = fields
    
    def get_employee_count(self, obj):
        """
        Retorna el número de empleados supervisados.
        """
        return obj.employees.filter(is_active=True).count()
