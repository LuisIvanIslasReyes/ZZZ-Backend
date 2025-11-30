"""
Script de verificación del sistema ML de detección de fatiga.
Verifica el modelo, datos de entrenamiento, predicciones y coherencia.
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.analytics.ml_service import FatigueMLService
from apps.sensors.models import SensorData, ProcessedMetrics
from pathlib import Path
import json

print("=" * 80)
print("🤖 VERIFICACIÓN DEL SISTEMA ML DE DETECCIÓN DE FATIGA")
print("=" * 80)

# 1. Verificar archivos del modelo
print("\n📁 1. VERIFICACIÓN DE ARCHIVOS")
print("-" * 80)

base_dir = Path(__file__).parent
ml_models_dir = base_dir / 'ml_models'
model_file = ml_models_dir / 'fatigue_model.pkl'
metadata_file = ml_models_dir / 'model_metadata.json'

print(f"Directorio ML: {ml_models_dir}")
print(f"Modelo (.pkl): {'✅ Existe' if model_file.exists() else '❌ NO existe'}")
print(f"Metadata (.json): {'✅ Existe' if metadata_file.exists() else '❌ NO existe'}")

if metadata_file.exists():
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"\n📊 Metadata del modelo:")
    if 'kmeans' in metadata:
        km = metadata['kmeans']
        print(f"   • Algoritmo: K-Means")
        print(f"   • Clusters: {km['n_clusters']}")
        print(f"   • Silhouette Score: {km['silhouette_score']:.4f}")
        print(f"   • Muestras entrenamiento: {metadata['data']['n_samples']:,}")
        print(f"   • Features seleccionadas: {metadata['data']['n_features']}")
        
        print(f"\n   📈 Distribución de clusters:")
        for cluster_id, count in km['cluster_distribution'].items():
            fatigue = km['cluster_fatigue_map'][cluster_id]
            pct = (count / metadata['data']['n_samples']) * 100
            print(f"      Cluster {cluster_id}: {count:,} muestras ({pct:.1f}%) - Fatiga promedio: {fatigue:.1f}%")

# 2. Verificar servicio ML
print(f"\n🔧 2. VERIFICACIÓN DEL SERVICIO ML")
print("-" * 80)

ml_service = FatigueMLService()
print(f"Servicio inicializado: ✅")
print(f"Modo actual: {ml_service.model_type}")
print(f"Modelo cargado: {'✅ Sí' if ml_service.model_loaded else '❌ No (usando placeholder)'}")

# Intentar cargar modelo si existe
if model_file.exists() and not ml_service.model_loaded:
    print(f"\n🔄 Intentando cargar modelo...")
    success = ml_service.load_model(str(model_file))
    if success:
        print(f"✅ Modelo cargado exitosamente")
        print(f"   • Tipo: {ml_service.model_type}")
        print(f"   • Features: {len(ml_service.selected_features)}")
        print(f"   • Features: {', '.join(ml_service.selected_features[:5])}...")
    else:
        print(f"❌ No se pudo cargar el modelo")

# 3. Verificar datos disponibles
print(f"\n💾 3. VERIFICACIÓN DE DATOS")
print("-" * 80)

sensor_count = SensorData.objects.count()
metrics_count = ProcessedMetrics.objects.count()

print(f"Datos de sensores (SensorData): {sensor_count:,} registros")
print(f"Métricas procesadas (ProcessedMetrics): {metrics_count:,} registros")

if sensor_count > 0:
    latest_sensor = SensorData.objects.first()
    print(f"   Último dato sensor: {latest_sensor.timestamp} ({latest_sensor.device.device_identifier})")
else:
    print(f"   ⚠️  No hay datos de sensores. Crea un simulador para generar datos.")

if metrics_count > 0:
    latest_metric = ProcessedMetrics.objects.first()
    print(f"   Última métrica: {latest_metric.window_end} - Fatiga: {latest_metric.fatigue_index:.1f}%")
else:
    print(f"   ⚠️  No hay métricas procesadas. Ejecuta el procesamiento automático.")

# 4. Prueba de predicción
print(f"\n🧪 4. PRUEBA DE PREDICCIÓN")
print("-" * 80)

# Métricas de prueba (valores normales)
test_metrics_normal = {
    'hr_avg': 75.0,
    'hr_std': 5.0,
    'hrv_sdnn': 45.0,
    'hrv_rmssd': 35.0,
    'hrv_ratio': 1.3,
    'spo2_avg': 98.0,
    'spo2_std': 0.5,
    'spo2_variance': 0.25,
    'desaturation_count': 0,
    'activity_level': 0.3,
    'activity_normalized': 0.3,
    'movement_variance': 0.15,
    'movement_entropy': 2.5,
    'hr_activity_ratio': 1.5
}

# Métricas de prueba (valores fatigados)
test_metrics_fatigued = {
    'hr_avg': 95.0,
    'hr_std': 12.0,
    'hrv_sdnn': 25.0,
    'hrv_rmssd': 18.0,
    'hrv_ratio': 0.7,
    'spo2_avg': 93.0,
    'spo2_std': 2.0,
    'spo2_variance': 4.0,
    'desaturation_count': 5,
    'activity_level': 0.8,
    'activity_normalized': 0.8,
    'movement_variance': 0.45,
    'movement_entropy': 1.2,
    'hr_activity_ratio': 2.5
}

print("Caso 1: Persona descansada")
fatigue_normal = ml_service.predict_fatigue_index(test_metrics_normal)
print(f"   Predicción: {fatigue_normal:.1f}% de fatiga")
print(f"   Estado: {'✅ Normal' if fatigue_normal < 50 else '⚠️ Elevado'}")

print("\nCaso 2: Persona fatigada")
fatigue_fatigued = ml_service.predict_fatigue_index(test_metrics_fatigued)
print(f"   Predicción: {fatigue_fatigued:.1f}% de fatiga")
print(f"   Estado: {'✅ Normal' if fatigue_fatigued < 50 else '⚠️ Elevado'}")

# Verificar coherencia
print(f"\n🔍 Verificación de coherencia:")
if fatigue_fatigued > fatigue_normal:
    print(f"   ✅ Las predicciones son coherentes (fatigado > normal)")
    diff = fatigue_fatigued - fatigue_normal
    print(f"   📊 Diferencia: {diff:.1f} puntos")
else:
    print(f"   ❌ ALERTA: Predicciones incoherentes")
    print(f"      Normal: {fatigue_normal:.1f}% | Fatigado: {fatigue_fatigued:.1f}%")

# 5. Recomendaciones
print(f"\n💡 5. RECOMENDACIONES")
print("-" * 80)

if not model_file.exists():
    print("❌ Modelo no entrenado")
    print("\n📝 Para entrenar el modelo:")
    print("   1. Genera datos con simuladores (al menos 30 minutos)")
    print("   2. Ejecuta: python notebooks/03_clustering_model.py")
    print("   3. Reinicia el servidor Django")
    
elif not ml_service.model_loaded:
    print("⚠️  Modelo existe pero no está cargado")
    print("\n📝 Para cargar el modelo:")
    print("   1. Reinicia el servidor Django")
    print("   2. O llama ml_service.load_model() manualmente")
    
else:
    print("✅ Sistema ML completamente funcional")
    print("\n📝 Próximos pasos:")
    print("   • Generar más datos para mejorar el modelo")
    print("   • Monitorear predicciones en tiempo real")
    print("   • Ajustar umbrales si es necesario")

# 6. Estado de features
if ml_service.model_loaded:
    print(f"\n📊 6. FEATURES DEL MODELO")
    print("-" * 80)
    print(f"Total de features: {len(ml_service.selected_features)}")
    print(f"\nFeatures utilizadas:")
    for i, feature in enumerate(ml_service.selected_features, 1):
        print(f"   {i:2d}. {feature}")

print("\n" + "=" * 80)
print("✅ Verificación completada")
print("=" * 80)
