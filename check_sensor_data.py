"""Script para verificar datos de sensores guardados en BD."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sensors.models import SensorData
from apps.devices.models import Device
from django.utils import timezone
from datetime import timedelta

print("=" * 80)
print("📊 VERIFICACIÓN DE DATOS DE SENSORES EN BD")
print("=" * 80)

# Total de registros
total = SensorData.objects.count()
print(f"\n📈 Total de registros en SensorData: {total}")

if total == 0:
    print("\n⚠️  No hay datos aún. Espera unos segundos después de crear un simulador.")
    print("   Los datos se guardan cada 5 segundos.")
else:
    # Últimos 10 registros
    print(f"\n📋 Últimos 10 registros:")
    recent = SensorData.objects.all()[:10]
    
    for data in recent:
        print(f"\n   ┌─ {data.device.device_identifier} - {data.timestamp.strftime('%H:%M:%S')}")
        print(f"   │  ❤️  HR: {data.heart_rate:.1f} bpm")
        print(f"   │  🫁 SpO2: {data.spo2:.1f}%")
        print(f"   │  📊 Accel: X={data.accel_x:.2f}, Y={data.accel_y:.2f}, Z={data.accel_z:.2f}")
        print(f"   └{'─' * 75}")
    
    # Agrupar por dispositivo
    print(f"\n📊 Datos por dispositivo:")
    devices = Device.objects.all()
    for device in devices:
        count = SensorData.objects.filter(device=device).count()
        if count > 0:
            latest = SensorData.objects.filter(device=device).first()
            oldest = SensorData.objects.filter(device=device).last()
            duration = latest.timestamp - oldest.timestamp
            minutes = int(duration.total_seconds() / 60)
            
            print(f"\n   🔵 {device.device_identifier}")
            print(f"      • Total registros: {count}")
            print(f"      • Duración: {minutes} minutos")
            print(f"      • Frecuencia: {count/max(minutes, 1):.1f} registros/min")
            print(f"      • Último dato: {latest.timestamp.strftime('%H:%M:%S')}")
    
    # Datos de las últimas 24 horas
    yesterday = timezone.now() - timedelta(hours=24)
    recent_count = SensorData.objects.filter(timestamp__gte=yesterday).count()
    print(f"\n📅 Datos de las últimas 24 horas: {recent_count}")

print("\n" + "=" * 80)
print("💡 Tip: Estos datos se usan para generar las gráficas en el dashboard")
print("=" * 80)
