"""
Feature Engineering - Sistema de Detección de Fatiga
Prepara y selecciona features para el modelo de machine learning.
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sensors.models import ProcessedMetrics

print("=" * 80)
print("FEATURE ENGINEERING - SISTEMA DE DETECCIÓN DE FATIGA")
print("=" * 80)
print()

# 1. CARGAR DATOS
print("📊 1. CARGANDO MÉTRICAS PROCESADAS...")
print("-" * 80)

metrics_count = ProcessedMetrics.objects.count()
print(f"Total de métricas procesadas: {metrics_count:,}")

if metrics_count < 10:
    print("\n⚠️  Necesitas al menos 10 registros de métricas procesadas.")
    print("   Ejecuta el simulador ESP32 por al menos 10 minutos.")
    sys.exit(0)

# Cargar datos
df = pd.DataFrame(list(ProcessedMetrics.objects.all().values(
    'window_start', 'window_end',
    'hr_avg', 'hr_max', 'hr_min', 'hrv_rmssd', 'hrv_sdnn', 'hr_trend',
    'spo2_avg', 'spo2_min', 'spo2_variance', 'desaturation_count',
    'activity_level', 'movement_variance', 'movement_entropy',
    'fatigue_index', 'hr_activity_ratio', 'recovery_time'
)))

df['window_start'] = pd.to_datetime(df['window_start'])
df = df.sort_values('window_start')

print(f"✅ Datos cargados: {len(df)} registros")
print(f"   Rango: {df['window_start'].min()} a {df['window_start'].max()}")
print()

# 2. ANÁLISIS DE FEATURES
print("🔍 2. ANÁLISIS DE FEATURES")
print("-" * 80)

# Listar todas las features numéricas
numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
# Remover target y timestamps
features_to_exclude = ['fatigue_index', 'window_start', 'window_end']
feature_cols = [col for col in numeric_features if col not in features_to_exclude]

print(f"\n📋 Features disponibles ({len(feature_cols)}):")
for i, feat in enumerate(feature_cols, 1):
    print(f"   {i:2d}. {feat}")

# Valores faltantes
print(f"\n🔍 Valores faltantes:")
missing = df[feature_cols].isnull().sum()
for col in feature_cols:
    if missing[col] > 0:
        print(f"   {col}: {missing[col]} ({missing[col]/len(df)*100:.1f}%)")
if missing.sum() == 0:
    print(f"   ✅ No hay valores faltantes")

# Rellenar valores faltantes con la mediana
df[feature_cols] = df[feature_cols].fillna(df[feature_cols].median())

print()

# 3. CREACIÓN DE NUEVOS FEATURES
print("🔧 3. CREACIÓN DE NUEVOS FEATURES")
print("-" * 80)

# Feature 1: Diferencia entre HR máximo y mínimo
df['hr_range'] = df['hr_max'] - df['hr_min']
print("✅ hr_range = hr_max - hr_min")

# Feature 2: Índice de recuperación (SpO2 relativo a HR)
df['recovery_index'] = df['spo2_avg'] / (df['hr_avg'] / 100)
print("✅ recovery_index = spo2_avg / (hr_avg / 100)")

# Feature 3: Ratio de variabilidad cardíaca
df['hrv_ratio'] = df['hrv_rmssd'] / (df['hrv_sdnn'] + 1)  # +1 para evitar división por 0
print("✅ hrv_ratio = hrv_rmssd / hrv_sdnn")

# Feature 4: Stress index (HR alto con baja HRV)
df['stress_index'] = df['hr_avg'] / (df['hrv_rmssd'] + 1)
print("✅ stress_index = hr_avg / hrv_rmssd")

# Feature 5: Actividad normalizada por HR
df['activity_normalized'] = df['activity_level'] / (df['hr_avg'] / 100)
print("✅ activity_normalized = activity_level / (hr_avg / 100)")

# Actualizar lista de features
new_features = ['hr_range', 'recovery_index', 'hrv_ratio', 'stress_index', 'activity_normalized']
all_features = feature_cols + new_features

print(f"\n📊 Total de features: {len(all_features)}")
print()

# 4. NORMALIZACIÓN
print("📏 4. NORMALIZACIÓN DE FEATURES")
print("-" * 80)

# Crear copia de features seleccionados
X = df[all_features].copy()

# Normalizar usando StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_scaled_df = pd.DataFrame(X_scaled, columns=all_features, index=df.index)

print(f"✅ Features normalizados usando StandardScaler (media=0, std=1)")
print(f"\nEjemplo - hr_avg:")
print(f"   Original: media={df['hr_avg'].mean():.2f}, std={df['hr_avg'].std():.2f}")
print(f"   Escalado: media={X_scaled_df['hr_avg'].mean():.2f}, std={X_scaled_df['hr_avg'].std():.2f}")
print()

# 5. ANÁLISIS DE IMPORTANCIA DE FEATURES
print("⭐ 5. IMPORTANCIA DE FEATURES")
print("-" * 80)

# Calcular correlación con fatigue_index
correlations = df[all_features].corrwith(df['fatigue_index']).abs().sort_values(ascending=False)

print("\n🔝 Top 10 features más correlacionados con fatigue_index:")
for i, (feat, corr) in enumerate(correlations.head(10).items(), 1):
    print(f"   {i:2d}. {feat:25s}: {corr:.4f}")

# Visualización
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Feature Engineering - Sistema de Detección de Fatiga', fontsize=16, y=1.0)

# 5.1 Correlaciones
ax = axes[0, 0]
correlations.head(15).plot(kind='barh', ax=ax, color='steelblue')
ax.set_title('Top 15 Features - Correlación con Fatigue Index', fontsize=12, fontweight='bold')
ax.set_xlabel('Correlación Absoluta')
ax.grid(True, alpha=0.3, axis='x')

# 5.2 Distribución de features importantes
ax = axes[0, 1]
top_feature = correlations.index[0]
ax.hist(df[top_feature], bins=30, color='green', alpha=0.7, edgecolor='black')
ax.set_title(f'Distribución de {top_feature}', fontsize=12, fontweight='bold')
ax.set_xlabel(top_feature)
ax.set_ylabel('Frecuencia')
ax.grid(True, alpha=0.3)

# 5.3 Scatter plot: feature vs fatigue
ax = axes[1, 0]
ax.scatter(df[top_feature], df['fatigue_index'], alpha=0.5, s=20)
ax.set_title(f'{top_feature} vs Fatigue Index', fontsize=12, fontweight='bold')
ax.set_xlabel(top_feature)
ax.set_ylabel('Fatigue Index')
ax.grid(True, alpha=0.3)

# 5.4 PCA - Análisis de componentes principales
ax = axes[1, 1]
pca = PCA(n_components=min(10, len(all_features)))
pca.fit(X_scaled)

explained_var = pca.explained_variance_ratio_
cumsum_var = np.cumsum(explained_var)

ax.bar(range(1, len(explained_var) + 1), explained_var, alpha=0.7, color='purple', label='Individual')
ax.plot(range(1, len(cumsum_var) + 1), cumsum_var, 'ro-', linewidth=2, label='Acumulado')
ax.axhline(0.95, color='red', linestyle='--', alpha=0.5, label='95%')
ax.set_title('PCA - Varianza Explicada', fontsize=12, fontweight='bold')
ax.set_xlabel('Componente Principal')
ax.set_ylabel('Varianza Explicada')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('notebooks/feature_engineering.png', dpi=300, bbox_inches='tight')
print("\n✅ Gráfica guardada: notebooks/feature_engineering.png")

# 6. SELECCIÓN DE FEATURES
print("\n🎯 6. SELECCIÓN DE FEATURES PARA ML")
print("-" * 80)

# Seleccionar top features por correlación
k_best = min(10, len(all_features))
selected_features = correlations.head(k_best).index.tolist()

print(f"\n📋 Features seleccionados ({k_best}):")
for i, feat in enumerate(selected_features, 1):
    corr = correlations[feat]
    print(f"   {i:2d}. {feat:25s} (r={corr:.4f})")

# 7. GUARDAR RESULTADOS
print("\n💾 7. GUARDANDO RESULTADOS")
print("-" * 80)

# Crear dataset para ML
ml_data = df[['fatigue_index'] + selected_features].copy()
ml_data.to_csv('notebooks/ml_dataset.csv', index=False)
print(f"✅ Dataset ML guardado: notebooks/ml_dataset.csv ({len(ml_data)} registros)")

# Guardar features normalizados
X_scaled_selected = X_scaled_df[selected_features].copy()
X_scaled_selected['fatigue_index'] = df['fatigue_index'].values
X_scaled_selected.to_csv('notebooks/ml_dataset_scaled.csv', index=False)
print(f"✅ Dataset normalizado guardado: notebooks/ml_dataset_scaled.csv")

# Guardar configuración del scaler
import joblib
scaler_data = {
    'scaler': scaler,
    'feature_names': all_features,
    'selected_features': selected_features
}
joblib.dump(scaler_data, 'notebooks/scaler_config.pkl')
print(f"✅ Configuración del scaler guardada: notebooks/scaler_config.pkl")

# 8. RESUMEN
print("\n" + "=" * 80)
print("✅ FEATURE ENGINEERING COMPLETADO")
print("=" * 80)
print(f"\n📊 Resumen:")
print(f"   - Features originales: {len(feature_cols)}")
print(f"   - Features creados: {len(new_features)}")
print(f"   - Features totales: {len(all_features)}")
print(f"   - Features seleccionados para ML: {k_best}")
print(f"   - Registros procesados: {len(df)}")
print()
print(f"📁 Archivos generados:")
print(f"   - notebooks/feature_engineering.png")
print(f"   - notebooks/ml_dataset.csv")
print(f"   - notebooks/ml_dataset_scaled.csv")
print(f"   - notebooks/scaler_config.pkl")
print()
print("💡 Próximo paso:")
print("   Ejecutar: python notebooks/03_clustering_model.py")
print()
print("=" * 80)

plt.show()
