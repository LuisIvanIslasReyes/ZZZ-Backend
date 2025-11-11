"""
Clustering Model - Sistema de Detección de Fatiga
Entrena modelo de clustering para clasificar niveles de fatiga.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import joblib

print("=" * 80)
print("CLUSTERING MODEL - SISTEMA DE DETECCIÓN DE FATIGA")
print("=" * 80)
print()

# 1. CARGAR DATOS
print("📊 1. CARGANDO DATOS PROCESADOS...")
print("-" * 80)

# Verificar que existan los archivos
if not os.path.exists('notebooks/ml_dataset_scaled.csv'):
    print("❌ Error: No existe ml_dataset_scaled.csv")
    print("   Ejecuta primero: python notebooks/02_feature_engineering.py")
    sys.exit(1)

# Cargar dataset normalizado
df = pd.read_csv('notebooks/ml_dataset_scaled.csv')
print(f"✅ Dataset cargado: {len(df)} registros")

# Separar features y target
y = df['fatigue_index'].values
X = df.drop('fatigue_index', axis=1).values
feature_names = df.drop('fatigue_index', axis=1).columns.tolist()

print(f"   Features: {len(feature_names)}")
print(f"   Registros: {len(X)}")
print()

# 2. DETERMINAR NÚMERO ÓPTIMO DE CLUSTERS
print("🔍 2. DETERMINANDO NÚMERO ÓPTIMO DE CLUSTERS (K-Means)")
print("-" * 80)

# Método del codo (Elbow method)
inertias = []
silhouette_scores = []
k_range = range(2, 11)

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    inertias.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(X, labels))
    print(f"   K={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={silhouette_scores[-1]:.4f}")

# Determinar K óptimo (máximo silhouette score)
optimal_k = k_range[np.argmax(silhouette_scores)]
print(f"\n✅ Número óptimo de clusters: {optimal_k} (Silhouette={max(silhouette_scores):.4f})")
print()

# 3. ENTRENAR MODELO K-MEANS
print("🤖 3. ENTRENANDO MODELO K-MEANS")
print("-" * 80)

kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
kmeans_labels = kmeans.fit_predict(X)

# Métricas de evaluación
silhouette = silhouette_score(X, kmeans_labels)
davies_bouldin = davies_bouldin_score(X, kmeans_labels)
calinski = calinski_harabasz_score(X, kmeans_labels)

print(f"✅ Modelo K-Means entrenado")
print(f"\n📊 Métricas de evaluación:")
print(f"   Silhouette Score: {silhouette:.4f} (1.0 = perfecto, 0 = aleatorio)")
print(f"   Davies-Bouldin Index: {davies_bouldin:.4f} (más bajo = mejor)")
print(f"   Calinski-Harabasz Index: {calinski:.2f} (más alto = mejor)")

# Distribución de clusters
unique, counts = np.unique(kmeans_labels, return_counts=True)
print(f"\n📋 Distribución de clusters:")
for cluster, count in zip(unique, counts):
    print(f"   Cluster {cluster}: {count} registros ({count/len(kmeans_labels)*100:.1f}%)")
print()

# 4. ENTRENAR MODELO DBSCAN
print("🤖 4. ENTRENANDO MODELO DBSCAN")
print("-" * 80)

# Determinar eps óptimo
from sklearn.neighbors import NearestNeighbors
nbrs = NearestNeighbors(n_neighbors=5).fit(X)
distances, indices = nbrs.kneighbors(X)
distances = np.sort(distances[:, -1])
eps_optimal = np.percentile(distances, 90)

print(f"   Eps óptimo estimado: {eps_optimal:.4f}")

dbscan = DBSCAN(eps=eps_optimal, min_samples=5)
dbscan_labels = dbscan.fit_predict(X)

# Contar clusters (excluyendo noise = -1)
n_clusters_dbscan = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
n_noise = list(dbscan_labels).count(-1)

print(f"✅ Modelo DBSCAN entrenado")
print(f"\n📊 Resultados:")
print(f"   Clusters encontrados: {n_clusters_dbscan}")
print(f"   Puntos de ruido: {n_noise} ({n_noise/len(dbscan_labels)*100:.1f}%)")

if n_clusters_dbscan > 1:
    # Solo calcular silhouette si hay más de 1 cluster y no todos son noise
    valid_mask = dbscan_labels != -1
    if sum(valid_mask) > 0 and len(set(dbscan_labels[valid_mask])) > 1:
        silhouette_dbscan = silhouette_score(X[valid_mask], dbscan_labels[valid_mask])
        print(f"   Silhouette Score: {silhouette_dbscan:.4f}")
print()

# 5. MAPEAR CLUSTERS A NIVELES DE FATIGA
print("🎯 5. MAPEANDO CLUSTERS A NIVELES DE FATIGA")
print("-" * 80)

# Calcular fatigue_index promedio por cluster
cluster_fatigue_map = {}
for cluster in range(optimal_k):
    mask = kmeans_labels == cluster
    avg_fatigue = y[mask].mean()
    cluster_fatigue_map[cluster] = avg_fatigue

# Ordenar clusters por nivel de fatiga
sorted_clusters = sorted(cluster_fatigue_map.items(), key=lambda x: x[1])

print(f"\n📋 Mapeo de clusters (K-Means):")
for rank, (cluster, avg_fatigue) in enumerate(sorted_clusters):
    mask = kmeans_labels == cluster
    count = sum(mask)
    level = "BAJO" if rank == 0 else "MEDIO" if rank < optimal_k - 1 else "ALTO"
    print(f"   Cluster {cluster} → Fatiga {avg_fatigue:.1f}/100 [{level}] ({count} registros)")

# Crear función de predicción
def predict_fatigue_level(model, scaler_data, features):
    """
    Predice el nivel de fatiga basado en features.
    
    Args:
        model: Modelo de clustering entrenado
        scaler_data: Configuración del scaler
        features: Dict con valores de features
    
    Returns:
        float: Índice de fatiga (0-100)
    """
    # Extraer features en el orden correcto
    feature_values = [features.get(f, 0) for f in scaler_data['selected_features']]
    
    # Normalizar
    X_scaled = scaler_data['scaler'].transform([feature_values])
    
    # Predecir cluster
    cluster = model.predict(X_scaled)[0]
    
    # Mapear a nivel de fatiga
    return cluster_fatigue_map[cluster]

print()

# 6. VISUALIZACIÓN
print("📊 6. GENERANDO VISUALIZACIONES")
print("-" * 80)

fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 6.1 Elbow Method
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(k_range, inertias, 'bo-', linewidth=2, markersize=8)
ax1.set_xlabel('Número de Clusters (k)', fontweight='bold')
ax1.set_ylabel('Inertia', fontweight='bold')
ax1.set_title('Método del Codo (Elbow Method)', fontweight='bold')
ax1.axvline(optimal_k, color='red', linestyle='--', alpha=0.7, label=f'K óptimo = {optimal_k}')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 6.2 Silhouette Score
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(k_range, silhouette_scores, 'go-', linewidth=2, markersize=8)
ax2.set_xlabel('Número de Clusters (k)', fontweight='bold')
ax2.set_ylabel('Silhouette Score', fontweight='bold')
ax2.set_title('Silhouette Score por K', fontweight='bold')
ax2.axvline(optimal_k, color='red', linestyle='--', alpha=0.7, label=f'K óptimo = {optimal_k}')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 6.3 Distribución de clusters
ax3 = fig.add_subplot(gs[0, 2])
ax3.bar(unique, counts, color='steelblue', edgecolor='black', alpha=0.7)
ax3.set_xlabel('Cluster', fontweight='bold')
ax3.set_ylabel('Número de Registros', fontweight='bold')
ax3.set_title(f'Distribución de Clusters (K={optimal_k})', fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# 6.4 PCA - 2 componentes
ax4 = fig.add_subplot(gs[1, :2])
pca_2d = PCA(n_components=2, random_state=42)
X_pca = pca_2d.fit_transform(X)

scatter = ax4.scatter(X_pca[:, 0], X_pca[:, 1], c=kmeans_labels, cmap='viridis', 
                     alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
ax4.scatter(pca_2d.transform(kmeans.cluster_centers_)[:, 0],
           pca_2d.transform(kmeans.cluster_centers_)[:, 1],
           c='red', marker='X', s=300, edgecolors='black', linewidth=2, label='Centroides')
ax4.set_xlabel(f'PC1 ({pca_2d.explained_variance_ratio_[0]*100:.1f}%)', fontweight='bold')
ax4.set_ylabel(f'PC2 ({pca_2d.explained_variance_ratio_[1]*100:.1f}%)', fontweight='bold')
ax4.set_title('K-Means Clustering (PCA 2D)', fontweight='bold', fontsize=14)
ax4.legend()
ax4.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax4, label='Cluster')

# 6.5 Fatigue Index por cluster
ax5 = fig.add_subplot(gs[1, 2])
fatigue_by_cluster = [y[kmeans_labels == i] for i in range(optimal_k)]
bp = ax5.boxplot(fatigue_by_cluster, labels=[f'C{i}' for i in range(optimal_k)],
                patch_artist=True, notch=True)
for patch, color in zip(bp['boxes'], plt.cm.viridis(np.linspace(0, 1, optimal_k))):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax5.set_xlabel('Cluster', fontweight='bold')
ax5.set_ylabel('Fatigue Index', fontweight='bold')
ax5.set_title('Distribución de Fatiga por Cluster', fontweight='bold')
ax5.grid(True, alpha=0.3, axis='y')

# 6.6 t-SNE visualization
ax6 = fig.add_subplot(gs[2, :2])
if len(X) > 50:  # t-SNE requiere suficientes muestras
    tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(X)-1))
    X_tsne = tsne.fit_transform(X)
    scatter = ax6.scatter(X_tsne[:, 0], X_tsne[:, 1], c=y, cmap='RdYlGn_r',
                         alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
    ax6.set_xlabel('t-SNE 1', fontweight='bold')
    ax6.set_ylabel('t-SNE 2', fontweight='bold')
    ax6.set_title('t-SNE: Distribución por Nivel de Fatiga', fontweight='bold', fontsize=14)
    plt.colorbar(scatter, ax=ax6, label='Fatigue Index')
    ax6.grid(True, alpha=0.3)
else:
    ax6.text(0.5, 0.5, 'Insuficientes datos\npara t-SNE\n(min 50 registros)',
            ha='center', va='center', fontsize=12, transform=ax6.transAxes)
    ax6.set_title('t-SNE: Distribución por Nivel de Fatiga', fontweight='bold', fontsize=14)

# 6.7 DBSCAN results
ax7 = fig.add_subplot(gs[2, 2])
if n_clusters_dbscan > 0:
    scatter = ax7.scatter(X_pca[:, 0], X_pca[:, 1], c=dbscan_labels, cmap='Spectral',
                         alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
    ax7.set_xlabel('PC1', fontweight='bold')
    ax7.set_ylabel('PC2', fontweight='bold')
    ax7.set_title(f'DBSCAN Clustering ({n_clusters_dbscan} clusters)', fontweight='bold')
    plt.colorbar(scatter, ax=ax7, label='Cluster')
    ax7.grid(True, alpha=0.3)
else:
    ax7.text(0.5, 0.5, f'DBSCAN:\n{n_clusters_dbscan} clusters\n{n_noise} noise points',
            ha='center', va='center', fontsize=12, transform=ax7.transAxes)
    ax7.set_title('DBSCAN Clustering', fontweight='bold')

fig.suptitle('Clustering Model - Sistema de Detección de Fatiga', fontsize=18, fontweight='bold', y=0.995)
plt.savefig('notebooks/clustering_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Visualización guardada: notebooks/clustering_analysis.png")
print()

# 7. GUARDAR MODELO
print("💾 7. GUARDANDO MODELO Y CONFIGURACIÓN")
print("-" * 80)

# Cargar scaler config
scaler_data = joblib.load('notebooks/scaler_config.pkl')

# Crear directorio para modelos
os.makedirs('ml_models', exist_ok=True)

# Guardar modelo K-Means
model_package = {
    'model': kmeans,
    'model_type': 'kmeans',
    'n_clusters': optimal_k,
    'cluster_fatigue_map': cluster_fatigue_map,
    'scaler': scaler_data['scaler'],
    'feature_names': scaler_data['feature_names'],
    'selected_features': scaler_data['selected_features'],
    'metrics': {
        'silhouette_score': silhouette,
        'davies_bouldin_index': davies_bouldin,
        'calinski_harabasz_index': calinski
    },
    'training_info': {
        'n_samples': len(X),
        'n_features': len(feature_names),
        'optimal_k': optimal_k
    }
}

joblib.dump(model_package, 'ml_models/fatigue_model.pkl')
print("✅ Modelo K-Means guardado: ml_models/fatigue_model.pkl")

# Guardar también DBSCAN
dbscan_package = {
    'model': dbscan,
    'model_type': 'dbscan',
    'n_clusters': n_clusters_dbscan,
    'eps': eps_optimal,
    'scaler': scaler_data['scaler'],
    'feature_names': scaler_data['feature_names'],
    'selected_features': scaler_data['selected_features']
}

joblib.dump(dbscan_package, 'ml_models/fatigue_model_dbscan.pkl')
print("✅ Modelo DBSCAN guardado: ml_models/fatigue_model_dbscan.pkl")

# Guardar metadata
metadata = {
    'kmeans': {
        'n_clusters': optimal_k,
        'silhouette_score': silhouette,
        'davies_bouldin_index': davies_bouldin,
        'calinski_harabasz_index': calinski,
        'cluster_distribution': dict(zip(unique.tolist(), counts.tolist())),
        'cluster_fatigue_map': cluster_fatigue_map
    },
    'dbscan': {
        'n_clusters': n_clusters_dbscan,
        'n_noise': n_noise,
        'eps': eps_optimal
    },
    'data': {
        'n_samples': len(X),
        'n_features': len(feature_names),
        'selected_features': scaler_data['selected_features']
    }
}

import json
with open('ml_models/model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("✅ Metadata guardado: ml_models/model_metadata.json")
print()

# 8. RESUMEN FINAL
print("=" * 80)
print("✅ MODELO DE CLUSTERING ENTRENADO EXITOSAMENTE")
print("=" * 80)
print(f"\n📊 Resumen del Modelo K-Means:")
print(f"   - Número de clusters: {optimal_k}")
print(f"   - Silhouette Score: {silhouette:.4f}")
print(f"   - Davies-Bouldin Index: {davies_bouldin:.4f}")
print(f"   - Calinski-Harabasz Index: {calinski:.2f}")
print(f"   - Registros entrenados: {len(X)}")
print(f"   - Features utilizados: {len(scaler_data['selected_features'])}")
print()
print(f"📁 Archivos generados:")
print(f"   - ml_models/fatigue_model.pkl (modelo principal)")
print(f"   - ml_models/fatigue_model_dbscan.pkl (modelo alternativo)")
print(f"   - ml_models/model_metadata.json (información del modelo)")
print(f"   - notebooks/clustering_analysis.png (visualizaciones)")
print()
print("💡 Próximo paso:")
print("   Crear servicio de ML para integración con Django")
print("   Ejecutar: Crear apps/analytics/ml_service.py")
print()
print("=" * 80)

plt.show()
