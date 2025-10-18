# 🧠 Arquitectura de Machine Learning

## Roadmap de ML para Detección de Estrés

### Fase 1: Baseline Heurístico (Actual) ✅

**Estado:** Implementado en `apps/devices/tasks.py`

El sistema actual usa un modelo heurístico simple:

```python
stress_score = (hr_component * 0.4) + (hrv_component * 0.3) + (movement_component * 0.3)
```

**Ventajas:**
- Funciona sin datos de entrenamiento
- Interpretable y rápido
- Baseline para comparación

**Limitaciones:**
- No aprende patrones individuales
- Sensibilidad fija
- No considera contexto temporal complejo

---

### Fase 2: Feature Engineering 🔄

**Objetivo:** Extraer features significativas de los datos de sensores

#### Features Propuestas

**Dominio del tiempo (HR):**
- Media, mediana, std, min, max
- Percentiles (25, 75, 90)
- Rango (max - min)
- Cambios bruscos (derivada)

**Variabilidad de HR (HRV):**
- SDNN (desviación estándar de intervalos NN)
- RMSSD (raíz cuadrada de diferencias sucesivas)
- pNN50 (% de intervalos que difieren >50ms)

**Actividad física:**
- Magnitud de aceleración
- Energía espectral (FFT)
- Duración de actividad vs reposo
- Pasos por minuto

**Contexto temporal:**
- Hora del día (sin encoding)
- Día de la semana
- Duración de la jornada
- Tiempo desde último descanso

**Features agregadas:**
- Ventanas deslizantes (5min, 15min, 1h)
- Tendencias (primera diferencia)
- Comparación con baseline personal

#### Implementación

Crear nueva tarea Celery:

```python
@shared_task
def extract_features(employee_id, window_start, window_end):
    """
    Extract ML features from sensor samples
    """
    samples = SensorSample.objects.filter(
        packet__device__employee_id=employee_id,
        sample_time__range=(window_start, window_end)
    )
    
    features = {
        'hr_mean': ...,
        'hr_std': ...,
        'hrv_rmssd': ...,
        'movement_energy': ...,
        'hour_of_day': ...,
        # ... más features
    }
    
    return features
```

---

### Fase 3: Etiquetado de Datos 📊

**Problema:** Necesitamos ground truth para entrenar un modelo supervisado.

#### Estrategias de Etiquetado

**1. Auto-reporte del empleado**
- Encuestas rápidas en la app móvil
- "¿Cómo te sientes? 😊😐😟😰"
- Preguntar cada 2-4 horas
- Almacenar en modelo `StressLabel`

**2. Eventos conocidos**
- Reuniones importantes
- Entregas de proyectos
- Cambios organizacionales

**3. Proxy labels**
- Productividad medida
- Errores cometidos
- Tiempo de respuesta

#### Modelo de Etiquetas

```python
class StressLabel(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    stress_level = models.IntegerField(
        choices=[
            (1, 'Muy relajado'),
            (2, 'Relajado'),
            (3, 'Normal'),
            (4, 'Estresado'),
            (5, 'Muy estresado')
        ]
    )
    source = models.CharField(max_length=20)  # 'self_report', 'event', 'proxy'
    confidence = models.FloatField(default=1.0)
```

---

### Fase 4: Entrenamiento de Modelo 🎯

#### Dataset

**Estructura:**
```
X: [hr_mean, hr_std, hrv_rmssd, ..., hour_of_day]  # Features
y: [1, 2, 3, 4, 5]  # Stress level
```

**Split:**
- Train: 70%
- Validation: 15%
- Test: 15%

**Consideraciones:**
- Split temporal (no aleatorio) para evitar leakage
- Validación por empleado (leave-one-out) si pocos usuarios

#### Modelos Candidatos

**1. XGBoost (Recomendado para empezar)**
```python
from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    objective='multi:softmax',
    num_class=5
)

model.fit(X_train, y_train)
```

**Ventajas:**
- Funciona bien con pocos datos
- Maneja features faltantes
- Interpretable (feature importance)
- Rápido para inferencia

**2. Random Forest**
- Más robusto a overfitting
- Ensemble de árboles
- Similar rendimiento a XGBoost

**3. Red Neuronal (futuro)**
```python
import torch.nn as nn

class StressNet(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 5)
        )
    
    def forward(self, x):
        return self.layers(x)
```

**Ventajas:**
- Aprende representaciones complejas
- Mejor con muchos datos
- Permite transfer learning

#### Métricas

**Clasificación:**
- Accuracy
- F1-Score (macro, weighted)
- Confusion Matrix
- ROC-AUC (por clase)

**Regresión (si convertimos a score continuo):**
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R² Score

#### Pipeline de Entrenamiento

```python
# scripts/train_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import joblib

# 1. Cargar datos
df = load_features_and_labels()

# 2. Split
X = df.drop('stress_level', axis=1)
y = df['stress_level']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, shuffle=False  # Temporal split
)

# 3. Entrenar
model = XGBClassifier(...)
model.fit(X_train, y_train)

# 4. Evaluar
y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")

# 5. Guardar
joblib.dump(model, 'models/stress_model_v2.pkl')
```

---

### Fase 5: Deployment 🚀

#### Opción A: Modelo en Django (Simple)

```python
# apps/devices/ml_model.py

import joblib
import numpy as np

class StressPredictor:
    def __init__(self):
        self.model = joblib.load('models/stress_model_v2.pkl')
    
    def predict(self, features):
        """
        features: dict with keys matching training features
        returns: stress_score (0-100)
        """
        # Convert to array
        X = np.array([list(features.values())])
        
        # Predict class (1-5)
        stress_class = self.model.predict(X)[0]
        
        # Convert to 0-100 scale
        stress_score = (stress_class - 1) * 25
        
        return stress_score, self.model.predict_proba(X)[0]

# Usar en tasks.py
predictor = StressPredictor()

@shared_task
def process_sensor_packet_ml(packet_id):
    features = extract_features(...)
    stress_score, confidence = predictor.predict(features)
    
    StressAggregate.objects.create(
        stress_score=stress_score,
        confidence=max(confidence),
        method_version='v2.0-xgboost',
        ...
    )
```

**Ventajas:**
- Simple de implementar
- Baja latencia
- No requiere servicios externos

**Desventajas:**
- No escala bien para modelos grandes
- Versionado manual

#### Opción B: Servicio de Inferencia (Avanzado)

**TorchServe / TensorFlow Serving**

```yaml
# docker-compose.yml
services:
  ml-service:
    image: pytorch/torchserve
    volumes:
      - ./models:/models
    ports:
      - "8080:8080"
```

```python
# Llamar desde Django
import requests

def predict_stress(features):
    response = requests.post(
        'http://ml-service:8080/predictions/stress_model',
        json={'features': features}
    )
    return response.json()
```

**Ventajas:**
- Escalable
- Versionado automático
- Monitoreo de modelos
- AB testing fácil

---

### Fase 6: Monitoreo y Mejora Continua 📈

#### Métricas en Producción

**Model Performance:**
- Accuracy en nuevos datos
- Distribución de predicciones
- Drift de features (cambio en distribución)

**Business Metrics:**
- Correlación con auto-reportes
- Alertas útiles vs falsos positivos
- Engagement de empleados con recomendaciones

#### Reentrenamiento

**Trigger de reentrenamiento:**
- Cada N nuevas etiquetas (ej. 1000)
- Cada X días (ej. 30)
- Cuando accuracy cae < threshold

**Pipeline automático:**
```python
@shared_task
def retrain_model():
    # 1. Fetch new data since last training
    # 2. Combine with existing dataset
    # 3. Train new model
    # 4. Evaluate on holdout
    # 5. If better than current: deploy
    # 6. Log metrics to MLflow/Weights&Biases
    pass
```

---

## 🎓 Recursos para Aprender

**Papers relevantes:**
- "Heart Rate Variability as a Measure of Stress" (Thayer et al.)
- "Machine Learning for Stress Detection from Wearable Sensors" (Gjoreski et al.)

**Datasets públicos:**
- WESAD (Wearable Stress and Affect Detection)
- SWELL-KW (Stress in the Workplace)

**Herramientas:**
- scikit-learn: baseline models
- XGBoost/LightGBM: boosting
- PyTorch: deep learning
- MLflow: experiment tracking
- Weights & Biases: model monitoring

---

## 🔮 Futuro: Personalización

**Modelo por empleado:**
- Aprender baseline personal
- Ajustar umbrales individuales
- Detectar anomalías relativas

**Transfer Learning:**
- Pre-entrenar en datos públicos
- Fine-tune con datos propios

**Features avanzadas:**
- Series temporales (LSTM/Transformer)
- Graph Neural Networks (relaciones entre empleados)
- Multi-modal (texto + sensores + calendario)

---

## 📝 Checklist de Implementación

- [ ] Implementar extracción de features avanzadas
- [ ] Crear modelo de StressLabel y endpoints de auto-reporte
- [ ] Recolectar ~1000+ muestras etiquetadas
- [ ] Entrenar modelo baseline (XGBoost)
- [ ] Evaluar y comparar con heurístico
- [ ] Deploy modelo v2 en Celery task
- [ ] Monitorear performance en producción
- [ ] Iterar con feedback de usuarios

---

**Última actualización:** Octubre 2025
