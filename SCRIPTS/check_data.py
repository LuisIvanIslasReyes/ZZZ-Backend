import django
import os
import sys

# Agregar directorio raíz al path
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.sensors.models import ProcessedMetrics, SensorData
from apps.analytics.models import RoutineRecommendation

User = get_user_model()

users = User.objects.count()
employees = User.objects.filter(role='employee').count()
supervisors = User.objects.filter(role='supervisor').count()
sensor_data = SensorData.objects.count()
metrics = ProcessedMetrics.objects.count()
recommendations = RoutineRecommendation.objects.count()

print(f"Usuarios totales: {users}")
print(f"Supervisores: {supervisors}")
print(f"Empleados: {employees}")
print(f"Datos de sensores: {sensor_data}")
print(f"Métricas procesadas: {metrics}")
print(f"Recomendaciones: {recommendations}")

if metrics == 0:
    print("\n⚠️  No hay métricas procesadas. Generando datos...")
    sys.exit(1)
else:
    print(f"\n✅ Hay {metrics} métricas disponibles")
    sys.exit(0)
