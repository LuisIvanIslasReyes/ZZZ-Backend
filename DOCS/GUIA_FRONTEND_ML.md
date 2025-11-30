# 🎯 GUÍA FRONTEND - Dashboard Machine Learning

**Backend:** ✅ 100% Listo  
**Tu trabajo:** Crear la UI con estos endpoints

---

## 📍 Endpoints Disponibles

Base URL: `http://localhost:8000`

### 1️⃣ Información del Modelo
```http
GET /api/ml/model-info/
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "model_exists": true,
  "model_size_mb": 0.09,
  "ml_service": {
    "type": "KMEANS",
    "features_count": 10,
    "features": ["movement_variance", "activity_normalized", "spo2_variance", ...]
  },
  "training": {
    "samples": 21438,
    "date": "2025-11-29T19:02:00",
    "clusters": 2,
    "cluster_fatigue_map": {"0": 50.27, "1": 60.79}
  },
  "quality_metrics": {
    "silhouette_score": 0.9262
  }
}
```

---

### 2️⃣ Estadísticas
```http
GET /api/ml/statistics/
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "predictions": {
    "total": 120,
    "last_24h": 48,
    "average_fatigue": 51.23
  },
  "fatigue_distribution": {
    "normal": 85,
    "moderate": 25,
    "high": 10
  }
}
```

---

### 3️⃣ Estado Re-entrenamiento
```http
GET /api/ml/retraining/
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "last_training": "2025-11-29T19:02:00",
  "next_scheduled": "2025-12-06T19:02:00",
  "available_metrics": 120,
  "min_required": 100,
  "can_retrain": true,
  "status": "ready"
}
```

---

### 4️⃣ Iniciar Re-entrenamiento (Solo Admin/Supervisor)
```http
POST /api/ml/retraining/
Authorization: Bearer <token>
Content-Type: application/json

{
  "force": false
}
```

**Respuesta (202):**
```json
{
  "status": "started",
  "message": "Re-entrenamiento iniciado",
  "estimated_time": "1-2 minutos"
}
```

---

### 5️⃣ Historial Predicciones
```http
GET /api/ml/predictions/history/?limit=50
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "count": 50,
  "predictions": [
    {
      "id": 120,
      "timestamp": "2025-11-29T18:30:00",
      "device": "ESP32-001",
      "employee": "Juan Pérez",
      "fatigue_index": 52.34,
      "hr_avg": 78.5,
      "spo2_avg": 97.2,
      "classification": "normal"
    }
  ]
}
```

---

## 🎨 Qué Mostrar en la UI

### Card 1: Modelo Actual
```
┌─────────────────────────────────┐
│ 📊 Modelo Actual       [Activo] │
├─────────────────────────────────┤
│ Algoritmo:    K-Means           │
│ Características: 10             │
│ Muestras:     21,438            │
│ Score:        0.9262 (🟢 Excelente) │
│                                 │
│ Cluster 0: 50.3% fatiga         │
│ Cluster 1: 60.8% fatiga         │
└─────────────────────────────────┘
```

**Fuente:** `GET /api/ml/model-info/`

---

### Card 2: Estadísticas
```
┌─────────────────────────────────┐
│ 📈 Estadísticas                 │
├─────────────────────────────────┤
│ Total:      120 predicciones    │
│ Últimas 24h: 48                 │
│ Promedio:   51.23% fatiga       │
│                                 │
│ Normal:    ████████ 85          │
│ Moderado:  ███ 25               │
│ Alto:      █ 10                 │
└─────────────────────────────────┘
```

**Fuente:** `GET /api/ml/statistics/`

---

### Card 3: Re-entrenamiento
```
┌─────────────────────────────────┐
│ 🔄 Re-entrenamiento             │
├─────────────────────────────────┤
│ Último: 29/11/2025 19:02        │
│ Próximo: En 6 días              │
│                                 │
│ Datos: 120 / 100 ✅             │
│                                 │
│ [Re-entrenar Ahora]             │
└─────────────────────────────────┘
```

**Fuente:** `GET /api/ml/retraining/`  
**Acción:** `POST /api/ml/retraining/` (botón)

**Flujo al hacer clic:**
1. Usuario → Click botón
2. Frontend → `POST /api/ml/retraining/`
3. Backend → Inicia entrenamiento (background)
4. Frontend → Mostrar spinner "Re-entrenando..."
5. Frontend → Polling cada 10s a `/api/ml/model-info/`
6. Cuando `training.date` cambie → Toast "✅ Completado"

---

### Card 4: Historial
```
┌──────────────────────────────────────────────────────┐
│ 📜 Historial                                         │
├──────────────────────────────────────────────────────┤
│ Fecha/Hora  Dispositivo  Empleado    Fatiga  Estado │
│ 29/11 18:30 ESP32-001   Juan Pérez   52%    🟢     │
│ 29/11 18:28 ESP32-002   María García 68%    🔴     │
└──────────────────────────────────────────────────────┘
```

**Fuente:** `GET /api/ml/predictions/history/?limit=50`

---

### Card 5: Visualizaciones (Gráficos del Modelo)

```
┌──────────────────────────────────────────────────────┐
│ 📊 Visualizaciones del Modelo                        │
├──────────────────────────────────────────────────────┤
│ [Análisis de Clustering] [Feature Engineering]       │
│                                                      │
│  [IMAGEN: 7 gráficos de clustering]                 │
│  - Elbow Method                                     │
│  - Silhouette Score                                 │
│  - PCA/t-SNE                                        │
│  - Distribución clusters                            │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**URLs de las imágenes:**
```javascript
// Análisis de clustering (7 gráficos en 1 imagen)
http://localhost:8000/media/ml_visualizations/clustering_analysis.png

// Feature engineering (correlaciones)
http://localhost:8000/media/ml_visualizations/feature_engineering.png
```

**Código para mostrar:**
```jsx
<div className="visualizations-card">
  <h2>📊 Visualizaciones</h2>
  
  <div className="tabs">
    <button onClick={() => setTab('clustering')}>Clustering</button>
    <button onClick={() => setTab('features')}>Features</button>
  </div>
  
  {tab === 'clustering' ? (
    <img 
      src="http://localhost:8000/media/ml_visualizations/clustering_analysis.png"
      alt="Análisis de clustering K-Means"
      style={{ width: '100%', height: 'auto' }}
    />
  ) : (
    <img 
      src="http://localhost:8000/media/ml_visualizations/feature_engineering.png"
      alt="Análisis de características"
      style={{ width: '100%', height: 'auto' }}
    />
  )}
</div>
```

**Lo que muestran las imágenes:**
- `clustering_analysis.png` → 7 gráficos del modelo K-Means (elbow, silhouette, PCA, t-SNE, distribuciones)
- `feature_engineering.png` → Correlación entre las 10 características biométricas

---

## 🎨 Colores

**Fatiga:**
- 🟢 Normal (<55%): `#10b981`
- 🟡 Moderado (55-65%): `#f59e0b`
- 🔴 Alto (>65%): `#ef4444`

**Score:**
- 🟢 Excelente (≥0.8): `#10b981`
- 🟡 Bueno (0.6-0.8): `#f59e0b`
- 🔴 Mejorable (<0.6): `#ef4444`

---

## ⏰ Auto-actualización

```javascript
// Actualizar cada cierto tiempo
setInterval(() => fetchModelInfo(), 30000);     // 30s
setInterval(() => fetchStatistics(), 60000);     // 60s
setInterval(() => fetchRetrainingStatus(), 300000); // 5min
```

---

## 🔐 Permisos

| Acción | Admin | Supervisor | Employee |
|--------|-------|------------|----------|
| Ver modelo | ✅ | ✅ | ✅ |
| Ver estadísticas | ✅ Todas | ✅ Su empresa | ❌ |
| Ver historial | ✅ Todas | ✅ Su empresa | ✅ Sus datos |
| Re-entrenar | ✅ | ✅ | ❌ |

---

## 📱 Ruta

**URL:** `/dashboard/machine-learning`

**Navegación:** Agregar link en el menú principal:
```jsx
<NavLink to="/dashboard/machine-learning">
  🧠 Machine Learning
</NavLink>
```

---

## 🧪 Probar Backend

```bash
# Terminal 1: Servidor
python manage.py runserver

# Terminal 2: Tests
python SCRIPTS\TEST\test_ml_endpoints.py
```

**Salida esperada:**
```
✅ Model Info funcionando correctamente
✅ Statistics funcionando correctamente
✅ Retraining Status funcionando correctamente
✅ Prediction History funcionando correctamente
```

---

## 📦 Código Base

### Servicio API (JavaScript/TypeScript)

```javascript
// services/mlApi.js
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const getToken = () => localStorage.getItem('token');

export const mlApi = {
  // 1. Info del modelo
  getModelInfo: async () => {
    const { data } = await axios.get(`${API_URL}/api/ml/model-info/`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return data;
  },

  // 2. Estadísticas
  getStatistics: async () => {
    const { data } = await axios.get(`${API_URL}/api/ml/statistics/`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return data;
  },

  // 3. Estado re-entrenamiento
  getRetrainingStatus: async () => {
    const { data } = await axios.get(`${API_URL}/api/ml/retraining/`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return data;
  },

  // 4. Iniciar re-entrenamiento
  startRetraining: async (force = false) => {
    const { data } = await axios.post(
      `${API_URL}/api/ml/retraining/`,
      { force },
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // 5. Historial
  getPredictionHistory: async (limit = 50) => {
    const { data } = await axios.get(
      `${API_URL}/api/ml/predictions/history/?limit=${limit}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  }
};
```

---

### Página Principal (React)

```jsx
// pages/MachineLearningDashboard.jsx
import React, { useState, useEffect } from 'react';
import { mlApi } from '../services/mlApi';

export const MachineLearningDashboard = () => {
  const [modelInfo, setModelInfo] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [retrainingStatus, setRetrainingStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    
    // Auto-refresh
    const interval1 = setInterval(() => mlApi.getModelInfo().then(setModelInfo), 30000);
    const interval2 = setInterval(() => mlApi.getStatistics().then(setStatistics), 60000);
    
    return () => {
      clearInterval(interval1);
      clearInterval(interval2);
    };
  }, []);

  const loadData = async () => {
    try {
      const [model, stats, retraining] = await Promise.all([
        mlApi.getModelInfo(),
        mlApi.getStatistics(),
        mlApi.getRetrainingStatus()
      ]);
      
      setModelInfo(model);
      setStatistics(stats);
      setRetrainingStatus(retraining);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Cargando...</div>;

  return (
    <div className="ml-dashboard">
      <h1>🧠 Machine Learning Dashboard</h1>
      
      {/* Card 1: Modelo */}
      <div className="card">
        <h2>📊 Modelo Actual</h2>
        {modelInfo?.model_exists ? (
          <>
            <p>Algoritmo: {modelInfo.training.algorithm}</p>
            <p>Características: {modelInfo.ml_service.features_count}</p>
            <p>Muestras: {modelInfo.training.samples.toLocaleString()}</p>
            <p>Score: {modelInfo.quality_metrics.silhouette_score?.toFixed(4)}</p>
          </>
        ) : (
          <p>⚠️ Modelo no entrenado</p>
        )}
      </div>

      {/* Card 2: Estadísticas */}
      <div className="card">
        <h2>📈 Estadísticas</h2>
        <p>Total: {statistics?.predictions.total}</p>
        <p>Últimas 24h: {statistics?.predictions.last_24h}</p>
        <p>Promedio: {statistics?.predictions.average_fatigue}%</p>
      </div>

      {/* Card 3: Re-entrenamiento */}
      <div className="card">
        <h2>🔄 Re-entrenamiento</h2>
        <p>Último: {new Date(retrainingStatus?.last_training).toLocaleString()}</p>
        <p>Datos: {retrainingStatus?.available_metrics} / {retrainingStatus?.min_required}</p>
        <button 
          onClick={handleRetrain}
          disabled={!retrainingStatus?.can_retrain}
        >
          Re-entrenar Ahora
        </button>
      </div>
    </div>
  );
};
```

---

### Función Re-entrenamiento

```javascript
const handleRetrain = async () => {
  if (!window.confirm('¿Iniciar re-entrenamiento? (1-2 min)')) return;
  
  try {
    setRetraining(true);
    await mlApi.startRetraining();
    
    // Polling hasta que cambie la fecha
    const lastDate = modelInfo.training.date;
    const pollInterval = setInterval(async () => {
      const newData = await mlApi.getModelInfo();
      
      if (newData.training.date !== lastDate) {
        clearInterval(pollInterval);
        setRetraining(false);
        alert('✅ Modelo re-entrenado exitosamente');
        loadData(); // Recargar todo
      }
    }, 10000); // Cada 10 segundos
    
  } catch (error) {
    alert('❌ Error: ' + error.message);
    setRetraining(false);
  }
};
```

---

## ✅ Checklist

### Backend
- [x] Endpoints implementados
- [x] Rutas configuradas
- [x] Tests funcionando

### Frontend (Tu trabajo)
- [ ] Crear ruta `/dashboard/machine-learning`
- [ ] Crear `mlApi.js` (copiar código de arriba)
- [ ] Crear página `MachineLearningDashboard.jsx`
- [ ] Crear 5 cards:
  - [ ] Modelo (info básica)
  - [ ] Estadísticas (números + gráfico barras)
  - [ ] Re-entrenamiento (botón + polling)
  - [ ] Historial (tabla)
  - [ ] Visualizaciones (imágenes del backend)
- [ ] Implementar auto-refresh
- [ ] Implementar botón re-entrenar con polling
- [ ] Mostrar imágenes de `clustering_analysis.png` y `feature_engineering.png`
- [ ] Agregar estilos CSS
- [ ] Agregar al menú de navegación

---

## 🎯 Prioridad

1. **MVP (mínimo viable):**
   - Card de modelo (info básica)
   - Card de estadísticas (números simples)
   - Historial básico (tabla)
   - **Visualizaciones (mostrar las 2 imágenes)** ← Súper fácil, solo <img>

2. **Mejoras:**
   - Card de re-entrenamiento con botón
   - Gráficos (barras, pie charts)
   - Filtros en historial

3. **Opcionales:**
   - Zoom en visualizaciones
   - Animaciones
   - Exportar datos

---

## 💡 Tips

**Colores de fatiga:**
```javascript
const getFatigueColor = (fatigue) => {
  if (fatigue < 55) return '#10b981'; // Verde
  if (fatigue < 65) return '#f59e0b'; // Amarillo
  return '#ef4444'; // Rojo
};
```

**Formatear números:**
```javascript
const formatNumber = (num) => num.toLocaleString('es-ES');
```

**Formatear fechas:**
```javascript
const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};
```

---

## 📞 Dudas

- **¿El backend funciona?** → Sí, 100% probado
- **¿Qué tengo que hacer?** → Crear la UI con los 5 endpoints + mostrar 2 imágenes
- **¿Cómo pruebo?** → `python SCRIPTS\TEST\test_ml_endpoints.py`
- **¿Permisos?** → Token JWT en header Authorization
- **¿Actualización automática?** → `setInterval` cada 30s/60s
- **¿Las imágenes?** → Backend las sirve en `/media/ml_visualizations/`, solo pon <img src="..." />

---

## 🚨 Troubleshooting: "Error al cargar modelo"

### ⚠️ Problema: Sale error al cargar el modelo

**Síntoma:** El endpoint `/api/ml/model-info/` devuelve `model_exists: false` o error 500.

**Causa:** El archivo del modelo (`ml_models/fatigue_model.pkl`) **NO está en git** (no se sube al repo).

---

### ✅ Solución: Entrenar el modelo

**Método 1 - Rápido (1-2 minutos):**
```bash
# Asegúrate de tener datos en la BD (mínimo 100 métricas)
python train_simple_model.py
```

**Método 2 - Desde Django admin (si hay datos):**
```bash
python manage.py retrain_model
```

**Método 3 - Con botón del frontend (cuando esté implementado):**
- Abrir `/dashboard/machine-learning`
- Click en "Re-entrenar Ahora"

---

### 🔍 Verificar si hay datos suficientes

```bash
python manage.py shell
```

```python
from apps.sensors.models import ProcessedMetrics
print(f"Métricas disponibles: {ProcessedMetrics.objects.count()}")
# Necesitas mínimo 100
```

---

### 📦 Si NO hay datos (repo recién clonado)

**Opción A - Generar datos históricos:**
```bash
python UTILS\generate_historical_data.py
```

**Opción B - Iniciar simuladores y esperar:**
```bash
# Terminal 1
python manage.py runserver

# Terminal 2
python UTILS\start_simulator.bat

# Esperar 5-10 minutos, luego entrenar
python train_simple_model.py
```

**Opción C - Copiar modelo de otro dev (más rápido):**
Si otro desarrollador ya tiene el modelo, puede compartir:
- `ml_models/fatigue_model.pkl` (87 KB)
- `ml_models/model_metadata.json` (2 KB)

Copiar esos 2 archivos en la misma ruta.

---

### 🎨 Cómo el Frontend debe manejar el error

**Estado 1: Sin modelo entrenado**
```jsx
{!modelInfo?.model_exists ? (
  <div className="alert alert-warning">
    <h3>⚠️ Modelo no entrenado</h3>
    <p>El modelo de Machine Learning aún no ha sido entrenado.</p>
    
    <div className="info-box">
      <p><strong>Datos disponibles:</strong> {retrainingStatus?.available_metrics || 0} métricas</p>
      <p><strong>Mínimo necesario:</strong> {retrainingStatus?.min_required || 100} métricas</p>
      
      {retrainingStatus?.available_metrics < retrainingStatus?.min_required ? (
        <p className="text-warning">
          ⏳ Esperando más datos... ({Math.round((retrainingStatus?.available_metrics / retrainingStatus?.min_required) * 100)}%)
        </p>
      ) : (
        <p className="text-success">✅ Suficientes datos para entrenar</p>
      )}
    </div>
    
    {retrainingStatus?.can_retrain && (
      <button onClick={handleRetrain} className="btn btn-primary">
        🚀 Entrenar Modelo Ahora
      </button>
    )}
    
    <details className="mt-3">
      <summary>Instrucciones para desarrolladores</summary>
      <ol>
        <li>Asegúrate que los simuladores estén corriendo</li>
        <li>Espera a tener mínimo 100 métricas procesadas</li>
        <li>Ejecuta: <code>python train_simple_model.py</code></li>
      </ol>
    </details>
  </div>
) : (
  // Mostrar info normal del modelo
  <ModelInfoCards data={modelInfo} />
)}
```

**Estado 2: Error 500 (otro problema)**
```jsx
{error && (
  <div className="alert alert-error">
    <h3>❌ Error al cargar información ML</h3>
    <p>{error.message || 'Error desconocido'}</p>
    <button onClick={loadData}>🔄 Reintentar</button>
  </div>
)}
```

---

### 📋 Checklist para nuevo desarrollador

Cuando alguien clone el repo por primera vez:

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Migrar BD
python manage.py migrate

# 3. Crear superusuario
python manage.py createsuperuser

# 4. Iniciar servidor
python manage.py runserver

# 5. En otra terminal: Generar datos
python UTILS\generate_historical_data.py

# 6. Entrenar modelo
python train_simple_model.py

# 7. Verificar
python SCRIPTS\TEST\test_ml_endpoints.py
```

**Tiempo total:** ~5 minutos

---

## 📸 Ubicación de las Imágenes

**En el servidor:**
- `notebooks/clustering_analysis.png` (264 KB) - 7 gráficos del modelo
- `notebooks/feature_engineering.png` - Correlación de características

**URL para el frontend:**
```
http://localhost:8000/media/ml_visualizations/clustering_analysis.png
http://localhost:8000/media/ml_visualizations/feature_engineering.png
```

**El backend YA las sirve automáticamente** (configurado en `config/urls.py`).  
Solo tienes que poner la URL en un `<img>` o descargarlas si quieres hospedarlas en tu servidor de frontend.

**Ejemplo rápido:**
```jsx
<img 
  src="http://localhost:8000/media/ml_visualizations/clustering_analysis.png"
  alt="Análisis ML"
  style={{ width: '100%' }}
/>
```

---

**Fecha:** 29/11/2025  
**Backend:** ✅ Listo (API + Imágenes)  
**Frontend:** 📋 Pendiente (esta guía)
