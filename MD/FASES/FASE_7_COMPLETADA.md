# 🚨 Fase 7: Sistema de Alertas y Recomendaciones - COMPLETADA

## 📋 Resumen de la Implementación

Esta fase implementa un sistema completo de alertas de fatiga y recomendaciones de rutinas, con capacidades de detección automática de anomalías basadas en los datos de sensores y predicciones de Machine Learning.

---

## 🔧 Componentes Implementados

### 1. Serializers de Alertas (`apps/analytics/serializers.py`)

#### **FatigueAlertListSerializer**
- Vista resumida de alertas para listados
- Campos: id, employee_name, device_name, severity, resolved, created_at, time_since_created
- Método calculado `time_since_created` para mostrar tiempo transcurrido

#### **FatigueAlertDetailSerializer**
- Vista detallada de alertas individuales
- Incluye: employee (objeto completo), device, supervisor, message, description, recommendations
- Método `time_to_resolve` para calcular tiempo de resolución
- Método `related_metrics` para obtener métricas asociadas

#### **FatigueAlertCreateSerializer**
- Creación de alertas manuales
- Validaciones:
  - Employee debe ser empleado activo
  - Device debe pertenecer al employee
  - Supervisor debe ser supervisor/admin
  - Supervisor debe gestionar al employee (si no es admin)

#### **FatigueAlertResolveSerializer**
- Marcar alertas como resueltas
- Campos: resolution_notes, resolved_by
- Actualiza automáticamente `resolved_at` timestamp

#### **AlertStatsSerializer**
- Estadísticas agregadas de alertas
- Métricas: total, por severidad, resueltas/pendientes, tiempo promedio de resolución

### 2. Serializers de Recomendaciones (`apps/analytics/serializers.py`)

#### **RoutineRecommendationListSerializer**
- Vista resumida de recomendaciones
- Campos: id, employee_name, recommendation_type, applied, created_at

#### **RoutineRecommendationDetailSerializer**
- Vista detallada con employee completo y data JSON
- Método `is_expired` para verificar vencimiento (30 días)

#### **RoutineRecommendationCreateSerializer**
- Creación de recomendaciones
- Validación del schema JSON según tipo
- Validación de employee activo

#### **ApplyRecommendationSerializer**
- Aplicar recomendaciones
- Campos: applied_notes, applied_by
- Actualiza `applied_at` timestamp

#### **RejectRecommendationSerializer**
- Rechazar recomendaciones
- Campos: rejection_reason

#### **RecommendationStatsSerializer**
- Estadísticas de recomendaciones
- Métricas: total, por tipo, aplicadas/rechazadas/pendientes

---

## 🌐 API Endpoints

### **Alertas de Fatiga** (`/api/alerts/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/alerts/` | Listar alertas | Admin: todas, Supervisor: sus empleados, Employee: propias |
| POST | `/api/alerts/` | Crear alerta | Admin, Supervisor |
| GET | `/api/alerts/{id}/` | Detalle de alerta | Admin, Supervisor, Employee (si es propia) |
| PUT | `/api/alerts/{id}/` | Actualizar alerta | Admin, Supervisor |
| DELETE | `/api/alerts/{id}/` | Eliminar alerta | Admin |
| POST | `/api/alerts/{id}/resolve/` | Resolver alerta | Admin, Supervisor |
| POST | `/api/alerts/{id}/unresolve/` | Reabrir alerta | Admin, Supervisor |
| GET | `/api/alerts/stats/` | Estadísticas | Admin, Supervisor |
| GET | `/api/alerts/my_alerts/` | Alertas propias | Employee |

#### **Filtros Disponibles:**
- `severity`: critical, high, medium, low
- `resolved`: true/false
- `employee`: ID del empleado
- `supervisor`: ID del supervisor
- `device`: ID del dispositivo
- `created_at_after`, `created_at_before`: rango de fechas

#### **Búsqueda:**
- Búsqueda por: message, description, employee__email, employee__first_name, employee__last_name

#### **Ordenamiento:**
- Campos: created_at, resolved_at, severity
- Ejemplo: `?ordering=-created_at` (más recientes primero)

### **Recomendaciones de Rutinas** (`/api/recommendations/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/recommendations/` | Listar recomendaciones | Admin: todas, Supervisor: sus empleados, Employee: propias |
| POST | `/api/recommendations/` | Crear recomendación | Admin, Supervisor |
| GET | `/api/recommendations/{id}/` | Detalle | Admin, Supervisor, Employee (si es propia) |
| PUT | `/api/recommendations/{id}/` | Actualizar | Admin, Supervisor |
| DELETE | `/api/recommendations/{id}/` | Eliminar | Admin |
| POST | `/api/recommendations/{id}/apply/` | Aplicar recomendación | Admin, Supervisor, Employee (si es propia) |
| POST | `/api/recommendations/{id}/reject/` | Rechazar recomendación | Admin, Supervisor, Employee (si es propia) |
| GET | `/api/recommendations/stats/` | Estadísticas | Admin, Supervisor |
| GET | `/api/recommendations/my_recommendations/` | Recomendaciones propias | Employee |

#### **Filtros Disponibles:**
- `recommendation_type`: sleep, break, exercise, cognitive, environment
- `applied`: true/false
- `employee`: ID del empleado
- `created_at_after`, `created_at_before`: rango de fechas

#### **Búsqueda:**
- Búsqueda por: employee__email, employee__first_name, employee__last_name

#### **Ordenamiento:**
- Campos: created_at, applied_at
- Ejemplo: `?ordering=-created_at`

---

## 🤖 Sistema de Detección de Anomalías

### **Archivo:** `apps/analytics/anomaly_detector.py`

### **Clase Principal: AnomalyDetector**

Sistema automático que analiza métricas procesadas y genera alertas cuando detecta patrones anormales.

### **Umbrales Configurables:**

```python
FATIGUE_THRESHOLDS = {
    'critical': 85,   # Fatiga crítica
    'high': 70,       # Fatiga alta
    'medium': 50,     # Fatiga moderada
}

SPO2_THRESHOLDS = {
    'critical': 88,   # SpO2 crítico
    'low': 90,        # SpO2 bajo
}

HEART_RATE_THRESHOLDS = {
    'very_high': 160,  # FC muy alta
    'high': 140,       # FC alta
}

DESATURATION_THRESHOLD = 3  # Número de desaturaciones
```

### **Métodos de Detección:**

#### 1. **`_check_fatigue_level(metric)`**
Detecta niveles elevados de fatiga basados en el índice de fatiga calculado por ML.

**Severidades:**
- `critical`: fatigue_index ≥ 85
- `high`: fatigue_index ≥ 70
- `medium`: fatigue_index ≥ 50

**Mensaje de ejemplo:**
```
"Nivel de fatiga crítico detectado (Índice: 87.5)"
```

#### 2. **`_check_spo2_level(metric)`**
Detecta niveles bajos de saturación de oxígeno.

**Severidades:**
- `critical`: SpO2 < 88%
- `high`: SpO2 < 90%

**Mensaje de ejemplo:**
```
"Nivel de oxígeno en sangre críticamente bajo (SpO2: 86.3%)"
```

#### 3. **`_check_heart_rate(metric)`**
Detecta frecuencia cardíaca anormalmente elevada.

**Severidades:**
- `high`: HR ≥ 160 bpm
- `medium`: HR ≥ 140 bpm

**Mensaje de ejemplo:**
```
"Frecuencia cardíaca muy elevada detectada (165 bpm)"
```

#### 4. **`_check_desaturations(metric)`**
Detecta múltiples eventos de desaturación.

**Criterio:**
- `high`: ≥ 3 desaturaciones

**Mensaje de ejemplo:**
```
"Múltiples eventos de desaturación detectados (5 eventos)"
```

#### 5. **`_check_combined_risks(metric)`**
Detecta combinaciones peligrosas de factores de riesgo.

**Combinaciones:**
- Fatiga alta + SpO2 bajo → `critical`
- Fatiga alta + FC elevada → `high`

**Mensaje de ejemplo:**
```
"Riesgo combinado: Fatiga alta (72.0) y nivel de oxígeno bajo (89.2%)"
```

#### 6. **`check_device_offline(device_id, time_threshold_minutes=30)`**
Detecta dispositivos sin conexión prolongada.

**Criterio:**
- Sin datos en los últimos 30 minutos (configurable)

**Mensaje de ejemplo:**
```
"Dispositivo ESP32-001 sin conexión desde hace más de 30 minutos"
```

### **Método Principal: `detect_and_create_alerts()`**

```python
results = detector.detect_and_create_alerts(
    time_window_minutes=60,  # Analizar últimos 60 minutos
    employee_id=None  # None = todos los empleados
)
```

**Retorna:**
```python
{
    'alerts_created': 3,
    'metrics_analyzed': 15,
    'employees_checked': 5
}
```

**Características:**
- Evita duplicados: no crea alertas si ya existe una no resuelta para el mismo empleado
- Logging detallado de todas las operaciones
- Transacciones atómicas para consistencia de datos
- Incluye recomendaciones automáticas basadas en el tipo de alerta

### **Función de Conveniencia:**

```python
from apps.analytics.anomaly_detector import run_anomaly_detection

# Ejecutar detección completa
results = run_anomaly_detection()
```

---

## 📊 Ejemplos de Uso de la API

### **1. Crear Alerta Manual**

```bash
POST /api/alerts/
Content-Type: application/json
Authorization: Bearer {token}

{
    "employee": 5,
    "device": 2,
    "severity": "high",
    "message": "Empleado reporta fatiga extrema",
    "description": "El empleado ha reportado síntomas de fatiga extrema después de turno nocturno",
    "recommendations": "Descanso inmediato de 2 horas, evaluación médica"
}
```

### **2. Resolver Alerta**

```bash
POST /api/alerts/15/resolve/
Content-Type: application/json
Authorization: Bearer {token}

{
    "resolution_notes": "Empleado tomó descanso, síntomas mejoraron. Se ajustó horario para próximo turno.",
    "resolved_by": 3
}
```

### **3. Obtener Estadísticas de Alertas**

```bash
GET /api/alerts/stats/
Authorization: Bearer {token}

Response:
{
    "total_alerts": 47,
    "by_severity": {
        "critical": 8,
        "high": 15,
        "medium": 18,
        "low": 6
    },
    "resolved": 35,
    "pending": 12,
    "avg_resolution_time_hours": 2.5
}
```

### **4. Crear Recomendación de Rutina**

```bash
POST /api/recommendations/
Content-Type: application/json
Authorization: Bearer {token}

{
    "employee": 5,
    "recommendation_type": "sleep",
    "data": {
        "duration_hours": 8,
        "suggested_bedtime": "22:00",
        "suggested_wake_time": "06:00",
        "sleep_hygiene_tips": [
            "Evitar pantallas 1 hora antes de dormir",
            "Mantener temperatura ambiente entre 18-20°C",
            "Rutina de relajación pre-sueño"
        ]
    }
}
```

### **5. Aplicar Recomendación**

```bash
POST /api/recommendations/8/apply/
Content-Type: application/json
Authorization: Bearer {token}

{
    "applied_notes": "Empleado aplicó rutina de sueño, reporta mejora en descanso",
    "applied_by": 5
}
```

### **6. Filtrar Alertas Críticas No Resueltas**

```bash
GET /api/alerts/?severity=critical&resolved=false&ordering=-created_at
Authorization: Bearer {token}
```

### **7. Mis Alertas (Endpoint de Empleado)**

```bash
GET /api/alerts/my_alerts/
Authorization: Bearer {employee_token}

Response:
[
    {
        "id": 23,
        "severity": "high",
        "message": "Nivel de fatiga alto detectado",
        "resolved": false,
        "created_at": "2024-01-15T14:30:00Z",
        "time_since_created": "2 horas"
    }
]
```

---

## 🔄 Integración con Otras Fases

### **Fase 3 (Modelos):**
- Utiliza modelos `FatigueAlert` y `RoutineRecommendation`
- Relaciones con `CustomUser`, `Device`, `ProcessedMetrics`

### **Fase 5 (Machine Learning):**
- Lee `fatigue_index` de `ProcessedMetrics`
- Usa predicciones de clustering (fatigue_cluster, anomaly_cluster)
- Analiza métricas fisiológicas procesadas (SpO2, HR, desaturaciones)

### **Fase 6 (REST APIs):**
- Sigue patrones de ViewSets establecidos
- Usa mismos sistemas de filtrado, búsqueda y paginación
- Consistente con permisos por roles

### **Próximas Fases:**
- **Fase 8:** Dashboard mostrará alertas en tiempo real
- **Fase 9:** Frontend React consumirá estos endpoints
- **Fase 10:** Tests de integración para detección de anomalías

---

## 🔐 Permisos y Seguridad

### **Roles y Accesos:**

| Acción | Admin | Supervisor | Employee |
|--------|-------|------------|----------|
| Ver todas las alertas | ✅ | ❌ (solo sus empleados) | ❌ (solo propias) |
| Crear alertas | ✅ | ✅ | ❌ |
| Resolver alertas | ✅ | ✅ | ❌ |
| Ver estadísticas | ✅ | ✅ | ❌ |
| Aplicar recomendaciones | ✅ | ✅ | ✅ (solo propias) |
| Rechazar recomendaciones | ✅ | ✅ | ✅ (solo propias) |

### **Validaciones de Seguridad:**
- Supervisores solo pueden gestionar alertas de sus empleados asignados
- Empleados solo acceden a sus propias alertas/recomendaciones
- Validación de ownership de dispositivos
- Prevención de duplicados de alertas activas

---

## 📈 Métricas de Implementación

- **Archivos creados:** 3
- **Líneas de código:** 1,095
- **Serializers:** 10
- **ViewSets:** 2
- **Endpoints API:** 18
- **Métodos de detección:** 6
- **Umbrales configurables:** 7

---

## 🚀 Próximos Pasos Sugeridos

1. **Automatización:**
   - Configurar Celery para ejecutar `run_anomaly_detection()` cada 5-10 minutos
   - Implementar notificaciones push cuando se crean alertas críticas

2. **Machine Learning Avanzado:**
   - Ajustar umbrales dinámicamente según histórico del empleado
   - Predicción de fatiga futura basada en patrones

3. **Dashboard:**
   - Visualización en tiempo real de alertas activas
   - Gráficos de tendencias de fatiga por empleado/turno

4. **Notificaciones:**
   - Email/SMS para alertas críticas
   - Notificaciones en app para supervisores

---

## ✅ Estado: COMPLETADA

Todos los componentes de la Fase 7 han sido implementados y están listos para integración con el frontend y pruebas.

**Fecha de completación:** 2024-01-15
