"""
Script de análisis exploratorio de datos para el sistema de detección de fatiga.
Genera visualizaciones y estadísticas de los datos de sensores.
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sensors.models import SensorData, ProcessedMetrics
from apps.devices.models import Device
from django.utils import timezone

# Configurar estilo de gráficas
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 8)

print("=" * 80)
print("ANÁLISIS EXPLORATORIO DE DATOS - SISTEMA DE DETECCIÓN DE FATIGA")
print("=" * 80)
print()

# 1. CARGAR DATOS
print("📊 1. CARGANDO DATOS...")
print("-" * 80)

# Contar registros
sensor_count = SensorData.objects.count()
metrics_count = ProcessedMetrics.objects.count()
devices_count = Device.objects.filter(is_active=True).count()

print(f"Total de registros SensorData: {sensor_count:,}")
print(f"Total de registros ProcessedMetrics: {metrics_count:,}")
print(f"Dispositivos activos: {devices_count}")

if sensor_count == 0:
    print("\n⚠️  No hay datos. Ejecuta el simulador ESP32 primero.")
    print("   python esp32_simulator.py")
    sys.exit(0)

print()

# 2. CONVERTIR A DATAFRAMES
print("📋 2. CONVIRTIENDO A DATAFRAMES...")
print("-" * 80)

# SensorData
sensor_df = pd.DataFrame(list(SensorData.objects.all().values(
    'device_id', 'timestamp', 'heart_rate', 'spo2',
    'accel_x', 'accel_y', 'accel_z', 'created_at'
)))

if not sensor_df.empty:
    sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'])
    sensor_df = sensor_df.sort_values('timestamp')
    print(f"✅ SensorData: {len(sensor_df)} registros")
    print(f"   Rango de fechas: {sensor_df['timestamp'].min()} a {sensor_df['timestamp'].max()}")

# ProcessedMetrics
if metrics_count > 0:
    metrics_df = pd.DataFrame(list(ProcessedMetrics.objects.all().values(
        'device_id', 'employee_id', 'window_start', 'window_end',
        'hr_avg', 'hr_max', 'hr_min', 'hrv_rmssd', 'hrv_sdnn', 'hr_trend',
        'spo2_avg', 'spo2_min', 'spo2_variance', 'desaturation_count',
        'activity_level', 'movement_variance', 'movement_entropy',
        'fatigue_index', 'hr_activity_ratio'
    )))
    
    metrics_df['window_start'] = pd.to_datetime(metrics_df['window_start'])
    metrics_df = metrics_df.sort_values('window_start')
    print(f"✅ ProcessedMetrics: {len(metrics_df)} registros")
else:
    print("⚠️  No hay métricas procesadas. Ejecuta el procesador:")
    print("   from apps.sensors.processors import metrics_processor")
    print("   metrics_processor.process_latest_windows()")
    metrics_df = pd.DataFrame()

print()

# 3. ESTADÍSTICAS DESCRIPTIVAS
print("📈 3. ESTADÍSTICAS DESCRIPTIVAS")
print("-" * 80)

print("\n🫀 RITMO CARDÍACO (HR):")
print(sensor_df['heart_rate'].describe())

print("\n💨 OXIGENACIÓN (SpO2):")
print(sensor_df['spo2'].describe())

print("\n🏃 ACELERÓMETRO:")
print("\n  Eje X:")
print(sensor_df['accel_x'].describe())
print("\n  Eje Y:")
print(sensor_df['accel_y'].describe())
print("\n  Eje Z:")
print(sensor_df['accel_z'].describe())

if not metrics_df.empty:
    print("\n😴 ÍNDICE DE FATIGA:")
    print(metrics_df['fatigue_index'].describe())
    print(f"\n  Distribución por niveles:")
    print(f"  - Bajo (0-30): {len(metrics_df[metrics_df['fatigue_index'] <= 30])}")
    print(f"  - Medio (30-60): {len(metrics_df[(metrics_df['fatigue_index'] > 30) & (metrics_df['fatigue_index'] <= 60)])}")
    print(f"  - Alto (60-100): {len(metrics_df[metrics_df['fatigue_index'] > 60])}")

print()

# 4. VISUALIZACIONES
print("📊 4. GENERANDO VISUALIZACIONES...")
print("-" * 80)

# Crear figura con múltiples subplots
fig, axes = plt.subplots(3, 2, figsize=(15, 12))
fig.suptitle('Análisis de Datos de Sensores - Sistema de Detección de Fatiga', fontsize=16, y=1.0)

# 4.1 Serie de tiempo - Ritmo Cardíaco
ax = axes[0, 0]
sensor_df_sample = sensor_df.tail(200)  # Últimos 200 puntos
ax.plot(sensor_df_sample['timestamp'], sensor_df_sample['heart_rate'], linewidth=0.8, color='red')
ax.set_title('Serie de Tiempo - Ritmo Cardíaco (HR)', fontsize=12, fontweight='bold')
ax.set_xlabel('Tiempo')
ax.set_ylabel('BPM')
ax.grid(True, alpha=0.3)
ax.tick_params(axis='x', rotation=45)

# 4.2 Distribución de HR
ax = axes[0, 1]
ax.hist(sensor_df['heart_rate'], bins=30, color='red', alpha=0.7, edgecolor='black')
ax.axvline(sensor_df['heart_rate'].mean(), color='darkred', linestyle='--', linewidth=2, label=f'Media: {sensor_df["heart_rate"].mean():.1f}')
ax.set_title('Distribución de Ritmo Cardíaco', fontsize=12, fontweight='bold')
ax.set_xlabel('BPM')
ax.set_ylabel('Frecuencia')
ax.legend()
ax.grid(True, alpha=0.3)

# 4.3 Serie de tiempo - SpO2
ax = axes[1, 0]
ax.plot(sensor_df_sample['timestamp'], sensor_df_sample['spo2'], linewidth=0.8, color='blue')
ax.axhline(95, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='Umbral 95%')
ax.set_title('Serie de Tiempo - Saturación de Oxígeno (SpO2)', fontsize=12, fontweight='bold')
ax.set_xlabel('Tiempo')
ax.set_ylabel('SpO2 (%)')
ax.legend()
ax.grid(True, alpha=0.3)
ax.tick_params(axis='x', rotation=45)

# 4.4 Distribución de SpO2
ax = axes[1, 1]
ax.hist(sensor_df['spo2'], bins=30, color='blue', alpha=0.7, edgecolor='black')
ax.axvline(sensor_df['spo2'].mean(), color='darkblue', linestyle='--', linewidth=2, label=f'Media: {sensor_df["spo2"].mean():.1f}%')
ax.set_title('Distribución de SpO2', fontsize=12, fontweight='bold')
ax.set_xlabel('SpO2 (%)')
ax.set_ylabel('Frecuencia')
ax.legend()
ax.grid(True, alpha=0.3)

# 4.5 Acelerómetro 3D
ax = axes[2, 0]
# Calcular magnitud del acelerómetro
sensor_df['accel_magnitude'] = np.sqrt(
    sensor_df['accel_x']**2 + 
    sensor_df['accel_y']**2 + 
    (sensor_df['accel_z'] - 9.81)**2
)
ax.plot(sensor_df_sample['timestamp'], sensor_df_sample['accel_magnitude'], linewidth=0.8, color='green')
ax.set_title('Nivel de Actividad (Magnitud del Acelerómetro)', fontsize=12, fontweight='bold')
ax.set_xlabel('Tiempo')
ax.set_ylabel('Magnitud (g)')
ax.grid(True, alpha=0.3)
ax.tick_params(axis='x', rotation=45)

# 4.6 Índice de Fatiga (si existe)
ax = axes[2, 1]
if not metrics_df.empty:
    ax.plot(metrics_df['window_start'], metrics_df['fatigue_index'], linewidth=1.5, color='purple', marker='o', markersize=4)
    ax.axhline(30, color='green', linestyle='--', alpha=0.5, label='Bajo')
    ax.axhline(60, color='orange', linestyle='--', alpha=0.5, label='Medio')
    ax.axhline(80, color='red', linestyle='--', alpha=0.5, label='Alto')
    ax.set_title('Índice de Fatiga en el Tiempo', fontsize=12, fontweight='bold')
    ax.set_xlabel('Tiempo')
    ax.set_ylabel('Índice de Fatiga (0-100)')
    ax.set_ylim(0, 100)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='x', rotation=45)
else:
    ax.text(0.5, 0.5, 'No hay datos de\nmétricas procesadas', 
            ha='center', va='center', fontsize=12, transform=ax.transAxes)
    ax.set_title('Índice de Fatiga', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('notebooks/exploracion_datos.png', dpi=300, bbox_inches='tight')
print("✅ Gráfica guardada: notebooks/exploracion_datos.png")

# 5. MATRIZ DE CORRELACIÓN
if not metrics_df.empty:
    print("\n📊 5. MATRIZ DE CORRELACIÓN")
    print("-" * 80)
    
    # Seleccionar variables numéricas
    numeric_cols = ['hr_avg', 'hr_max', 'hr_min', 'hrv_rmssd', 'spo2_avg', 
                    'activity_level', 'fatigue_index', 'hr_activity_ratio']
    
    # Filtrar columnas que existen
    available_cols = [col for col in numeric_cols if col in metrics_df.columns]
    
    if len(available_cols) > 2:
        correlation_matrix = metrics_df[available_cols].corr()
        
        plt.figure(figsize=(12, 10))
        sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                    center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
        plt.title('Matriz de Correlación - Métricas de Fatiga', fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig('notebooks/matriz_correlacion.png', dpi=300, bbox_inches='tight')
        print("✅ Matriz de correlación guardada: notebooks/matriz_correlacion.png")
        
        # Mostrar correlaciones más fuertes con fatigue_index
        if 'fatigue_index' in correlation_matrix.columns:
            print("\n🔍 Correlaciones con Fatigue Index:")
            fatigue_corr = correlation_matrix['fatigue_index'].sort_values(ascending=False)
            for var, corr in fatigue_corr.items():
                if var != 'fatigue_index':
                    print(f"   {var:25s}: {corr:6.3f}")

# 6. DETECCIÓN DE OUTLIERS
print("\n🔍 6. DETECCIÓN DE OUTLIERS")
print("-" * 80)

def detect_outliers_iqr(data, column):
    """Detecta outliers usando el método IQR"""
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = data[(data[column] < lower_bound) | (data[column] > upper_bound)]
    return outliers, lower_bound, upper_bound

# Detectar outliers en HR
hr_outliers, hr_low, hr_high = detect_outliers_iqr(sensor_df, 'heart_rate')
print(f"\n🫀 Ritmo Cardíaco:")
print(f"   Rango normal (IQR): {hr_low:.1f} - {hr_high:.1f} BPM")
print(f"   Outliers detectados: {len(hr_outliers)} ({len(hr_outliers)/len(sensor_df)*100:.2f}%)")

# Detectar outliers en SpO2
spo2_outliers, spo2_low, spo2_high = detect_outliers_iqr(sensor_df, 'spo2')
print(f"\n💨 SpO2:")
print(f"   Rango normal (IQR): {spo2_low:.1f} - {spo2_high:.1f} %")
print(f"   Outliers detectados: {len(spo2_outliers)} ({len(spo2_outliers)/len(sensor_df)*100:.2f}%)")

# 7. RESUMEN FINAL
print("\n" + "=" * 80)
print("✅ ANÁLISIS COMPLETADO")
print("=" * 80)
print(f"\n📁 Archivos generados:")
print(f"   - notebooks/exploracion_datos.png")
if not metrics_df.empty:
    print(f"   - notebooks/matriz_correlacion.png")
print()
print("💡 Próximos pasos:")
print("   1. Revisar las visualizaciones generadas")
print("   2. Ejecutar 02_feature_engineering.py para selección de features")
print("   3. Ejecutar 03_clustering_model.py para entrenar modelo ML")
print()
print("=" * 80)

# Mostrar gráficas
plt.show()
