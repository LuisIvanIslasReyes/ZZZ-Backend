"""
Script para verificar que el modelo ML se está usando en el sistema.
Compara predicciones con placeholder vs modelo entrenado.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.analytics.ml_service import ml_service, predict_fatigue
import numpy as np

print("="*80)
print("🔍 VERIFICACIÓN DE USO DEL MODELO ML")
print("="*80)
print()

# 1. Verificar estado del servicio
print("1. ESTADO DEL SERVICIO ML")
print("-"*80)
print(f"Modelo cargado: {'✅ SÍ' if ml_service.model_loaded else '❌ NO'}")
print(f"Modo actual: {ml_service.model_type}")

if ml_service.model_loaded:
    print(f"Features seleccionadas: {len(ml_service.selected_features)}")
    print(f"Clusters disponibles: {list(ml_service.cluster_fatigue_map.keys())}")
    print(f"Mapeo de fatiga por cluster:")
    for cluster, fatiga in ml_service.cluster_fatigue_map.items():
        print(f"  • Cluster {cluster} → Fatiga {fatiga:.1f}%")
else:
    print("⚠️  Modelo NO cargado. Intentando cargar...")
    if ml_service.load_model():
        print("✅ Modelo cargado exitosamente")
    else:
        print("❌ No se pudo cargar el modelo")
        print("   Usando modo placeholder (heurísticas)")

print()

# 2. Hacer predicciones de prueba
print("2. PRUEBAS DE PREDICCIÓN")
print("-"*80)

# Caso 1: Persona descansada
print("\n📊 Caso 1: Trabajador descansado")
metrics_normal = {
    'hr_avg': 70,
    'hrv_rmssd': 50,
    'hrv_sdnn': 55,
    'spo2_avg': 98,
    'spo2_variance': 0.5,
    'desaturation_count': 0,
    'activity_level': 1.0,
    'movement_variance': 0.5,
    'movement_entropy': 1.5,
    'hr_activity_ratio': 70,
    'hrv_ratio': 0.9,
    'activity_normalized': 1.4,
}

fatigue_normal = predict_fatigue(metrics_normal)
print(f"HR: 70 BPM, SpO2: 98%, HRV: 50ms")
print(f"Predicción: {fatigue_normal:.1f}% de fatiga")
print(f"Estado: {'✅ Normal' if fatigue_normal < 55 else '⚠️ Elevado'}")

# Caso 2: Persona fatigada
print("\n📊 Caso 2: Trabajador fatigado")
metrics_fatigued = {
    'hr_avg': 110,
    'hrv_rmssd': 20,
    'hrv_sdnn': 25,
    'spo2_avg': 94,
    'spo2_variance': 3.0,
    'desaturation_count': 2,
    'activity_level': 0.5,
    'movement_variance': 0.2,
    'movement_entropy': 0.8,
    'hr_activity_ratio': 220,
    'hrv_ratio': 0.8,
    'activity_normalized': 0.4,
}

fatigue_fatigued = predict_fatigue(metrics_fatigued)
print(f"HR: 110 BPM, SpO2: 94%, HRV: 20ms")
print(f"Predicción: {fatigue_fatigued:.1f}% de fatiga")
print(f"Estado: {'✅ Normal' if fatigue_fatigued < 55 else '⚠️ Elevado'}")

# Caso 3: Datos extremos
print("\n📊 Caso 3: Situación crítica")
metrics_critical = {
    'hr_avg': 140,
    'hrv_rmssd': 10,
    'hrv_sdnn': 12,
    'spo2_avg': 91,
    'spo2_variance': 5.0,
    'desaturation_count': 5,
    'activity_level': 0.3,
    'movement_variance': 0.1,
    'movement_entropy': 0.5,
    'hr_activity_ratio': 466,
    'hrv_ratio': 0.83,
    'activity_normalized': 0.2,
}

fatigue_critical = predict_fatigue(metrics_critical)
print(f"HR: 140 BPM, SpO2: 91%, HRV: 10ms")
print(f"Predicción: {fatigue_critical:.1f}% de fatiga")
print(f"Estado: {'✅ Normal' if fatigue_critical < 55 else '🚨 CRÍTICO'}")

print()

# 3. Análisis de coherencia
print("3. ANÁLISIS DE COHERENCIA")
print("-"*80)
print(f"Fatiga Normal:   {fatigue_normal:.1f}%")
print(f"Fatiga Elevada:  {fatigue_fatigued:.1f}%")
print(f"Fatiga Crítica:  {fatigue_critical:.1f}%")
print()

if fatigue_normal < fatigue_fatigued < fatigue_critical:
    print("✅ Predicciones coherentes (normal < elevado < crítico)")
    print(f"   Diferencia Normal→Elevada: +{fatigue_fatigued - fatigue_normal:.1f} puntos")
    print(f"   Diferencia Elevada→Crítica: +{fatigue_critical - fatigue_fatigued:.1f} puntos")
else:
    print("⚠️  Predicciones NO coherentes")
    print("   Revisa el modelo o las heurísticas")

print()

# 4. Información del modelo
print("4. INFORMACIÓN DEL MODELO")
print("-"*80)

if ml_service.model_loaded:
    print("✅ Usando modelo K-Means entrenado")
    print(f"   Tipo: {ml_service.model_type}")
    print(f"   Features: {len(ml_service.selected_features)}")
    print()
    print("   Features utilizadas:")
    for i, feature in enumerate(ml_service.selected_features, 1):
        print(f"   {i}. {feature}")
else:
    print("⚠️  Usando cálculo placeholder (heurísticas)")
    print()
    print("Para cargar el modelo entrenado:")
    print("   1. Verifica: ml_models/fatigue_model.pkl existe")
    print("   2. Reinicia el servidor Django")
    print("   3. O ejecuta: ml_service.load_model()")

print()

# 5. Verificar datos recientes
print("5. DATOS RECIENTES EN BD")
print("-"*80)

try:
    from apps.sensors.models import SensorData, ProcessedMetrics
    
    sensor_count = SensorData.objects.count()
    metrics_count = ProcessedMetrics.objects.count()
    
    print(f"Registros de sensores: {sensor_count}")
    print(f"Métricas procesadas: {metrics_count}")
    
    if metrics_count > 0:
        latest_metric = ProcessedMetrics.objects.order_by('-window_start').first()
        print(f"\nÚltima métrica procesada:")
        print(f"  • Timestamp: {latest_metric.window_start}")
        print(f"  • Empleado: {latest_metric.employee.get_full_name()}")
        print(f"  • HR promedio: {latest_metric.hr_avg:.1f} BPM")
        print(f"  • SpO2 promedio: {latest_metric.spo2_avg:.1f}%")
        print(f"  • 🎯 Fatiga ML: {latest_metric.fatigue_index:.1f}% ← Predicción del modelo")
        
        # Comparar con predicción manual
        test_metrics = {
            'hr_avg': latest_metric.hr_avg,
            'hrv_rmssd': latest_metric.hrv_rmssd or 0,
            'hrv_sdnn': latest_metric.hrv_sdnn or 0,
            'spo2_avg': latest_metric.spo2_avg,
            'spo2_variance': latest_metric.spo2_variance or 0,
            'desaturation_count': latest_metric.desaturation_count,
            'activity_level': latest_metric.activity_level,
            'movement_variance': latest_metric.movement_variance or 0,
            'movement_entropy': latest_metric.movement_entropy or 0,
            'hr_activity_ratio': latest_metric.hr_activity_ratio or 0,
            'hrv_ratio': (latest_metric.hrv_rmssd / (latest_metric.hrv_sdnn + 1)) if latest_metric.hrv_sdnn else 0,
            'activity_normalized': latest_metric.activity_level / (latest_metric.hr_avg / 100) if latest_metric.hr_avg > 0 else 0,
        }
        
        fatigue_recalc = predict_fatigue(test_metrics)
        print(f"  • Re-cálculo ahora: {fatigue_recalc:.1f}%")
        
        diff = abs(latest_metric.fatigue_index - fatigue_recalc)
        if diff < 5:
            print(f"  ✅ Consistente (diferencia: {diff:.1f}%)")
        else:
            print(f"  ⚠️  Diferencia notable: {diff:.1f}%")
            print(f"     (puede indicar cambio en modelo o placeholder)")
    
except Exception as e:
    print(f"⚠️  Error al consultar BD: {str(e)}")

print()
print("="*80)
print("✅ VERIFICACIÓN COMPLETADA")
print("="*80)
