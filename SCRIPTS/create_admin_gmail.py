import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser

# Crear o actualizar el usuario admin@gmail.com
email = 'admin@gmail.com'
password = 'cualquiera'

try:
    user = CustomUser.objects.get(email=email)
    user.set_password(password)
    user.is_active = True
    user.save()
    print(f"✅ Usuario actualizado: {email}")
    print(f"   Password: {password}")
    print(f"   Rol: {user.role}")
except CustomUser.DoesNotExist:
    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        first_name='Admin',
        last_name='Principal',
        role='admin',
        is_active=True
    )
    print(f"✅ Usuario creado: {email}")
    print(f"   Password: {password}")
    print(f"   Rol: {user.role}")
