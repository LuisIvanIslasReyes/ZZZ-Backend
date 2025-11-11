# ✅ FASE 3 COMPLETADA: Base de Datos y Modelos

## 📊 Modelos Creados

### 1. Device (apps/devices/models.py)
**Propósito:** Gestionar dispositivos ESP32 wearables  
**Características:**
- ✅ Relación 1:1 con Employee
- ✅ Relación N:1 con Supervisor
- ✅ Validación automática de roles
- ✅ Validación de coincidencia de supervisor
- ✅ Tracking de última conexión
- ✅ Soft delete con is_active

**Campos principales:**
- `device_identifier` - Identificador único (ej: ESP32-001)
- `employee` - OneToOneField al empleado
- `supervisor` - ForeignKey al supervisor
- `is_active` - Estado del dispositivo
- `last_connection` - Última vez que envió datos

---

### 2. SensorData (apps/sensors/models.py)
**Propósito:** Almacenar datos crudos de sensores  
**Frecuencia:** Cada 5 segundos (12 registros/minuto)

**Sensores capturados:**
- ✅ **Ritmo Cardíaco (HR)** - heart_rate en BPM
- ✅ **Oxigenación (SpO2)** - spo2 en %
- ✅ **Acelerómetro** - accel_x, accel_y, accel_z en g

**Índices optimizados:**
- device + timestamp (consultas rápidas por dispositivo)
- timestamp (ordenamiento cronológico)

**Estimación de datos:**
- 1 empleado = 12 registros/min = 720 registros/hora
- 10 empleados = 7,200 registros/hora
- 100 empleados = 72,000 registros/hora

---

### 3. ProcessedMetrics (apps/sensors/models.py)
**Propósito:** Métricas procesadas en ventanas de tiempo  
**Ventanas:** 30 segundos a 5 minutos

**Métricas de Ritmo Cardíaco:**
- ✅ hr_avg, hr_max, hr_min - Estadísticas básicas
- ✅ hrv_rmssd, hrv_sdnn - Variabilidad cardíaca
- ✅ hr_trend - Tendencia (stable/increasing/decreasing)

**Métricas de Oxigenación:**
- ✅ spo2_avg, spo2_min - Niveles de oxígeno
- ✅ spo2_variance - Variabilidad
- ✅ desaturation_count - Conteo de desaturaciones

**Métricas de Movimiento:**
- ✅ activity_level - Magnitud RMS del acelerómetro
- ✅ movement_variance - Variabilidad del movimiento
- ✅ movement_entropy - Entropía (inactividad/temblores)
- ✅ posture_angle - Ángulo de postura

**Features Combinados:**
- ✅ **fatigue_index** (0-100) - Calculado por ML
- ✅ hr_activity_ratio - HR alta + baja actividad = fatiga
- ✅ recovery_time - Tiempo de recuperación post-esfuerzo

**Índices optimizados:**
- employee + window_start (consultas por empleado)
- fatigue_index (filtros por nivel de fatiga)
- device + window_start (consultas por dispositivo)

---

### 4. FatigueAlert (apps/analytics/models.py)
**Propósito:** Sistema de alertas automáticas de fatiga

**Niveles de Severidad:**
- 🟢 low - Fatiga leve
- 🟡 medium - Fatiga moderada
- 🟠 high - Fatiga alta
- 🔴 critical - Fatiga crítica

**Tipos de Alertas:**
- high_fatigue - Fatigue index > 70
- low_spo2 - SpO2 < 90%
- high_hr - HR elevado sin actividad
- slow_recovery - Recuperación lenta post-esfuerzo
- suspicious_inactivity - Inactividad + HR alta

**Características:**
- ✅ Asignación automática a employee y supervisor
- ✅ Sistema de resolución con timestamp
- ✅ Tracking de quién resolvió la alerta
- ✅ Índices para consultas rápidas por estado

**Campos principales:**
- `employee` - Empleado afectado
- `supervisor` - Supervisor responsable
- `severity` - Nivel de criticidad
- `alert_type` - Tipo de alerta
- `message` - Descripción detallada
- `fatigue_index` - Índice en el momento de la alerta
- `is_resolved` - Estado de resolución
- `resolved_by` - Quién la resolvió

---

### 5. RoutineRecommendation (apps/analytics/models.py)
**Propósito:** Recomendaciones de optimización de rutinas

**Tipos de Recomendaciones:**
- ✅ **break** - Descanso sugerido
- ✅ **task_redistribution** - Redistribuir tareas
- ✅ **shift_rotation** - Rotación de turnos

**Características:**
- ✅ Sistema de prioridad (1-5)
- ✅ Almacenamiento de datos base (JSON)
- ✅ Tracking de aplicación
- ✅ Orientado a supervisores

**Campos principales:**
- `supervisor` - Supervisor que recibe
- `employee` - Empleado afectado
- `recommendation_type` - Tipo de acción
- `description` - Explicación detallada
- `priority` - Urgencia (1 = más urgente)
- `based_on_data` - JSONField con métricas
- `is_applied` - Si fue implementada
- `applied_at` - Cuándo se aplicó

---

## 🗄️ Estructura de Base de Datos

### Tablas Creadas:
1. ✅ `devices` - 8 columnas
2. ✅ `sensor_data` - 9 columnas  
3. ✅ `processed_metrics` - 26 columnas
4. ✅ `fatigue_alerts` - 11 columnas
5. ✅ `routine_recommendations` - 10 columnas

### Total: 5 tablas nuevas + 64 columnas

---

## 🔗 Relaciones entre Modelos

```
CustomUser (Admin)
    └── CustomUser (Supervisor) [admin_id FK]
            ├── CustomUser (Employee) [supervisor_id FK]
            │       ├── Device [employee OneToOne]
            │       │       └── SensorData [device FK]
            │       │               └── ProcessedMetrics [device FK]
            │       ├── ProcessedMetrics [employee FK]
            │       ├── FatigueAlert [employee FK]
            │       └── RoutineRecommendation [employee FK]
            │
            ├── Device [supervisor FK]
            ├── FatigueAlert [supervisor FK]
            └── RoutineRecommendation [supervisor FK]
```

---

## 📈 Índices de Performance

### Optimizaciones implementadas:
1. **SensorData:**
   - Índice compuesto: (device, timestamp)
   - Índice: timestamp
   - Índice descendente: -timestamp

2. **ProcessedMetrics:**
   - Índice compuesto: (employee, window_start)
   - Índice: fatigue_index
   - Índice descendente: -window_start
   - Índice compuesto: (device, window_start)

3. **FatigueAlert:**
   - Índice compuesto: (employee, is_resolved)
   - Índice compuesto: (supervisor, is_resolved)
   - Índice compuesto: (severity, -timestamp)
   - Índice descendente: -timestamp

4. **RoutineRecommendation:**
   - Índice compuesto: (supervisor, is_applied)
   - Índice compuesto: (employee, is_applied)
   - Índice compuesto: (priority, -created_at)

---

## 🔧 Admin Panel Configurado

### Interfaces de administración creadas:

1. **DeviceAdmin**
   - Lista: identifier, employee, supervisor, is_active, last_connection
   - Filtros: is_active, supervisor, created_at
   - Búsqueda: identifier, employee email/name

2. **SensorDataAdmin**
   - Lista: device, timestamp, heart_rate, spo2
   - Filtros: device, timestamp
   - Jerarquía por fecha

3. **ProcessedMetricsAdmin**
   - Lista: employee, window_start, fatigue_index, hr_avg, spo2_avg, activity
   - Filtros: employee, window_start, hr_trend
   - Jerarquía por fecha

4. **FatigueAlertAdmin**
   - Lista: employee, severity, alert_type, fatigue_index, is_resolved
   - Filtros: severity, is_resolved, alert_type
   - Acción personalizada: "Marcar como resuelta"

5. **RoutineRecommendationAdmin**
   - Lista: employee, supervisor, type, priority, is_applied
   - Filtros: type, priority, is_applied
   - Acción personalizada: "Marcar como aplicada"

---

## ✅ Verificaciones Realizadas

- ✅ `python manage.py makemigrations` - 3 migraciones creadas
- ✅ `python manage.py migrate` - Aplicadas exitosamente
- ✅ `python manage.py check` - 0 errores
- ✅ Validaciones de integridad en modelos
- ✅ Relaciones FK correctamente configuradas
- ✅ Índices de performance creados

---

## 🎯 Próximos Pasos: FASE 4

### Integración MQTT

1. **Cliente MQTT en Django:**
   - Conectar a broker Mosquitto
   - Suscribirse a topic `devices/+/sensors`
   - Parser de mensajes JSON

2. **Simulador ESP32:**
   - Script Python que simule dispositivo
   - Generar datos realistas de sensores
   - Publicar cada 5 segundos

3. **Procesador de Ventanas:**
   - Servicio que calcule ProcessedMetrics
   - Ejecutar cada 30s - 1min
   - Llamar modelo ML para fatigue_index

4. **Sistema de Alertas:**
   - Monitoreo continuo de métricas
   - Creación automática de FatigueAlert
   - Generación de RoutineRecommendation

---

## 📊 Estadísticas del Proyecto

**Líneas de código agregadas:** ~600 líneas  
**Modelos creados:** 5  
**Campos totales:** 64  
**Índices de BD:** 15  
**Relaciones FK:** 8  

**Estado:** ✅ FASE 3 COMPLETADA  
**Fecha:** 10 de noviembre de 2025  

---

**¿Listo para continuar con la Fase 4 (Integración MQTT)?**
