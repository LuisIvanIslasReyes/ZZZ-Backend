# 🤖 SISTEMA DE RECOMENDACIONES CON MACHINE LEARNING

## 📋 Índice
1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Modelo de Machine Learning](#modelo-de-machine-learning)
4. [Sistema de Recomendaciones](#sistema-de-recomendaciones)
5. [Tipos de Recomendaciones](#tipos-de-recomendaciones)
6. [Flujo Completo](#flujo-completo)
7. [Uso del Sistema](#uso-del-sistema)
8. [Ejemplos Prácticos](#ejemplos-prácticos)

---

## 📖 Descripción General

El sistema utiliza **Machine Learning** para analizar patrones de fatiga en empleados y generar **recomendaciones inteligentes** para supervisores y empleados, con el objetivo de optimizar las rutinas laborales y prevenir fatiga crónica.

### Componentes Principales:

```
┌─────────────────────────────────────────────────────────────┐
│                    DATOS DE SENSORES                        │
│  ESP32 → MQTT → SensorData (cada 5 segundos)              │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              PROCESAMIENTO AUTOMÁTICO                       │
│  • Agrupa datos en ventanas de 1 minuto                   │
│  • Calcula métricas avanzadas (HRV, SpO2, actividad)      │
│  • ML predice índice de fatiga                            │
│  → ProcessedMetrics                                        │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         ANÁLISIS DE PATRONES (últimos 7 días)              │
│  • RecommendationService analiza tendencias                │
│  • Detecta empleados sobrecargados                         │
│  • Identifica horarios problemáticos                       │
│  • Compara carga de trabajo entre empleados                │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│            GENERACIÓN DE RECOMENDACIONES                    │
│  → Descansos preventivos                                   │
│  → Redistribución de tareas                                │
│  → Rotación de turnos                                      │
│  → RoutineRecommendation (base de datos)                   │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  API REST / FRONTEND                        │
│  Supervisores y empleados ven recomendaciones             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitectura del Sistema

### 1. Capas del Sistema

#### **Capa de Datos** (`apps/sensors/`)
- **SensorData**: Datos crudos de sensores (5 seg)
- **ProcessedMetrics**: Métricas procesadas (1 min)
  - Incluye: HR, SpO2, HRV, actividad, **fatigue_index**

#### **Capa de ML** (`apps/analytics/ml_service.py`)
- **FatigueMLService**: Servicio de predicción de fatiga
- Carga modelo entrenado: `ml_models/fatigue_model.pkl`
- Si no hay modelo → usa cálculo heurístico

#### **Capa de Análisis** (`apps/analytics/recommendation_service.py`)
- **RecommendationService**: Generador de recomendaciones
- Analiza patrones de fatiga (últimos 7 días)
- Genera 3 tipos de recomendaciones

#### **Capa de Presentación** (API REST)
- **RoutineRecommendationViewSet**: Endpoints REST
- Filtros por tipo, prioridad, supervisor
- Acciones: listar, ver detalle, aplicar

### 2. Modelos de Datos

#### **ProcessedMetrics** (Métricas procesadas)
```python
{
  "employee": User,
  "window_start": datetime,
  "window_end": datetime,
  
  # Métricas HR
  "hr_avg": 75.5,
  "hr_max": 85.0,
  "hr_min": 68.0,
  "hrv_rmssd": 45.2,  # Variabilidad
  
  # Métricas SpO2
  "spo2_avg": 97.8,
  "spo2_min": 96.5,
  "desaturation_count": 2,
  
  # Métricas de Actividad
  "activity_level": 3,  # 0-5
  "movement_variance": 0.15,
  
  # Features combinados
  "fatigue_index": 42.5,  # ⭐ PREDICHO POR ML
  "hr_activity_ratio": 1.15
}
```

#### **RoutineRecommendation** (Recomendación)
```python
{
  "supervisor": User (supervisor),
  "employee": User (employee) | None,  # None = recomendación para equipo
  "recommendation_type": "break" | "task_redistribution" | "shift_rotation",
  "description": "Texto descriptivo con análisis",
  "priority": 1-5,  # 1 = más urgente
  "based_on_data": {
    "avg_fatigue": 65.5,
    "max_fatigue": 85.0,
    "analysis_days": 7,
    "peak_hours": [14, 15, 16]
  },
  "is_applied": False,
  "created_at": datetime
}
```

---

## 🧠 Modelo de Machine Learning

### 1. Tipo de Modelo: **K-Means Clustering**

El sistema usa clustering no supervisado para clasificar niveles de fatiga:

```
┌──────────────────────────────────────────────────────┐
│           FEATURES DE ENTRADA (15-20 variables)      │
├──────────────────────────────────────────────────────┤
│  • hr_avg, hr_max, hr_min                           │
│  • hrv_rmssd, hrv_sdnn (variabilidad cardíaca)      │
│  • spo2_avg, spo2_min, spo2_variance                │
│  • desaturation_count (eventos de baja oxigenación) │
│  • activity_level, movement_variance                │
│  • hr_activity_ratio (HR vs actividad física)       │
│  • posture_angle, entropy                           │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│              NORMALIZACIÓN (StandardScaler)          │
│  Cada feature se normaliza: (x - μ) / σ             │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│            MODELO K-MEANS (k=3-5 clusters)           │
│  Agrupa patrones similares de fatiga                │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│          MAPEO CLUSTER → NIVEL DE FATIGA             │
│  Cluster 0 → Fatiga Baja (20-35)                    │
│  Cluster 1 → Fatiga Media (40-65)                   │
│  Cluster 2 → Fatiga Alta (70-90)                    │
└──────────────────────────────────────────────────────┘
```

### 2. Entrenamiento del Modelo

#### Pasos para entrenar:

```bash
# Opción 1: Script automático
python SCRIPTS/train_ml_model.py

# Opción 2: Manual
python notebooks/01_data_exploration.py     # Análisis exploratorio
python notebooks/02_feature_engineering.py  # Ingeniería de features
python notebooks/03_clustering_model.py     # Entrena K-Means
```

#### Archivos generados:
```
ml_models/
├── fatigue_model.pkl           # Modelo principal (K-Means)
├── fatigue_model_dbscan.pkl    # Alternativo DBSCAN
└── model_metadata.json         # Información del modelo
```

### 3. Cálculo de Fatiga

#### Con modelo ML:
```python
from apps.analytics.ml_service import FatigueMLService

ml_service = FatigueMLService()
metrics = {
    "hr_avg": 85.0,
    "spo2_avg": 96.5,
    "hrv_rmssd": 30.0,
    "activity_level": 2,
    # ... otros features
}
fatigue_index = ml_service.predict_fatigue_index(metrics)
# → 72.5 (fatiga alta)
```

#### Sin modelo ML (fallback heurístico):
```python
# Componentes ponderados:
fatigue = (
    hr_activity_score * 0.40 +    # ¿HR alto para la actividad?
    spo2_score * 0.30 +            # ¿SpO2 bajo?
    hrv_score * 0.20 +             # ¿HRV bajo? (estrés)
    desaturation_score * 0.10      # ¿Desaturaciones?
)
```

### 4. Métricas de Evaluación

```python
# Métricas usadas para evaluar el modelo:
- Silhouette Score: ~0.45-0.65 (bueno)
- Davies-Bouldin Index: <1.5 (mejor)
- Calinski-Harabasz Score: >100 (mejor)
```

---

## 🎯 Sistema de Recomendaciones

### 1. Servicio Principal: `RecommendationService`

```python
from apps.analytics.recommendation_service import RecommendationService

# Generar para todos los supervisores
service = RecommendationService()
result = service.generate_all_recommendations()

# Generar para un supervisor específico
service = RecommendationService(supervisor=supervisor_user)
result = service.generate_all_recommendations()
```

### 2. Algoritmo de Análisis

#### Parámetros de análisis:
```python
FATIGUE_HIGH = 70       # Umbral fatiga alta
FATIGUE_MEDIUM = 50     # Umbral fatiga media
FATIGUE_LOW = 30        # Umbral fatiga baja
ANALYSIS_DAYS = 7       # Analizar últimos 7 días
MIN_DATA_POINTS = 20    # Mínimo de métricas confiables
```

#### Proceso de análisis:
```python
Para cada supervisor:
  Para cada empleado del supervisor:
    1. Obtener métricas de últimos 7 días
    2. Calcular estadísticas:
       - Fatiga promedio
       - Fatiga máxima
       - Desviación estándar
       - Episodios de fatiga alta (>70)
    3. Analizar patrones:
       - Horarios de pico de fatiga
       - Días problemáticos
       - Tendencias
    4. Generar recomendaciones apropiadas
```

### 3. Priorización

```python
Prioridad 5 (más urgente):
  - Fatiga promedio > 70
  - Diferencia entre empleados > 30 puntos

Prioridad 4:
  - Fatiga máxima > 85
  - Muchos episodios de fatiga alta (>5)
  - Rotación de turnos necesaria

Prioridad 3:
  - Fatiga promedio 50-70
  - Desbalance moderado
  - Patrones detectados

Prioridad 2-1: Recomendaciones preventivas
```

---

## 🔄 Tipos de Recomendaciones

### 1. ⏸️ Descansos Preventivos (`break`)

**Cuándo se genera:**
- Fatiga promedio ≥ 50 en últimos 7 días
- Más de 5 episodios de fatiga alta
- Pico de fatiga ≥ 85

**Análisis incluido:**
- Horarios de mayor fatiga
- Frecuencia de episodios
- Tendencia temporal

**Ejemplo de recomendación:**
```markdown
**Empleado:** Juan Pérez

**Razón:** Fatiga promedio elevada (65.5/100) en los últimos 7 días

**Recomendación:**
- Programar descansos preventivos de 15-20 minutos
- Horarios sugeridos: 14:00, 15:00, 16:00

**Estadísticas (7 días):**
- Fatiga promedio: 65.5/100
- Fatiga máxima: 85.0/100
- Episodios de fatiga alta: 8
```

### 2. ⚖️ Redistribución de Tareas (`task_redistribution`)

**Cuándo se genera:**
- Diferencia de fatiga >20 puntos entre empleados
- Desbalance significativo en el equipo
- Empleados sobrecargados vs. con menor carga

**Análisis incluido:**
- Fatiga promedio del equipo
- Empleados sobrecargados (fatiga > promedio + 10)
- Empleados con menor carga (fatiga < promedio - 10)

**Ejemplo de recomendación:**
```markdown
**Desbalance de carga detectado en el equipo**

**Empleados sobrecargados:**
- Juan Pérez: Fatiga promedio 75.5/100
- María López: Fatiga promedio 72.0/100

**Empleados con menor carga:**
- Carlos Gómez: Fatiga promedio 45.0/100
- Ana Martínez: Fatiga promedio 38.5/100

**Recomendación:**
- Redistribuir tareas desde empleados sobrecargados a los de menor carga
- Fatiga promedio del equipo: 57.5/100
- Diferencia máxima: 37.0 puntos

**Beneficio esperado:**
- Equilibrar carga de trabajo
- Reducir fatiga en empleados sobrecargados
- Mejorar eficiencia general del equipo
```

### 3. 🔄 Rotación de Turnos (`shift_rotation`)

**Cuándo se genera:**
- Fatiga alta en horarios específicos
- Fatiga elevada en ciertos días de la semana
- Patrones cronológicos consistentes

**Análisis incluido:**
- Horarios con mayor/menor fatiga
- Días con mejor/peor desempeño
- Patrones de fatiga crónica

**Ejemplo de recomendación:**
```markdown
**Empleado:** Juan Pérez

**Patrones detectados:**
- Fatiga alta en horarios: 14:00, 15:00, 16:00
- Fatiga elevada en días: Lunes, Martes, Miércoles

**Recomendación:**
- Considerar rotación de turno para este empleado
- Horarios con mejor desempeño: 8:00, 9:00, 10:00
- Días con mejor desempeño: Jueves, Viernes

**Beneficio esperado:**
- Reducir fatiga crónica
- Mejorar bienestar del empleado
- Optimizar rendimiento en horarios de menor fatiga
```

---

## 🔄 Flujo Completo

### Diagrama de Flujo

```
┌─────────────────────┐
│ ESP32 DEVICES       │
│ (Cada 5 segundos)   │
└──────┬──────────────┘
       │ MQTT
       ↓
┌─────────────────────┐
│ SensorData          │
│ (Datos crudos)      │
└──────┬──────────────┘
       │ Automático (cada 2 min)
       ↓
┌─────────────────────┐
│ MetricsProcessor    │
│ • Agrega ventanas   │
│ • Calcula HRV, etc. │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ FatigueMLService    │
│ • Predice fatiga    │
│ • Usa modelo K-Means│
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│ ProcessedMetrics    │
│ (con fatigue_index) │
└──────┬──────────────┘
       │ Manual o programado
       ↓
┌─────────────────────┐
│RecommendationService│
│ • Analiza patrones  │
│ • Detecta problemas │
│ • Genera recs.      │
└──────┬──────────────┘
       │
       ↓
┌─────────────────────┐
│RoutineRecommendation│
│ (Base de datos)     │
└──────┬──────────────┘
       │ API REST
       ↓
┌─────────────────────┐
│ FRONTEND            │
│ • Supervisores      │
│ • Empleados         │
└─────────────────────┘
```

### Cronología Típica

```
T+0s:    ESP32 envía datos → SensorData
T+120s:  Procesador automático ejecuta
         → Calcula métricas → ML predice fatiga
         → Guarda en ProcessedMetrics

T+7d:    Se ejecuta (manual/programado):
         python manage.py generate_recommendations --all
         
         → RecommendationService analiza 7 días de datos
         → Genera recomendaciones
         → Guarda en RoutineRecommendation

T+7d+1m: Frontend consulta:
         GET /api/recommendations/
         
         → Supervisor ve recomendaciones
         → Puede aplicarlas o descartarlas
```

---

## 🚀 Uso del Sistema

### 1. Configuración Inicial

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Verificar estado del sistema
python SCRIPTS/setup_ml_recommendations.py
```

### 2. Generar Datos de Prueba

```bash
# Opción 1: Simulador ESP32 (recomendado 2-5 minutos)
python SCRIPTS/esp32_simulator.py

# Opción 2: Datos sintéticos mensuales
python manage.py generate_monthly_data --days 30
```

### 3. Procesamiento de Métricas

```bash
# Automático: Se ejecuta cada 2 minutos con runserver
python manage.py runserver

# Manual (si es necesario)
python manage.py process_metrics
```

### 4. Entrenar Modelo ML (Opcional)

```bash
# Si quieres usar ML en vez de cálculo heurístico
python SCRIPTS/train_ml_model.py
```

### 5. Generar Recomendaciones

```bash
# Para todos los supervisores
python manage.py generate_recommendations --all

# Para un supervisor específico
python manage.py generate_recommendations --supervisor-id 5
```

### 6. Consumir en Frontend

#### Listar recomendaciones
```javascript
// GET /api/recommendations/
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "recommendation_type": "break",
      "priority": 4,
      "employee": {
        "id": 10,
        "full_name": "Juan Pérez"
      },
      "description": "...",
      "created_at": "2025-11-24T10:30:00Z",
      "is_applied": false
    },
    // ...
  ]
}
```

#### Filtrar por tipo
```javascript
// GET /api/recommendations/?type=break
// GET /api/recommendations/?type=task_redistribution
// GET /api/recommendations/?type=shift_rotation
```

#### Filtrar por prioridad
```javascript
// GET /api/recommendations/?priority=5  // Más urgentes
// GET /api/recommendations/?priority__gte=4  // Prioridad alta
```

#### Ver detalle
```javascript
// GET /api/recommendations/1/
{
  "id": 1,
  "supervisor": {
    "id": 5,
    "full_name": "Carlos Supervisor"
  },
  "employee": {
    "id": 10,
    "full_name": "Juan Pérez"
  },
  "recommendation_type": "break",
  "description": "...",
  "priority": 4,
  "based_on_data": {
    "avg_fatigue": 65.5,
    "max_fatigue": 85.0,
    "high_fatigue_count": 8,
    "peak_hours": [14, 15, 16]
  },
  "is_applied": false,
  "created_at": "2025-11-24T10:30:00Z"
}
```

#### Aplicar recomendación
```javascript
// POST /api/recommendations/1/apply/
{
  "message": "Recomendación aplicada exitosamente",
  "recommendation": { /* ... */ }
}
```

#### Estadísticas
```javascript
// GET /api/recommendations/stats/
{
  "total": 15,
  "pending": 10,
  "applied": 5,
  "by_type": {
    "break": 6,
    "task_redistribution": 3,
    "shift_rotation": 1
  },
  "by_priority": {
    "5": 2,
    "4": 5,
    "3": 3
  }
}
```

---

## 💡 Ejemplos Prácticos

### Ejemplo 1: Flujo Completo para Supervisor

```python
# Backend: Generar recomendaciones
$ python manage.py generate_recommendations --all

# Frontend: Supervisor consulta recomendaciones
GET /api/recommendations/?supervisor__id=5&is_applied=false

# Respuesta:
[
  {
    "id": 1,
    "type": "break",
    "priority": 4,
    "employee": "Juan Pérez",
    "summary": "Fatiga alta (65.5/100) - Descansos en 14:00, 15:00, 16:00"
  },
  {
    "id": 2,
    "type": "task_redistribution",
    "priority": 5,
    "summary": "Desbalance de 37 puntos entre empleados"
  }
]

# Supervisor ve detalles
GET /api/recommendations/1/

# Supervisor aplica la recomendación
POST /api/recommendations/1/apply/
```

### Ejemplo 2: Empleado ve sus Recomendaciones

```python
# Frontend: Empleado consulta sus recomendaciones
GET /api/recommendations/?employee__id=10

# Respuesta:
[
  {
    "id": 1,
    "type": "break",
    "priority": 4,
    "message": "Tu supervisor recomienda descansos de 15 min a las 14:00, 15:00, 16:00",
    "reason": "Se detectó fatiga promedio de 65.5/100 en últimos 7 días"
  }
]
```

### Ejemplo 3: Análisis Programático

```python
# Shell de Django
python manage.py shell

from apps.analytics.models import RoutineRecommendation
from django.db.models import Count

# Ver recomendaciones por tipo
stats = RoutineRecommendation.objects.values('recommendation_type').annotate(
    count=Count('id')
)
for s in stats:
    print(f"{s['recommendation_type']}: {s['count']}")

# Empleados con más recomendaciones
from django.db.models import Count
employees = RoutineRecommendation.objects.values(
    'employee__first_name', 'employee__last_name'
).annotate(
    rec_count=Count('id')
).order_by('-rec_count')[:5]

for e in employees:
    print(f"{e['employee__first_name']} {e['employee__last_name']}: {e['rec_count']}")
```

---

## 📊 Casos de Uso

### Caso 1: Prevención de Fatiga Individual
**Escenario:** Juan muestra fatiga promedio de 68/100 en últimos 7 días

**Sistema detecta:**
- 9 episodios con fatiga > 70
- Picos a las 14:00, 15:00, 16:00

**Recomendación generada:**
- Tipo: `break`
- Prioridad: 4
- Acción: Descansos de 15 min en horarios específicos

### Caso 2: Desbalance de Equipo
**Escenario:** 
- Juan: 75/100 fatiga promedio
- María: 72/100
- Carlos: 40/100
- Ana: 35/100

**Sistema detecta:**
- Diferencia de 40 puntos
- Desbalance significativo

**Recomendación generada:**
- Tipo: `task_redistribution`
- Prioridad: 5 (urgente)
- Acción: Redistribuir tareas de Juan/María hacia Carlos/Ana

### Caso 3: Fatiga Cronológica
**Escenario:** María muestra fatiga alta consistentemente los lunes y martes

**Sistema detecta:**
- Lunes: 78/100 promedio
- Martes: 75/100 promedio
- Jueves/Viernes: 45/100 promedio

**Recomendación generada:**
- Tipo: `shift_rotation`
- Prioridad: 4
- Acción: Considerar cambio de días laborales o inicio de semana con menor carga

---

## 🎓 Conclusión

El sistema de recomendaciones con ML proporciona:

✅ **Análisis automático** de patrones de fatiga  
✅ **Predicción precisa** con Machine Learning  
✅ **Recomendaciones personalizadas** por empleado y equipo  
✅ **Priorización inteligente** de acciones  
✅ **API REST** para integración con frontend  
✅ **Escalable** y extensible a nuevos tipos de recomendaciones  

### Próximos Pasos

1. **Para desarrolladores:**
   - Ejecutar `python SCRIPTS/setup_ml_recommendations.py`
   - Revisar código en `apps/analytics/`
   - Entrenar modelo ML con datos reales

2. **Para supervisores:**
   - Revisar recomendaciones en el dashboard
   - Aplicar recomendaciones prioritarias
   - Monitorear efectividad

3. **Para administradores:**
   - Programar generación automática de recomendaciones
   - Monitorear métricas del sistema
   - Ajustar umbrales según necesidades

---

**Documentación actualizada:** 24 de noviembre de 2025  
**Versión del sistema:** 1.0.0  
**Autor:** Sistema de Detección de Fatiga Laboral
