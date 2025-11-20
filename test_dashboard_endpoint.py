"""
Script para probar el endpoint del dashboard
"""
import os
import django
import sys

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from apps.users.models import CustomUser

# Crear cliente de prueba
client = APIClient()

# Intentar obtener un usuario para autenticación
try:
    user = CustomUser.objects.filter(is_active=True).first()
    if user:
        print(f"✓ Usuario encontrado: {user.email} (rol: {user.role})")
        
        # Autenticar el cliente
        client.force_authenticate(user=user)
        
        # Probar el endpoint
        print("\n🔍 Probando endpoint: /api/dashboard/stats/")
        response = client.get('/api/dashboard/stats/', HTTP_HOST='localhost')
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📄 Response Data:")
        if hasattr(response, 'data'):
            print(response.data)
        else:
            print(response.content.decode() if response.content else 'No content')
        
        if response.status_code == 200:
            print("\n✅ Endpoint funcionando correctamente!")
        else:
            print(f"\n❌ Error: {response.status_code}")
            
    else:
        print("❌ No se encontraron usuarios en la base de datos")
        print("💡 Ejecuta: python manage.py createsuperuser")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
