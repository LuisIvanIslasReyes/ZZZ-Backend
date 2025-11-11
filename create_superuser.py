import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import CustomUser

# Crear superusuario admin
if not CustomUser.objects.filter(email='admin@example.com').exists():
    admin = CustomUser.objects.create_superuser(
        email='admin@example.com',
        password='admin123',
        first_name='Admin',
        last_name='Principal',
        role='admin'
    )
    print(f"✅ Superusuario creado: {admin.email}")
    print(f"   Email: admin@example.com")
    print(f"   Password: admin123")
    print(f"   Rol: {admin.role}")
else:
    print("⚠️  El superusuario ya existe")
