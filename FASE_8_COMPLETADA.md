# 📊 Fase 8: Dashboards y Visualizaciones - COMPLETADA

## 📋 Resumen de la Implementación

Esta fase implementa un sistema completo de dashboards y visualizaciones con métricas en tiempo real, análisis de tendencias y gráficas interactivas para los tres roles del sistema (Admin, Supervisor, Empleado).

---

## 🔧 Componentes Implementados

### 1. Serializers de Dashboard (`apps/analytics/dashboard_serializers.py`)

#### **OverviewStatsSerializer**
Estadísticas generales del sistema:
- Contadores: empleados totales/activos, dispositivos totales/activos
- Alertas: totales, pendientes, críticas, del día
- Recomendaciones: totales, pendientes, aplicadas
- Promedios: fatigue_index, SpO2, frecuencia cardíaca
- Datos de sensores: total de lecturas, lecturas del día

#### **RealTimeMetricsSerializer**
Métricas en tiempo real (últimos 5 minutos):
- Empleados activos, en peligro (fatigue>70), críticos (fatigue>85)
- Alertas recientes
- Top 5 empleados en riesgo
- Dispositivos offline

#### **EmployeeFatigueStatsSerializer**
Estadísticas de fatiga por empleado:
- Métricas actuales: fatigue_index, SpO2, FC, última lectura
- Promedios de 7 días
- Conteo de alertas (totales, pendientes, de la semana)
- Estado del dispositivo y batería

#### **TeamPerformanceSerializer**
Rendimiento de equipo para supervisores:
- Información del equipo: total de empleados, activos
- Alertas del equipo: totales, pendientes, críticas
- Promedios del equipo
- Empleado con mayor riesgo
- Tendencias: fatiga (increasing/decreasing/stable), alertas

#### **FatigueTrendSerializer**
Tendencias de fatiga en el tiempo:
- Por fecha/hora
- Promedios, máximos, mínimos de fatiga
- Métricas asociadas (SpO2, FC)
- Conteo de lecturas y empleados monitoreados
- Alertas generadas

#### **HourlyDistributionSerializer**
Distribución de fatiga por hora del día:
- Promedios por hora (0-23)
- Identifica horas pico de fatiga
- Conteo de alertas por hora

#### **WeeklyDistributionSerializer**
Distribución de fatiga por día de la semana:
- Promedios por día (Lunes-Domingo)
- Identifica días más críticos
- Conteo de alertas por día

#### **FatigueLevelDistributionSerializer**
Distribución de niveles de fatiga:
- Categorías: low (<50), medium (50-70), high (70-85), critical (≥85)
- Conteo y porcentaje de cada nivel

#### **DeviceHealthSerializer**
Estado de salud de dispositivos IoT:
- Información del dispositivo y empleado
- Estado, batería, última conexión
- Uptime percentage
- Total de lecturas (totales y del día)
- Data quality score

#### **AlertHistorySerializer**
Historial de alertas:
- Agrupado por fecha
- Conteo por severidad (critical, high, medium, low)
- Alertas resueltas
- Tiempo promedio de resolución

#### **RecommendationEffectivenessSerializer**
Efectividad de recomendaciones:
- Por tipo de recomendación
- Conteo: creadas, aplicadas, rechazadas
- Tasa de aplicación
- Impacto en fatiga (antes/después)
- Porcentaje de mejora

#### **EmployeeComparisonSerializer**
Comparación entre empleados:
- Métricas promedio individuales
- Total de alertas y tasa de alertas
- Ranking de fatiga
- Overall health score (0-100)

#### **CorrelationAnalysisSerializer**
Análisis de correlaciones:
- Entre variables (fatigue_index, SpO2, FC)
- Coeficiente de correlación
- Fuerza: weak, moderate, strong
- Dirección: positive, negative

#### **PredictiveInsightsSerializer**
Insights predictivos (preparado para ML avanzado):
- Predicción de fatiga próxima hora/turno
- Probabilidad de alerta
- Nivel de riesgo
- Acciones sugeridas
- Confianza de la predicción

#### **DashboardSummarySerializer**
Resumen completo para dashboard principal:
- Combina: overview, real_time, high_risk_employees
- Alertas recientes, tendencias de fatiga
- Dispositivos problemáticos

#### **SupervisorDashboardSerializer**
Dashboard específico para supervisores:
- Información del supervisor
- Rendimiento del equipo
- Lista de empleados con métricas
- Alertas del equipo
- Comparación entre empleados
- Recomendaciones pendientes

#### **EmployeeDashboardSerializer**
Dashboard personal para empleados:
- Información personal
- Estadísticas personales
- Historial de fatiga (7 días)
- Alertas y recomendaciones personales
- Comparación con promedio del equipo
- Progreso (mejora semana actual vs anterior)

---

## 🌐 API Endpoints

### **Dashboard General** (`/api/dashboard/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/dashboard/overview/` | Estadísticas generales del sistema | Autenticado |
| GET | `/api/dashboard/real_time/` | Métricas en tiempo real (5 min) | Autenticado |
| GET | `/api/dashboard/employee_dashboard/` | Dashboard personal del empleado | Employee |
| GET | `/api/dashboard/supervisor_dashboard/` | Dashboard de supervisor con equipo | Supervisor |
| GET | `/api/dashboard/admin_dashboard/` | Dashboard completo de admin | Admin |

### **Visualizaciones** (`/api/visualizations/`)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/visualizations/fatigue_trends/` | Tendencias de fatiga en el tiempo | Autenticado |
| GET | `/api/visualizations/hourly_distribution/` | Distribución por hora del día | Autenticado |
| GET | `/api/visualizations/weekly_distribution/` | Distribución por día de semana | Autenticado |
| GET | `/api/visualizations/fatigue_levels/` | Distribución de niveles de fatiga | Autenticado |
| GET | `/api/visualizations/alert_history/` | Historial de alertas | Autenticado |
| GET | `/api/visualizations/recommendation_effectiveness/` | Efectividad de recomendaciones | Supervisor/Admin |
| GET | `/api/visualizations/correlations/` | Análisis de correlaciones | Autenticado |
| GET | `/api/visualizations/heatmap_data/` | Datos para heatmap (día×hora) | Autenticado |

---

## 📊 Ejemplos de Uso

### **1. Obtener Overview del Sistema**

```bash
GET /api/dashboard/overview/
Authorization: Bearer {token}

Response:
{
    "total_employees": 25,
    "active_employees": 23,
    "total_devices": 25,
    "active_devices": 22,
    "total_alerts": 142,
    "pending_alerts": 8,
    "critical_alerts": 2,
    "alerts_today": 5,
    "total_recommendations": 87,
    "pending_recommendations": 12,
    "applied_recommendations": 65,
    "avg_fatigue_index": 42.5,
    "avg_spo2": 96.8,
    "avg_heart_rate": 78.3,
    "total_sensor_readings": 45678,
    "readings_today": 1234
}
```

### **2. Métricas en Tiempo Real**

```bash
GET /api/dashboard/real_time/
Authorization: Bearer {token}

Response:
{
    "timestamp": "2024-01-15T14:30:00Z",
    "active_employees": 18,
    "employees_in_danger": 3,
    "employees_critical": 1,
    "recent_alerts": 2,
    "high_risk_employees": [
        {
            "employee_id": 12,
            "employee_name": "Juan Pérez",
            "fatigue_index": 87.5,
            "spo2": 89.2,
            "last_reading": "2024-01-15T14:28:00Z"
        }
    ],
    "offline_devices": 3
}
```

### **3. Dashboard de Empleado**

```bash
GET /api/dashboard/employee_dashboard/
Authorization: Bearer {employee_token}

Response:
{
    "employee_info": {
        "id": 5,
        "name": "María González",
        "email": "maria@empresa.com",
        "phone": "+52 555 1234"
    },
    "personal_stats": {
        "current_fatigue_index": 52.3,
        "current_spo2": 97.5,
        "current_heart_rate": 76.0,
        "last_reading": "2024-01-15T14:25:00Z",
        "avg_fatigue_7d": 48.7,
        "avg_spo2_7d": 96.9,
        "avg_heart_rate_7d": 77.2,
        "total_alerts": 3,
        "pending_alerts": 1,
        "alerts_this_week": 2,
        "device_status": "active",
        "device_battery": 85.0
    },
    "fatigue_history": [
        {
            "date": "2024-01-09",
            "avg_fatigue_index": 45.2,
            "max_fatigue_index": 62.1,
            "min_fatigue_index": 32.5
        }
        // ... más días
    ],
    "vs_team_average": {
        "my_fatigue": 48.7,
        "team_fatigue": 45.3,
        "fatigue_diff": 3.4,
        "my_spo2": 96.9,
        "team_spo2": 97.2
    },
    "progress": {
        "current_week_fatigue": 48.7,
        "previous_week_fatigue": 52.1,
        "improvement": 3.4,
        "trend": "improving"
    }
}
```

### **4. Dashboard de Supervisor**

```bash
GET /api/dashboard/supervisor_dashboard/
Authorization: Bearer {supervisor_token}

Response:
{
    "supervisor_info": {
        "id": 3,
        "name": "Carlos Supervisor",
        "email": "carlos@empresa.com"
    },
    "team_performance": {
        "total_employees": 8,
        "active_employees": 7,
        "team_alerts": 25,
        "team_pending_alerts": 4,
        "team_critical_alerts": 1,
        "team_avg_fatigue": 45.8,
        "team_avg_spo2": 96.5,
        "team_avg_heart_rate": 78.9,
        "highest_risk_employee": {
            "employee_id": 12,
            "employee_name": "Juan Pérez",
            "fatigue_index": 72.3
        },
        "fatigue_trend": "increasing",
        "alerts_trend": "stable"
    },
    "employees": [
        // Lista de empleados con sus métricas
    ],
    "employee_comparison": [
        {
            "employee_id": 12,
            "employee_name": "Juan Pérez",
            "avg_fatigue": 72.3,
            "total_alerts": 8,
            "alert_rate": 1.14,
            "fatigue_rank": 1,
            "overall_health_score": 27.7
        }
        // ... más empleados
    ]
}
```

### **5. Tendencias de Fatiga**

```bash
GET /api/visualizations/fatigue_trends/?days=7&interval=day
Authorization: Bearer {token}

Response:
[
    {
        "date": "2024-01-09",
        "hour": null,
        "avg_fatigue_index": 45.2,
        "max_fatigue_index": 78.3,
        "min_fatigue_index": 22.1,
        "avg_spo2": 96.8,
        "avg_heart_rate": 77.5,
        "total_readings": 328,
        "employees_monitored": 23,
        "alerts_generated": 4
    }
    // ... más días
]
```

### **6. Distribución por Hora del Día**

```bash
GET /api/visualizations/hourly_distribution/?days=30
Authorization: Bearer {token}

Response:
[
    {
        "hour": 0,
        "avg_fatigue": 35.2,
        "avg_spo2": 97.1,
        "avg_heart_rate": 72.3,
        "total_readings": 156,
        "alert_count": 2
    },
    {
        "hour": 1,
        "avg_fatigue": 38.5,
        "avg_spo2": 96.9,
        "avg_heart_rate": 73.8,
        "total_readings": 142,
        "alert_count": 3
    }
    // ... hasta hora 23
]
```

### **7. Distribución por Día de Semana**

```bash
GET /api/visualizations/weekly_distribution/?days=90
Authorization: Bearer {token}

Response:
[
    {
        "day_of_week": 0,
        "day_name": "Lunes",
        "avg_fatigue": 48.5,
        "avg_spo2": 96.7,
        "avg_heart_rate": 79.2,
        "total_readings": 2345,
        "alert_count": 18
    }
    // ... hasta Domingo
]
```

### **8. Distribución de Niveles de Fatiga**

```bash
GET /api/visualizations/fatigue_levels/?days=30
Authorization: Bearer {token}

Response:
[
    {"level": "low", "count": 3256, "percentage": 65.2},
    {"level": "medium", "count": 1234, "percentage": 24.7},
    {"level": "high", "count": 412, "percentage": 8.2},
    {"level": "critical", "count": 98, "percentage": 1.9}
]
```

### **9. Heatmap de Fatiga (Día × Hora)**

```bash
GET /api/visualizations/heatmap_data/?days=30
Authorization: Bearer {token}

Response:
{
    "x_labels": ["00:00", "01:00", ..., "23:00"],
    "y_labels": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
    "values": [
        [35.2, 38.5, 42.1, ..., 30.2],  // Lunes
        [36.8, 40.2, 44.5, ..., 32.1],  // Martes
        // ... resto de días
    ]
}
```

### **10. Efectividad de Recomendaciones**

```bash
GET /api/visualizations/recommendation_effectiveness/
Authorization: Bearer {supervisor_token}

Response:
[
    {
        "recommendation_type": "sleep",
        "total_created": 25,
        "total_applied": 18,
        "total_rejected": 3,
        "application_rate": 72.0,
        "avg_fatigue_before": 68.5,
        "avg_fatigue_after": 52.3,
        "fatigue_improvement": 23.6
    }
    // ... otros tipos
]
```

### **11. Historial de Alertas**

```bash
GET /api/visualizations/alert_history/?days=30
Authorization: Bearer {token}

Response:
[
    {
        "date": "2024-01-09",
        "total_alerts": 8,
        "critical_alerts": 2,
        "high_alerts": 3,
        "medium_alerts": 2,
        "low_alerts": 1,
        "resolved_alerts": 7,
        "avg_resolution_time": 125.5
    }
    // ... más días
]
```

---

## 🔄 Integración con Otras Fases

### **Fase 3 (Modelos):**
- Consulta modelos: Device, SensorData, ProcessedMetrics, FatigueAlert, RoutineRecommendation, CustomUser
- Usa relaciones: employee, supervisor, device

### **Fase 5 (Machine Learning):**
- Lee fatigue_index calculado por ML
- Usa clustering results para análisis
- Base para insights predictivos

### **Fase 6 (REST APIs):**
- Sigue patrones de ViewSets
- Usa permisos por rol
- Integra con serializers existentes

### **Fase 7 (Alertas):**
- Analiza alertas generadas automáticamente
- Muestra estadísticas de alertas
- Tracking de resolución

### **Próximas Fases:**
- **Fase 9:** Frontend React consumirá estos endpoints para dashboards interactivos
- **Fase 10:** Insights predictivos serán expandidos con ML avanzado

---

## 🔐 Permisos y Seguridad

### **Filtrado Automático por Rol:**

| Endpoint | Admin | Supervisor | Employee |
|----------|-------|------------|----------|
| overview | ✅ Todos los datos | ✅ Todos los datos | ✅ Todos los datos |
| real_time | ✅ Sistema completo | ✅ Sistema completo | ✅ Sistema completo |
| employee_dashboard | ❌ | ❌ | ✅ Solo propios |
| supervisor_dashboard | ❌ | ✅ Su equipo | ❌ |
| admin_dashboard | ✅ | ❌ | ❌ |
| fatigue_trends | ✅ Todos | ✅ Su equipo | ✅ Solo propios |
| recommendation_effectiveness | ✅ Todos | ✅ Su equipo | ❌ |

### **Validaciones:**
- Empleados solo ven sus propios datos en visualizaciones
- Supervisores ven datos de empleados asignados
- Admin tiene acceso completo

---

## 📈 Métricas de Implementación

- **Archivos creados:** 5
- **Líneas de código:** 2,450
- **Serializers:** 19
- **ViewSets:** 3 (Dashboard, Visualization, Report)
- **Endpoints API:** 18 (5 dashboards + 8 visualizaciones + 5 reportes)
- **Tipos de gráficas soportadas:** 8 (tendencias, distribuciones, heatmap, correlaciones, historial)
- **Formatos de exportación:** 2 (JSON, CSV)

---

## 🎨 Tipos de Visualizaciones Soportadas

1. **Líneas de Tiempo (Time Series):**
   - Tendencias de fatiga diarias/por hora
   - Historial de alertas
   - Progreso individual

2. **Distribuciones:**
   - Por hora del día (0-23)
   - Por día de semana (Lun-Dom)
   - Por niveles de fatiga (low, medium, high, critical)

3. **Heatmaps:**
   - Fatiga por día × hora (7×24)
   - Identifica patrones temporales

4. **Comparaciones:**
   - Entre empleados (ranking)
   - Empleado vs promedio del equipo
   - Semana actual vs anterior

5. **Correlaciones:**
   - Fatigue vs SpO2
   - Fatigue vs FC
   - SpO2 vs FC

6. **Efectividad:**
   - Impacto de recomendaciones (antes/después)
   - Tasa de aplicación por tipo
   - Mejora en fatiga

7. **Estadísticas en Tiempo Real:**
   - Empleados en riesgo
   - Alertas activas
   - Dispositivos offline

8. **Historial:**
   - Alertas por día con severidad
   - Tiempo de resolución
   - Tendencias de alertas

---

## 🚀 Próximos Pasos Sugeridos

1. **Caché con Redis:**
   - Cachear dashboard overview (5 minutos)
   - Cachear tendencias diarias (1 hora)
   - Invalidación al crear alertas

2. **WebSockets para Tiempo Real:**
   - Push de métricas cada 10 segundos
   - Notificaciones de alertas críticas
   - Actualización automática de dashboards

3. **Exportación de Reportes:** ✅ Implementado
   - CSV de datos brutos
   - Reportes por empleado, equipo, alertas, métricas
   - Resumen ejecutivo para administradores
   - PDF con gráficas (requiere librería adicional)
   - Excel con múltiples hojas (requiere librería adicional)

4. **Sistema de Métricas Agregadas:** ✅ Implementado
   - Cálculo de estadísticas diarias, semanales, mensuales
   - Métricas de rendimiento por empleado y equipo
   - Optimizado para reducir carga en base de datos
   - Preparado para cache con Redis

5. **Machine Learning Avanzado:**
   - Predicción de fatiga futura
   - Detección de anomalías en tendencias
   - Recomendaciones automáticas personalizadas

6. **Alertas Proactivas:**
   - Notificar cuando tendencia es creciente
   - Alertar si empleado está por encima del promedio consistentemente
   - Sugerir breaks basado en patrones

---

## 📦 Archivos Creados

1. **`apps/analytics/dashboard_serializers.py`** (450 líneas)
   - 19 serializers para dashboards y métricas

2. **`apps/analytics/dashboard_views.py`** (650 líneas)
   - DashboardViewSet con 5 endpoints principales

3. **`apps/analytics/visualization_views.py`** (350 líneas)
   - VisualizationViewSet con 8 endpoints de gráficas

4. **`apps/analytics/report_views.py`** (550 líneas)
   - ReportViewSet con 5 endpoints de exportación CSV

5. **`apps/analytics/aggregated_metrics.py`** (450 líneas)
   - Sistema de métricas agregadas (diarias, semanales, mensuales)

6. **`config/urls.py`** (actualizado)
   - Registro de 3 ViewSets adicionales

---

## 🔗 Endpoints de Reportes

### **Reportes** (`/api/reports/`)

| Método | Endpoint | Descripción | Permisos | Exportación |
|--------|----------|-------------|----------|-------------|
| GET | `/api/reports/employee_report/?employee_id=5&days=30&format=csv` | Reporte individual de empleado | Admin/Supervisor/Employee | JSON, CSV |
| GET | `/api/reports/team_report/?days=30&format=csv` | Reporte de equipo completo | Supervisor/Admin | JSON, CSV |
| GET | `/api/reports/alerts_report/?days=30&format=csv` | Reporte detallado de alertas | Autenticado | JSON, CSV |
| GET | `/api/reports/metrics_report/?days=30&format=csv` | Reporte de métricas agregadas | Autenticado | JSON, CSV |
| GET | `/api/reports/executive_summary/?format=csv` | Resumen ejecutivo del sistema | Admin | JSON, CSV |

**Parámetros comunes:**
- `days`: Días hacia atrás (default: 30)
- `start_date`: Fecha inicio (formato: YYYY-MM-DD)
- `end_date`: Fecha fin (formato: YYYY-MM-DD)
- `format`: Formato de salida (`json` o `csv`)
- `employee_id`: ID del empleado (para reportes específicos)

**Ejemplo de uso:**
```bash
# Reporte de empleado en CSV
GET /api/reports/employee_report/?employee_id=5&days=30&format=csv
Authorization: Bearer {token}

# Descarga archivo: reporte_empleado_5_2024-01-01_to_2024-01-30.csv
```

---

## 📊 Sistema de Métricas Agregadas

### **Uso desde Django Shell:**

```python
# Acceder a Django shell
python manage.py shell

# Importar funciones
from apps.analytics.aggregated_metrics import (
    calculate_daily_metrics,
    calculate_weekly_metrics,
    calculate_monthly_metrics,
    get_employee_performance,
    get_team_performance,
    generate_all_metrics
)

# Calcular métricas diarias (últimos 30 días)
daily_stats = calculate_daily_metrics()
# Retorna lista de diccionarios con métricas por día

# Calcular métricas semanales (últimas 8 semanas)
weekly_stats = calculate_weekly_metrics(weeks=8)

# Calcular métricas mensuales (últimos 6 meses)
monthly_stats = calculate_monthly_metrics(months=6)

# Rendimiento de un empleado específico
employee_stats = get_employee_performance(employee_id=5, days=30)
# Retorna: métricas, alertas, recomendaciones del empleado

# Rendimiento de un equipo
team_stats = get_team_performance(supervisor_id=3, days=30)
# Retorna: métricas del equipo, alertas, tamaño del equipo

# Generar todas las métricas de una vez
all_metrics = generate_all_metrics()
# Retorna: {'daily': [...], 'weekly': [...], 'monthly': [...]}
```

### **Estructura de Métricas Diarias:**

```python
{
    'date': datetime.date(2024, 1, 15),
    'metrics': {
        'fatigue': {
            'avg': 45.2,
            'max': 78.5,
            'min': 22.1,
            'std': 12.3
        },
        'spo2': {
            'avg': 96.8,
            'min': 88.5,
            'max': 99.2
        },
        'heart_rate': {
            'avg': 77.5,
            'max': 145.2,
            'min': 58.3
        },
        'movement': {
            'avg': 65.4
        }
    },
    'counts': {
        'total_readings': 328,
        'unique_employees': 23,
        'unique_devices': 22,
        'fatigue_levels': {
            'low': 180,
            'medium': 98,
            'high': 42,
            'critical': 8
        }
    },
    'alerts': {
        'total': 12,
        'critical': 3,
        'high': 5,
        'resolved': 10
    }
}
```

### **Automatización con Cron o Celery:**

**Opción 1: Cron Job (Linux/Mac)**
```bash
# Agregar a crontab
# Ejecutar cada día a las 2 AM
0 2 * * * cd /path/to/project && python manage.py shell -c "from apps.analytics.aggregated_metrics import generate_all_metrics; generate_all_metrics()"
```

**Opción 2: Task Scheduler (Windows)**
```powershell
# Crear tarea programada
schtasks /create /tn "FatigueMetrics" /tr "python C:\path\to\manage.py shell -c 'from apps.analytics.aggregated_metrics import generate_all_metrics; generate_all_metrics()'" /sc daily /st 02:00
```

**Opción 3: Celery Beat (Recomendado para producción)**
```python
# celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('fatigue_detection')

app.conf.beat_schedule = {
    'generate-metrics-daily': {
        'task': 'apps.analytics.tasks.generate_metrics',
        'schedule': crontab(hour=2, minute=0),  # 2 AM cada día
    },
}

# tasks.py
from celery import shared_task
from apps.analytics.aggregated_metrics import generate_all_metrics

@shared_task
def generate_metrics():
    return generate_all_metrics()
```

---

## 🚀 Próximos Pasos Sugeridos

1. **Caché con Redis:**
   - Cachear dashboard overview (5 minutos)
   - Cachear tendencias diarias (1 hora)
   - Invalidación al crear alertas

2. **WebSockets para Tiempo Real:**
   - Push de métricas cada 10 segundos
   - Notificaciones de alertas críticas
   - Actualización automática de dashboards

---

## ✅ Estado: COMPLETADA

Todos los componentes de la Fase 8 han sido implementados. El sistema proporciona dashboards completos y visualizaciones para los tres roles, con análisis en tiempo real y tendencias históricas.

**Fecha de completación:** 2024-01-15
