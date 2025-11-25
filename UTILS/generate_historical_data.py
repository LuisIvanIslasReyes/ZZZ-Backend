"""
Script para generar datos de prueba con fechas históricas
Esto crea métricas procesadas para los últimos 7 días
"""

import os
import django
from datetime import datetime, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.sensors.models import ProcessedMetrics
from apps.devices.models import Device
from apps.users.models import CustomUser

print("=" * 60)
print("GENERADOR DE DATOS DE PRUEBA PARA GRÁFICAS")
print("=" * 60)

# Obtener dispositivos activos
devices = Device.objects.filter(is_active=True)

if not devices.exists():
    print("❌ No hay dispositivos activos")
    exit()

print(f"\n📱 Dispositivos encontrados: {devices.count()}")

# Generar datos para los últimos 7 días
now = timezone.now()
days_back = 7

total_created = 0

for device in devices:
    employee = device.employee
    print(f"\n🔄 Generando datos para: {employee.get_full_name()} ({employee.email})")
    
    for day_offset in range(days_back):
        # Fecha del día
        target_date = now - timedelta(days=day_offset)
        
        # Generar entre 5-10 métricas por día (cada ~2-3 horas)
        metrics_per_day = random.randint(5, 10)
        
        for i in range(metrics_per_day):
            # Hora aleatoria del día
            hour = random.randint(8, 20)  # Entre 8 AM y 8 PM
            minute = random.randint(0, 59)
            
            window_start = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            window_end = window_start + timedelta(minutes=1)
            
            # Verificar si ya existe
            if ProcessedMetrics.objects.filter(
                device=device,
                window_start=window_start
            ).exists():
                continue
            
            # Generar valores realistas
            base_fatigue = 50 + (day_offset * 2)  # Aumenta con los días
            hr_base = 75 + random.randint(-10, 10)
            
            # Valores que varían según la hora del día
            hour_factor = 1.0
            if 8 <= hour <= 10:  # Mañana - baja fatiga
                hour_factor = 0.8
            elif 14 <= hour <= 16:  # Después del almuerzo - alta fatiga
                hour_factor = 1.3
            elif 18 <= hour <= 20:  # Tarde - fatiga moderada-alta
                hour_factor = 1.2
            
            fatigue_index = min(100, base_fatigue * hour_factor + random.randint(-5, 5))
            hr_avg = hr_base + random.randint(-5, 5)
            spo2_avg = 97.0 + random.uniform(-1.0, 1.5)
            
            # Crear métrica
            ProcessedMetrics.objects.create(
                device=device,
                employee=employee,
                window_start=window_start,
                window_end=window_end,
                hr_avg=hr_avg,
                hr_max=hr_avg + random.randint(5, 15),
                hr_min=hr_avg - random.randint(5, 10),
                hrv_rmssd=random.uniform(20, 50),
                hrv_sdnn=random.uniform(15, 40),
                hr_trend='stable',
                spo2_avg=spo2_avg,
                spo2_min=spo2_avg - random.uniform(0.5, 2.0),
                spo2_variance=random.uniform(0.1, 1.0),
                desaturation_count=random.randint(0, 2),
                activity_level=random.uniform(0.5, 2.5),
                movement_variance=random.uniform(0.1, 0.5),
                movement_entropy=random.uniform(1.0, 3.0),
                fatigue_index=fatigue_index,
                hr_activity_ratio=hr_avg / 1.5,
            )
            
            total_created += 1
        
        print(f"  ✅ Día {day_offset + 1} ({target_date.strftime('%Y-%m-%d')}): {metrics_per_day} métricas")

print(f"\n{'=' * 60}")
print(f"✅ COMPLETADO")
print(f"{'=' * 60}")
print(f"📊 Total de métricas creadas: {total_created}")
print(f"📈 Total en BD: {ProcessedMetrics.objects.count()}")
print(f"\n🎉 Ahora las gráficas deberían mostrar datos de los últimos 7 días!")
