from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo CustomUser (lectura).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'company', 'company_name', 'supervisor',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear usuarios.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8, required=False)
    supervisor = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='supervisor'),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role',
            'company', 'supervisor', 'phone', 'department', 'position'
        ]
    
    def validate(self, attrs):
        """
        Validar que las contraseñas coincidan y la jerarquía sea correcta.
        """
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)
        
        # Si se proporciona password_confirm, debe coincidir con password
        if password_confirm and password != password_confirm:
            raise serializers.ValidationError({'password': 'Las contraseñas no coinciden'})
        
        role = attrs.get('role')
        supervisor = attrs.get('supervisor')
        company = attrs.get('company')
        
        # Supervisores y empleados deben tener empresa
        if role in ['supervisor', 'employee'] and not company:
            raise serializers.ValidationError({'company': f'Los {role}s deben pertenecer a una empresa'})
        
        # Admins no deben tener empresa ni supervisor
        if role == 'admin' and (company or supervisor):
            raise serializers.ValidationError('Los administradores no deben tener empresa ni supervisor asignado')
        
        # Supervisores no deben tener supervisor asignado (son la empresa)
        if role == 'supervisor' and supervisor:
            attrs['supervisor'] = None
        
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
            'company', 'supervisor', 'is_active'
        ]
    
    def validate(self, attrs):
        """
        Validar jerarquía al actualizar.
        """
        instance = self.instance
        role = attrs.get('role', instance.role)
        supervisor = attrs.get('supervisor', instance.supervisor)
        company = attrs.get('company', instance.company)
        
        # Validar jerarquía
        if role == 'supervisor' and supervisor:
            attrs['supervisor'] = None
        
        if role == 'admin':
            attrs['supervisor'] = None
            attrs['company'] = None
        
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
    employee_id = serializers.SerializerMethodField()
    supervisor_name = serializers.SerializerMethodField()
    # Campos opcionales que pueden no existir en el modelo
    department = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    position = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    hire_date = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 
            'employee_id', 'role', 'supervisor', 'supervisor_name',
            'phone', 'department', 'position', 'hire_date',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'employee_id', 'supervisor_name']
    
    def get_employee_id(self, obj):
        """
        Genera un ID de empleado basado en el ID del usuario.
        """
        return f"EMP-{obj.id:04d}"
    
    def get_supervisor_name(self, obj):
        """
        Retorna el nombre completo del supervisor (el supervisor de la empresa).
        """
        if obj.supervisor:
            return obj.supervisor.get_full_name()
        # Si no tiene supervisor asignado pero tiene empresa, buscar el supervisor de la empresa
        if obj.company:
            company_supervisor = CustomUser.objects.filter(
                company=obj.company,
                role='supervisor',
                is_active=True
            ).first()
            if company_supervisor:
                return company_supervisor.get_full_name()
        return None


class SupervisorListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar supervisores (para admins).
    Nota: Los supervisores ahora son cuentas de empresa (1 por empresa).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    employee_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'company', 'company_name', 'employee_count', 'is_active', 'created_at']
        read_only_fields = fields
    
    def get_employee_count(self, obj):
        """
        Retorna el número de empleados de la empresa del supervisor.
        """
        if obj.company:
            return CustomUser.objects.filter(
                company=obj.company,
                role='employee',
                is_active=True
            ).count()
        return 0
