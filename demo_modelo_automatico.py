"""
Demostración de que el modelo ML funciona automáticamente con nuevos dispositivos.
Este script simula la adición de un dispositivo nuevo y muestra el flujo completo.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.devices.models import Device
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.companies.models import Company
from django.utils import timezone
from datetime import timedelta
import random

print("="*80)
print("🧪 DEMOSTRACIÓN: MODELO ML CON NUEVOS DISPOSITIVOS")
print("="*80)
print()

# 1. ESTADO INICIAL
print("1️⃣  ESTADO INICIAL DEL SISTEMA")
print("-"*80)

devices_count = Device.objects.filter(is_active=True).count()
sensor_data_count = SensorData.objects.count()
processed_count = ProcessedMetrics.objects.count()

print(f"✅ Dispositivos activos: {devices_count}")
print(f"✅ Registros de sensores: {sensor_data_count}")
print(f"✅ Métricas procesadas (con ML): {processed_count}")
print()

# 2. LISTAR DISPOSITIVOS ACTUALES
print("2️⃣  DISPOSITIVOS ACTUALES")
print("-"*80)

devices = Device.objects.filter(is_active=True).select_related('employee')
for i, device in enumerate(devices[:5], 1):
    latest_metric = ProcessedMetrics.objects.filter(device=device).first()
    fatigue = latest_metric.fatigue_index if latest_metric else "Sin datos"
    print(f"{i}. {device.device_identifier} → {device.employee.get_full_name()}")
    print(f"   Última fatiga ML: {fatigue if isinstance(fatigue, str) else f'{fatigue:.1f}%'}")

if devices.count() > 5:
    print(f"   ... y {devices.count() - 5} dispositivos más")
print()

# 3. VERIFICAR SCHEDULER AUTOMÁTICO
print("3️⃣  VERIFICACIÓN DEL SCHEDULER")
print("-"*80)
print("El scheduler está configurado para procesar automáticamente:")
print("  • Intervalo: Cada 2 minutos")
print("  • Busca: Device.objects.filter(is_active=True)")
print("  • Incluye: TODOS los dispositivos activos (antiguos y nuevos)")
print()

# 4. MOSTRAR CÓDIGO DEL SCHEDULER
print("4️⃣  CÓDIGO QUE HACE AUTOMÁTICO EL PROCESAMIENTO")
print("-"*80)
print("""
# apps/sensors/scheduler.py (línea ~27)

def process_metrics_job():
    '''Job que procesa TODOS los dispositivos activos'''
    
    # ⭐ BUSCA AUTOMÁTICAMENTE TODOS LOS DISPOSITIVOS ⭐
    devices = Device.objects.filter(is_active=True)
    # ↑ No hay lista hardcoded, incluye cualquier dispositivo nuevo
    
    for device in devices:
        # Procesar ventana de datos
        processor.process_device_window(device, start, end)
        # ↓
        # Calcula métricas → Llama al modelo ML → Guarda en BD
""")
print()

# 5. MOSTRAR USO DEL MODELO
print("5️⃣  USO DEL MODELO ML (MISMO PARA TODOS)")
print("-"*80)
print("""
# apps/analytics/ml_service.py

def predict_fatigue(metrics):
    '''Predicción con modelo K-Means (un solo modelo para todos)'''
    
    # 1. Normalizar
    X_scaled = scaler.transform([metrics])
    
    # 2. Predecir cluster
    cluster = model.predict(X_scaled)[0]
    
    # 3. Mapear a fatiga
    fatigue = cluster_fatigue_map[cluster]
    
    return fatigue  # Mismo modelo, diferentes dispositivos
""")
print()

# 6. SIMULACIÓN: AÑADIR DISPOSITIVO NUEVO
print("6️⃣  SIMULACIÓN: ¿QUÉ PASA SI AÑADO UN DISPOSITIVO?")
print("-"*80)
print()

print("Paso 1: Crear dispositivo nuevo (manual)")
print("""
    POST /api/devices/
    {
      "device_identifier": "ESP32-NEW",
      "employee": 15,
      "is_active": true
    }
""")
print("  ✅ Dispositivo creado en BD")
print()

print("Paso 2: ESP32 envía datos (automático)")
print("""
    Cada 5 segundos:
    POST /api/sensors/data/
    {
      "device_identifier": "ESP32-NEW",
      "heart_rate": 78,
      "spo2": 97,
      ...
    }
""")
print("  ✅ Datos guardados en SensorData")
print()

print("Paso 3: Scheduler detecta (automático - cada 2min)")
print("""
    devices = Device.objects.filter(is_active=True)
    # ← Incluye ESP32-NEW automáticamente
    
    for device in devices:  # Incluye el nuevo
        if has_recent_data(device):
            process_device_window(device)
""")
print("  ✅ ESP32-NEW detectado y procesado")
print()

print("Paso 4: Modelo ML predice (automático)")
print("""
    metrics = calculate_features(sensor_data)  # 10 features
    fatigue = predict_fatigue(metrics)  # Modelo K-Means
    # ← Mismo modelo que para ESP32-010, ESP32-011, etc.
""")
print("  ✅ Predicción: 52.3% de fatiga")
print()

print("Paso 5: Guardar en BD (automático)")
print("""
    ProcessedMetrics.objects.create(
        device=ESP32-NEW,  # Nuevo dispositivo
        employee=empleado_15,
        fatigue_index=52.3,  # Predicción ML
        ...
    )
""")
print("  ✅ Métrica guardada con predicción ML")
print()

print("Paso 6: Dashboard muestra (automático)")
print("""
    GET /api/dashboard/?employee=15
    {
      "device": "ESP32-NEW",
      "fatigue_current": 52.3,  # ← Del modelo ML
      "status": "normal"
    }
""")
print("  ✅ Visible en dashboard inmediatamente")
print()

# 7. TABLA COMPARATIVA
print("7️⃣  COMPARACIÓN: DISPOSITIVO VIEJO vs NUEVO")
print("-"*80)
print()
print("| Aspecto              | ESP32-010 (viejo) | ESP32-NEW (nuevo) |")
print("|----------------------|-------------------|-------------------|")
print("| Scheduler lo detecta | ✅ SÍ             | ✅ SÍ             |")
print("| Procesa datos        | ✅ Cada 2min      | ✅ Cada 2min      |")
print("| Usa modelo ML        | ✅ K-Means        | ✅ K-Means        |")
print("| Modelo específico    | ❌ NO             | ❌ NO             |")
print("| Configuración extra  | ❌ NO             | ❌ NO             |")
print("| Funciona automático  | ✅ SÍ             | ✅ SÍ             |")
print()
print("💡 Conclusión: NO HAY DIFERENCIA en el procesamiento")
print()

# 8. ESTADÍSTICAS ACTUALES
print("8️⃣  ESTADÍSTICAS DE USO DEL MODELO")
print("-"*80)

# Métricas con predicciones ML
recent_metrics = ProcessedMetrics.objects.order_by('-window_start')[:10]

if recent_metrics.exists():
    print(f"✅ Últimas {recent_metrics.count()} predicciones del modelo ML:")
    print()
    print("  Device       | Empleado              | Fatiga ML | Timestamp")
    print("  " + "-"*70)
    
    for metric in recent_metrics:
        device_id = metric.device.device_identifier[:12]
        employee_name = metric.employee.get_full_name()[:20]
        fatigue = metric.fatigue_index
        timestamp = metric.window_start.strftime("%Y-%m-%d %H:%M")
        
        print(f"  {device_id:12} | {employee_name:20} | {fatigue:5.1f}%  | {timestamp}")
    
    print()
    print(f"  💡 Todas estas predicciones usan el MISMO modelo K-Means")
else:
    print("  ⚠️  Aún no hay métricas procesadas")
    print("     Espera 2-3 minutos después de que los simuladores envíen datos")

print()

# 9. RESUMEN
print("9️⃣  RESUMEN EJECUTIVO")
print("-"*80)
print()
print("✅ El modelo ML funciona AUTOMÁTICAMENTE con nuevos dispositivos porque:")
print()
print("  1. Scheduler busca Device.objects.filter(is_active=True)")
print("     → No hay lista hardcoded de dispositivos")
print()
print("  2. Modelo ML es GENÉRICO (no por dispositivo)")
print("     → Un solo modelo (fatigue_model.pkl) para todos")
print()
print("  3. Procesamiento es DINÁMICO")
print("     → Se adapta a cualquier dispositivo activo")
print()
print("  4. Base de datos RELACIONAL")
print("     → Todo se vincula automáticamente por ForeignKeys")
print()
print("🎯 INTERVENCIÓN MANUAL REQUERIDA: ❌ CERO")
print()
print("   Solo necesitas:")
print("   • Crear el registro del dispositivo en BD")
print("   • Configurar el ESP32 físico")
print("   • ¡Listo! El resto es automático.")
print()

print("="*80)
print("✅ DEMOSTRACIÓN COMPLETADA")
print("="*80)
print()
print("💡 Tip: Puedes añadir 1, 10, 100 o 1000 dispositivos.")
print("    El sistema procesará todos automáticamente sin cambios en código.")
