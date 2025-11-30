"""
Entrenamiento simple del modelo K-Means - Sin visualizaciones complejas
"""
import os
import sys
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import json

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*80)
print("ENTRENAMIENTO SIMPLE DEL MODELO K-MEANS")
print("="*80)

# 1. CARGAR DATOS
print("\n1. Cargando datos...")
df = pd.read_csv('notebooks/ml_dataset_scaled.csv')
print(f"✅ Dataset: {len(df)} registros")

# Separar features y target
y = df['fatigue_index'].values
X = df.drop('fatigue_index', axis=1).values
feature_names = df.drop('fatigue_index', axis=1).columns.tolist()
print(f"   Features: {len(feature_names)}")

# 2. ENTRENAR MODELO
print("\n2. Entrenando modelo K-Means...")
optimal_k = 2  # Ya sabemos que 2 es óptimo
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X)
print(f"✅ Modelo entrenado con K={optimal_k}")

# 3. MAPEAR CLUSTERS A FATIGA
print("\n3. Mapeando clusters a niveles de fatiga...")
cluster_fatigue_map = {}
for cluster_id in range(optimal_k):
    cluster_mask = clusters == cluster_id
    avg_fatigue = np.mean(y[cluster_mask])
    cluster_fatigue_map[int(cluster_id)] = float(avg_fatigue)
    count = np.sum(cluster_mask)
    print(f"   Cluster {cluster_id}: Fatiga {avg_fatigue:.1f}% ({count} registros)")

# 4. CREAR CONFIGURACIÓN DEL SCALER
print("\n4. Creando configuración del scaler...")
scaler = StandardScaler()
scaler_data = {
    'scaler': scaler,
    'feature_names': feature_names,
    'selected_features': feature_names
}

# 5. GUARDAR MODELO
print("\n5. Guardando modelo...")
os.makedirs('ml_models', exist_ok=True)

# Paquete del modelo
model_package = {
    'model': kmeans,
    'model_type': 'kmeans',
    'n_clusters': optimal_k,
    'cluster_fatigue_map': cluster_fatigue_map,
    'scaler': scaler,
    'feature_names': feature_names,
    'selected_features': feature_names,
    'training_samples': len(X),
    'training_date': pd.Timestamp.now().isoformat()
}

# Guardar modelo
model_path = 'ml_models/fatigue_model.pkl'
joblib.dump(model_package, model_path)
print(f"✅ Modelo guardado: {model_path}")

# Guardar metadata
metadata = {
    'model_type': 'kmeans',
    'algorithm': 'K-Means',
    'n_clusters': optimal_k,
    'training_samples': len(X),
    'features_count': len(feature_names),
    'features': feature_names,
    'selected_features': feature_names,
    'cluster_fatigue_map': cluster_fatigue_map,
    'training_date': pd.Timestamp.now().isoformat(),
    'model_path': model_path,
    'cluster_distribution': {
        f'cluster_{i}': int(np.sum(clusters == i))
        for i in range(optimal_k)
    }
}

metadata_path = 'ml_models/model_metadata.json'
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"✅ Metadata guardada: {metadata_path}")

print("\n"+"="*80)
print("✅ MODELO ENTRENADO Y GUARDADO EXITOSAMENTE")
print("="*80)
print(f"\nArchivos generados:")
print(f"  • {model_path}")
print(f"  • {metadata_path}")
print(f"\nReinicia el servidor Django para cargar el modelo nuevo:")
print(f"  python manage.py runserver")
