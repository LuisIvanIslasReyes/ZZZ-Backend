# Contexto del Proyecto: Sistema de Detección de Fatiga Laboral

## 📋 INFORMACIÓN GENERAL

**Nombre del Proyecto:** Sistema de Detección de Fatiga en Empleados  
**Tipo:** Proyecto escolar  
**Objetivo:** Aplicación web para detección de fatiga en empleados mediante sensores IoT, permitiendo análisis y predicción para optimizar rutinas laborales.  
**Fecha de inicio:** 10 de noviembre de 2025

---

## 🏗️ ARQUITECTURA TECNOLÓGICA

### Backend
- **Framework:** Django REST Framework (DRF)
- **Base de datos:** PostgreSQL
- **Autenticación:** JWT (JSON Web Tokens) con djangorestframework-simplejwt
- **Protocolo IoT:** MQTT (paho-mqtt)
- **Machine Learning:** Jupyter Notebook con scikit-learn, pandas, numpy

### Frontend
- **Framework:** React + TypeScript
- **Build tool:** Vite
- **UI Framework:** DaisyUI (basado en TailwindCSS)
- **Gráficas:** Chart.js o Recharts
- **HTTP Client:** Axios
- **Routing:** react-router-dom

### Hardware
- **Dispositivo:** ESP32 (simulado)
- **Sensores:**
  - Sensor de ritmo cardíaco (HR/PPG/ECG)
  - Acelerómetro (movimiento)
  - Sensor de oxígeno (SpO2)

### Comunicación
- **ESP32 → Backend:** MQTT
- **Frontend ↔ Backend:** REST API
- **Actualizaciones en tiempo real:** Polling cada 10-30s (opcional: WebSockets)

---

## 👥 ROLES Y JERARQUÍA DE USUARIOS

### 1. Administrador
**Responsabilidades:**
- Gestionar Supervisores (CRUD)
- Ver estadísticas generales del sistema
- Configuración global
- Acceso a logs de actividad

**No gestiona directamente:** Empleados ni Dispositivos

### 2. Supervisor
**Responsabilidades:**
- Gestionar Empleados bajo su supervisión (CRUD)
- Gestionar Dispositivos (solo 1 por empleado en esta versión)
- Ver dashboard con métricas de todos sus empleados
- Gestionar alertas de fatiga
- Recibir recomendaciones para optimización de rutinas

**Jerarquía:** Reporta a Administrador, supervisa a Empleados

### 3. Empleado
**Responsabilidades:**
- Visualizar sus propias estadísticas y métricas
- Ver su historial de fatiga
- Recibir y ver sus alertas personales
- Usar el dispositivo wearable (ESP32)

**Jerarquía:** Reporta a Supervisor, porta el dispositivo

**Relación de datos:**
```
Administrador (1) → Supervisores (N)
Supervisor (1) → Empleados (N)
Empleado (1) → Dispositivo ESP32 (1)
Dispositivo → Datos de sensores (N)
```

---

## 📊 ESTRUCTURA DE DATOS

### Parámetros de Sensores

#### 1. Frecuencia Cardíaca (HR)
- **Métricas:**
  - HR promedio (BPM)
  - HR máximo/mínimo
  - Variabilidad (HRV): RMSSD, SDNN, pNN50
  - Tendencias: aumento sostenido, recuperación lenta
- **Sampling:** 100 Hz (PPG/ECG)

#### 2. Oxigenación (SpO₂)
- **Métricas:**
  - SpO₂ media y mínima (%)
  - Desaturaciones (>3% o >4%)
  - Variabilidad de SpO₂
- **Sampling:** 1 Hz

#### 3. Movimiento (Acelerómetro)
- **Métricas:**
  - Nivel de actividad (magnitud RMS, energía)
  - Varianza y entropía (inactividad o temblores)
  - Postura / inclinación del cuerpo
  - Frecuencia de paso o cadencia
- **Sampling:** 50-100 Hz

#### 4. Features Combinados (para ML)
- HR alta con baja actividad = fatiga
- Recuperación lenta de HR después de esfuerzo
- Correlación HR–SpO₂
- Inactividad + HR alta

#### 5. Procesamiento
- **Ventanas de tiempo:** 30 segundos a 5 minutos
- **Frecuencia de envío desde ESP32:** Cada 5 segundos (12 registros/min)
- **Filtrado:** Ruido y sincronización entre sensores

---

## 🗄️ MODELOS DE BASE DE DATOS

### 1. CustomUser
```python
- id (PK)
- email (unique)
- password (hashed)
- first_name
- last_name
- role (choices: 'admin', 'supervisor', 'employee')
- supervisor_id (FK a User, nullable) # solo para employees
- admin_id (FK a User, nullable) # solo para supervisors
- is_active
- created_at
- updated_at
```

### 2. Device
```python
- id (PK)
- device_identifier (unique, ej: "ESP32-001")
- employee_id (FK a User, unique) # 1 dispositivo por empleado
- supervisor_id (FK a User) # quien lo gestiona
- is_active
- last_connection
- created_at
```

### 3. SensorData (Datos crudos - cada 5 segundos)
```python
- id (PK)
- device_id (FK a Device)
- timestamp (indexed)
- heart_rate (float, BPM)
- spo2 (float, %)
- accel_x (float, g)
- accel_y (float, g)
- accel_z (float, g)
- created_at
```
**Índices:** device_id + timestamp

### 4. ProcessedMetrics (Ventanas de 1-5 min)
```python
- id (PK)
- device_id (FK a Device)
- employee_id (FK a User)
- window_start (datetime)
- window_end (datetime)
- # HR metrics
- hr_avg (float)
- hr_max (float)
- hr_min (float)
- hrv_rmssd (float)
- hrv_sdnn (float)
- hr_trend (string) # 'stable', 'increasing', 'decreasing'
- # SpO2 metrics
- spo2_avg (float)
- spo2_min (float)
- spo2_variance (float)
- desaturation_count (int)
- # Movement metrics
- activity_level (float) # magnitud RMS
- movement_variance (float)
- movement_entropy (float)
- posture_angle (float, nullable)
- # Combined features
- fatigue_index (float, 0-100) # calculado por ML
- hr_activity_ratio (float)
- recovery_time (float, nullable) # post-esfuerzo
- created_at
```
**Índices:** employee_id + window_start, fatigue_index

### 5. FatigueAlert
```python
- id (PK)
- employee_id (FK a User)
- supervisor_id (FK a User)
- timestamp (datetime)
- severity (choices: 'low', 'medium', 'high', 'critical')
- alert_type (string) # 'high_fatigue', 'low_spo2', 'high_hr', etc.
- message (text)
- fatigue_index (float)
- is_resolved (boolean)
- resolved_at (datetime, nullable)
- resolved_by (FK a User, nullable)
- created_at
```
**Índices:** employee_id + is_resolved, supervisor_id + is_resolved

### 6. RoutineRecommendation
```python
- id (PK)
- supervisor_id (FK a User)
- employee_id (FK a User)
- recommendation_type (choices: 'break', 'task_redistribution', 'shift_rotation')
- description (text)
- priority (int, 1-5)
- based_on_data (JSON) # métricas que generaron la recomendación
- is_applied (boolean)
- applied_at (datetime, nullable)
- created_at
```

---

## 🤖 MACHINE LEARNING

### Objetivo
**Clustering automático** para detectar y clasificar niveles de fatiga (0-100) sin etiquetas previas.

### Enfoque
1. **Datos de entrada:** Iniciar desde cero, recolectar datos del ESP32 simulado
2. **Algoritmo:** K-Means o DBSCAN para clustering
3. **Features principales:**
   - HR promedio, variabilidad, tendencia
   - HRV (RMSSD, SDNN)
   - SpO2 promedio, mínimo, variabilidad
   - Actividad (magnitud RMS)
   - Entropía de movimiento
   - HR alta + baja actividad
   - Recuperación post-esfuerzo
   - Ratio HR/actividad

### Pipeline
1. **Feature Engineering en Jupyter:**
   - Calcular todas las métricas desde SensorData
   - Normalización y scaling
   - Selección de features relevantes
   
2. **Clustering:**
   - Determinar número óptimo de clusters (método del codo, silhouette)
   - Entrenar modelo
   - Etiquetar clusters como niveles de fatiga (0-100)
   
3. **Validación:**
   - Métricas: Silhouette Score, Davies-Bouldin Index
   - Visualizaciones: PCA, t-SNE
   
4. **Exportación:**
   - Guardar modelo como .pkl
   - Crear función de predicción
   
5. **Integración con Backend:**
   - Endpoint que carga el modelo
   - Predicción en tiempo real al procesar nuevas ventanas
   - Actualizar fatigue_index en ProcessedMetrics

---

## 📈 DASHBOARDS Y VISUALIZACIONES

### Dashboard del EMPLEADO

**Gráficas:**
1. **Índice de Fatiga** (principal)
   - Tipo: Línea
   - Rango: 0-100
   - Tiempo: Últimas 8 horas / día actual
   - Color dinámico según nivel

2. **Ritmo Cardíaco (HR)**
   - Tipo: Línea
   - Eje Y: BPM
   - Mostrar zona normal y alertas

3. **Variabilidad Cardíaca (HRV)**
   - Tipo: Área
   - Métrica: RMSSD
   - Indica estrés/recuperación

4. **Oxigenación (SpO2)**
   - Tipo: Línea
   - Eje Y: %
   - Línea de referencia en 90%

5. **Nivel de Actividad**
   - Tipo: Área
   - Magnitud del acelerómetro

**Cards de Resumen:**
- HR promedio del día
- SpO2 mínimo del día
- Nivel de fatiga actual
- Tiempo total en fatiga alta hoy
- Alertas activas

**Panel de Alertas:**
- Lista de alertas recientes
- Indicadores visuales por severidad

### Dashboard del SUPERVISOR

**Vista General:**
1. **Grid de Empleados**
   - Card por cada empleado
   - Indicador de estado actual (color según fatiga)
   - HR actual, SpO2 actual, Fatiga actual
   - Botón para ver detalles

2. **Gráfica Comparativa de Fatiga**
   - Tipo: Líneas múltiples
   - Una línea por empleado
   - Últimas 8 horas

3. **Heatmap de Fatiga**
   - Filas: Empleados
   - Columnas: Horas del día
   - Color: Nivel de fatiga

4. **Estadísticas Agregadas:**
   - Promedio de fatiga del equipo
   - Número de empleados en alerta
   - Tendencia semanal
   - Comparativa con semana anterior

5. **Panel de Recomendaciones:**
   - Empleados que necesitan descanso
   - Sugerencias de redistribución de tareas
   - Recomendaciones de rotación de turnos
   - Prioridad por color

6. **Panel de Alertas Activas:**
   - Lista priorizada por severidad
   - Filtros por empleado
   - Botón para resolver
   - Historial

**Herramientas:**
- Filtros por fecha
- Exportación de reportes
- Configuración de umbrales de alerta

---

## 🚨 SISTEMA DE ALERTAS

### Condiciones de Activación

1. **Fatiga Alta:**
   - fatigue_index > 70 por más de 10 minutos
   - Severidad: medium/high según duración

2. **Oxigenación Baja:**
   - SpO2 < 90% por más de 2 minutos
   - Severidad: critical

3. **Ritmo Cardíaco Elevado:**
   - HR > umbral personalizado por >5 minutos sin actividad correspondiente
   - Severidad: medium

4. **Inactividad Sospechosa:**
   - Actividad muy baja + HR alta
   - Severidad: high

5. **Recuperación Lenta:**
   - HR tarda >10 min en volver a normal post-esfuerzo
   - Severidad: low/medium

### Flujo de Alertas

1. **Detección:** Servicio en backend monitorea ProcessedMetrics continuamente
2. **Creación:** Se crea registro en FatigueAlert
3. **Notificación:** 
   - Al empleado afectado
   - Al supervisor del empleado
4. **Visualización:** 
   - Badge en UI
   - Aparece en panel de alertas
5. **Resolución:**
   - Supervisor puede marcar como resuelta
   - Se registra quién y cuándo la resolvió

---

## 🎯 OPTIMIZACIÓN DE RUTINAS

### Algoritmo de Recomendaciones

**Basado en:**
1. **Patrones históricos de fatiga por empleado**
   - Horarios de picos de fatiga
   - Días de la semana con mayor fatiga
   
2. **Correlaciones:**
   - Tipo de tarea vs nivel de fatiga
   - Duración de jornada vs recuperación
   
3. **Comparativa entre empleados:**
   - Distribución de carga
   - Equidad en tareas pesadas

**Tipos de Recomendaciones:**

1. **Descansos programados:**
   - Sugerir break cuando fatiga alcanza 60%
   - Horarios óptimos según histórico

2. **Redistribución de tareas:**
   - Identificar empleados sobrecargados
   - Sugerir reasignación a empleados con menor fatiga

3. **Rotación de turnos:**
   - Empleados con fatiga crónica en ciertos horarios
   - Sugerir cambio de turno

4. **Alertas preventivas:**
   - Predecir picos de fatiga
   - Notificar antes de que ocurran

### Implementación
- Endpoint: `/api/recommendations/`
- Se genera reporte diario/semanal
- Supervisor puede aceptar o rechazar
- Tracking de efectividad de recomendaciones aplicadas

---

## 🔌 ENDPOINTS DE API

### Autenticación
- `POST /api/auth/register/` - Registro (solo admin puede crear supervisores)
- `POST /api/auth/login/` - Login (retorna JWT)
- `POST /api/auth/refresh/` - Refresh token
- `POST /api/auth/logout/` - Logout

### Admin
- `GET /api/admin/supervisors/` - Lista de supervisores
- `POST /api/admin/supervisors/` - Crear supervisor
- `PUT /api/admin/supervisors/{id}/` - Actualizar supervisor
- `DELETE /api/admin/supervisors/{id}/` - Eliminar supervisor
- `GET /api/admin/stats/` - Estadísticas generales

### Supervisor
- `GET /api/supervisor/employees/` - Lista sus empleados
- `POST /api/supervisor/employees/` - Crear empleado
- `PUT /api/supervisor/employees/{id}/` - Actualizar empleado
- `DELETE /api/supervisor/employees/{id}/` - Eliminar empleado
- `GET /api/supervisor/devices/` - Lista dispositivos de sus empleados
- `POST /api/supervisor/devices/` - Asignar dispositivo a empleado
- `PUT /api/supervisor/devices/{id}/` - Actualizar dispositivo
- `GET /api/supervisor/dashboard/` - Resumen de todos los empleados
- `GET /api/supervisor/employees/{id}/metrics/` - Métricas de un empleado
- `GET /api/supervisor/employees/{id}/metrics/realtime/` - Datos en tiempo real
- `GET /api/supervisor/employees/{id}/metrics/history/` - Histórico con filtros
- `GET /api/supervisor/alerts/` - Alertas de sus empleados
- `POST /api/supervisor/alerts/{id}/resolve/` - Resolver alerta
- `GET /api/supervisor/recommendations/` - Recomendaciones de optimización

### Empleado
- `GET /api/employee/me/` - Información personal
- `GET /api/employee/me/metrics/` - Mis métricas actuales
- `GET /api/employee/me/metrics/history/` - Mi histórico
- `GET /api/employee/me/fatigue/` - Mi índice de fatiga
- `GET /api/employee/me/alerts/` - Mis alertas
- `GET /api/employee/me/stats/` - Mis estadísticas

### ML & Analytics
- `POST /api/ml/predict/` - Predicción de fatiga (interno)
- `GET /api/analytics/trends/` - Tendencias generales

---

## 📡 INTEGRACIÓN MQTT

### Configuración
- **Broker:** Mosquitto (local o cloud: HiveMQ, CloudMQTT)
- **QoS:** 1 (at least once)
- **Retain:** false

### Topics
- **Publicación desde ESP32:**
  - `devices/{device_id}/sensors` - Datos de sensores
  
- **Suscripción en Backend:**
  - `devices/+/sensors` - Escucha todos los dispositivos

### Formato de Mensaje (JSON)
```json
{
  "device_id": "ESP32-001",
  "timestamp": "2025-11-10T14:30:00Z",
  "heart_rate": 75.5,
  "spo2": 98.2,
  "accel": {
    "x": 0.12,
    "y": -0.05,
    "z": 9.81
  }
}
```

### Flujo
1. ESP32 lee sensores cada 5 segundos
2. Publica a MQTT broker
3. Backend Django escucha con cliente MQTT
4. Parser valida y guarda en SensorData
5. Cada 30s-1min, procesa ventana y crea ProcessedMetrics
6. Modelo ML predice fatigue_index
7. Sistema de alertas evalúa condiciones

---

## 📂 ESTRUCTURA DE APPS DJANGO

```
backend/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/
│   │   ├── models.py (CustomUser)
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── permissions.py
│   ├── devices/
│   │   ├── models.py (Device)
│   │   ├── serializers.py
│   │   └── views.py
│   ├── sensors/
│   │   ├── models.py (SensorData, ProcessedMetrics)
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── processors.py (procesamiento de ventanas)
│   ├── analytics/
│   │   ├── models.py (FatigueAlert, RoutineRecommendation)
│   │   ├── ml_service.py (carga modelo ML)
│   │   ├── alert_service.py (lógica de alertas)
│   │   └── recommendation_service.py
│   └── mqtt_client/
│       ├── client.py (cliente MQTT)
│       ├── handlers.py (procesamiento de mensajes)
│       └── apps.py (inicialización)
├── ml_models/
│   └── fatigue_model.pkl (modelo entrenado)
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_clustering_model.ipynb
├── requirements.txt
└── manage.py
```

---

## 📂 ESTRUCTURA DE FRONTEND

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Navbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Card.tsx
│   │   ├── charts/
│   │   │   ├── FatigueChart.tsx
│   │   │   ├── HeartRateChart.tsx
│   │   │   ├── SpO2Chart.tsx
│   │   │   ├── ActivityChart.tsx
│   │   │   └── HeatmapChart.tsx
│   │   └── alerts/
│   │       ├── AlertList.tsx
│   │       └── AlertCard.tsx
│   ├── pages/
│   │   ├── auth/
│   │   │   └── Login.tsx
│   │   ├── admin/
│   │   │   └── SupervisorManagement.tsx
│   │   ├── supervisor/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── EmployeeManagement.tsx
│   │   │   ├── DeviceManagement.tsx
│   │   │   ├── Alerts.tsx
│   │   │   └── Recommendations.tsx
│   │   └── employee/
│   │       ├── Dashboard.tsx
│   │       └── MyStats.tsx
│   ├── services/
│   │   ├── api.ts (axios config)
│   │   ├── authService.ts
│   │   ├── metricsService.ts
│   │   └── alertsService.ts
│   ├── types/
│   │   ├── User.ts
│   │   ├── Metrics.ts
│   │   └── Alert.ts
│   ├── context/
│   │   └── AuthContext.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useRealTimeMetrics.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   └── constants.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

---

## 🚀 PLAN DE DESARROLLO POR FASES

### FASE 1: Configuración del Proyecto Base
- Inicializar Django + DRF
- Configurar PostgreSQL
- Inicializar React + Vite + TypeScript
- Configurar TailwindCSS + DaisyUI
- Verificar conexión frontend-backend

### FASE 2: Sistema de Autenticación y Roles
- Modelo CustomUser con roles
- JWT authentication
- Login/registro endpoints
- Rutas protegidas en frontend
- Layouts por rol

### FASE 3: Base de Datos y Modelos
- Modelos: User, Device, SensorData, ProcessedMetrics, FatigueAlert, RoutineRecommendation
- Migraciones
- Relaciones y FK
- Índices para performance

### FASE 4: Integración MQTT
- Cliente MQTT en Django
- Simulador ESP32 en Python
- Parser de mensajes
- Guardado en SensorData
- Logs y debugging

### FASE 5: Modelo de Machine Learning
- Jupyter: exploración de datos
- Feature engineering
- Clustering (K-Means/DBSCAN)
- Validación y exportación
- Integración con backend

### FASE 6: APIs REST
- Endpoints para Admin
- Endpoints para Supervisor
- Endpoints para Empleado
- Serializers y validaciones
- Documentación Swagger

### FASE 7: Sistema de Alertas
- Servicio de monitoreo
- Lógica de detección
- Creación de alertas
- Endpoints de gestión
- Notificaciones en UI

### FASE 8: Dashboards y Visualizaciones
- Dashboard Empleado con gráficas
- Dashboard Supervisor con comparativas
- Integración con Chart.js/Recharts
- Actualización en tiempo real
- Responsividad

### FASE 9: Panel de Gestión Admin
- CRUD de Supervisores
- Estadísticas generales
- Logs de actividad

### FASE 10: Sistema de Optimización
- Algoritmo de recomendaciones
- Endpoints de recomendaciones
- UI de sugerencias para Supervisor
- Tracking de aplicación

### FASE 11: Testing y Optimización
- Tests unitarios (pytest)
- Tests de integración
- Optimización de queries
- Validación end-to-end

### FASE 12: Documentación y Deploy
- README completo
- Documentación de API
- Docker/docker-compose
- Preparación para presentación

---

## 📝 NOTAS IMPORTANTES

### Consideraciones de Performance
- Datos cada 5 segundos = 720 registros/hora/empleado
- Ventanas de procesamiento: 30s-1min para evitar sobrecarga
- Índices en timestamp y employee_id
- Considerar archivado de datos antiguos (>3 meses)
- Caching opcional con Redis para métricas frecuentes

### Enfoque Escolar
- **Simplicidad:** Priorizar funcionalidad sobre complejidad
- **Documentación:** Código bien comentado
- **Demo:** Preparar datos de prueba realistas
- **Presentación:** Dashboard visualmente atractivo

### Simulación ESP32
- Script Python con paho-mqtt
- Generar datos realistas con variaciones
- Simular diferentes escenarios de fatiga
- Facilitar testing sin hardware

### Futuras Mejoras (Opcional)
- WebSockets para tiempo real verdadero
- Notificaciones push
- Exportación de reportes PDF
- Análisis predictivo avanzado
- Aplicación móvil
- Múltiples dispositivos por empleado

---

## 🔧 DEPENDENCIAS PRINCIPALES

### Backend (requirements.txt)
```
Django>=4.2
djangorestframework>=3.14
djangorestframework-simplejwt>=5.3
psycopg2-binary>=2.9
paho-mqtt>=1.6
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
joblib>=1.3
python-decouple>=3.8
django-cors-headers>=4.0
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "axios": "^1.5.0",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0",
    "daisyui": "^3.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^4.4.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## ✅ ESTADO ACTUAL DEL PROYECTO

**Fecha:** 10 de noviembre de 2025  
**Fase actual:** Planificación completa  
**Siguiente paso:** Iniciar Fase 1 - Configuración del Proyecto Base

**Decisiones pendientes:**
- Nombre específico del broker MQTT (local vs cloud)
- Umbral específico de HR por edad/empleado
- Duración específica de las ventanas (decidir entre 30s, 1min, 5min)
- Framework de gráficas final (Chart.js vs Recharts)

---

## 📞 INFORMACIÓN DE CONTACTO DEL PROYECTO

**Repositorio:** ZZZ-Backend  
**Owner:** LuisIvanIslasReyes  
**Branch principal:** main  
**Sistema operativo:** Windows  
**Shell:** PowerShell

---

**FIN DEL CONTEXTO**

Este documento contiene toda la información necesaria para continuar el desarrollo del proyecto en futuras conversaciones. Leer este archivo proporciona contexto completo sobre arquitectura, decisiones técnicas, modelos de datos, y plan de ejecución.
