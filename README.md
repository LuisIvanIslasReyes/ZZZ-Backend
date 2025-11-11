# Sistema de Detección de Fatiga en Empleados 😴⚡

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema completo de detección y análisis de fatiga en empleados mediante sensores IoT (ESP32), con Machine Learning para predicción y optimización de rutinas laborales.

---

## 🎯 Descripción del Proyecto

Aplicación web empresarial que permite:

- 📊 **Monitoreo en Tiempo Real**: Signos vitales (ritmo cardíaco, SpO2, temperatura, movimiento)
- 🤖 **Machine Learning**: Predicción automática de niveles de fatiga (0-100)
- 🚨 **Sistema de Alertas**: Notificaciones automáticas cuando se detecta fatiga alta
- 📈 **Dashboards Interactivos**: Visualización para Empleados, Supervisores y Administradores
- 🔄 **Optimización de Rutinas**: Recomendaciones automáticas basadas en patrones detectados
- 📱 **IoT Integration**: Comunicación MQTT con dispositivos ESP32

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────┐      MQTT      ┌──────────────┐      REST API     ┌──────────────┐
│  ESP32      │ ────────────► │  Django      │ ───────────────► │  Frontend    │
│  Sensores   │                │  Backend     │                   │  React       │
└─────────────┘                └──────────────┘                   └──────────────┘
                                      │
                                      │ PostgreSQL
                                      ▼
                               ┌──────────────┐
                               │  Database    │
                               │  + ML Models │
                               └──────────────┘
```

### Componentes Principales

1. **ESP32 Simulator** - Genera datos de sensores simulados
2. **MQTT Client** - Recibe y procesa datos de sensores
3. **Sensor Processor** - Calcula métricas y alimenta el modelo ML
4. **ML Service** - Predice niveles de fatiga (K-Means clustering)
5. **Alert System** - Genera alertas automáticas
6. **Recommendation Engine** - Optimiza rutinas laborales
7. **REST API** - 50+ endpoints documentados con Swagger

---

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** Django 4.2.7 + Django REST Framework 3.14.0
- **Base de Datos:** PostgreSQL
- **Autenticación:** JWT (djangorestframework-simplejwt)
- **IoT:** MQTT (paho-mqtt)
- **Machine Learning:** scikit-learn, pandas, numpy

### Frontend
- **Framework:** React + TypeScript
- **Build Tool:** Vite
- **UI:** DaisyUI + TailwindCSS
- **Gráficas:** Chart.js / Recharts

### Hardware
- **Dispositivo:** ESP32
- **Sensores:** Ritmo cardíaco, Acelerómetro, SpO2

## 📋 Requisitos Previos

- Python 3.11+
- PostgreSQL 14+
- Broker MQTT (Mosquitto recomendado)
- Node.js 18+ (para frontend)
- Git

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/LuisIvanIslasReyes/ZZZ-Backend.git
cd ZZZ-Backend
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv
```

**Activar el entorno virtual:**
- Windows (PowerShell):
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- Windows (CMD):
  ```cmd
  venv\Scripts\activate.bat
  ```
- Linux/Mac:
  ```bash
  source venv/bin/activate
  ```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copiar el archivo de ejemplo y editar con tus configuraciones:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
# Django Settings
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=fatigue_detection_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# MQTT Settings
MQTT_BROKER=localhost
MQTT_PORT=1883
```

### 5. Configurar PostgreSQL

Crear la base de datos:

```sql
CREATE DATABASE fatigue_detection_db;
CREATE USER postgres WITH PASSWORD 'tu_password';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'America/Mexico_City';
GRANT ALL PRIVILEGES ON DATABASE fatigue_detection_db TO postgres;
```

### 6. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 8. Ejecutar el Servidor

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://localhost:8000`

## 📁 Estructura del Proyecto

```
ZZZ-Backend/
├── apps/
│   ├── users/              # Gestión de usuarios y autenticación
│   ├── devices/            # Gestión de dispositivos ESP32
│   ├── sensors/            # Datos de sensores y métricas
│   ├── analytics/          # Alertas y recomendaciones
│   └── mqtt_client/        # Cliente MQTT
├── config/                 # Configuración de Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── ml_models/              # Modelos de Machine Learning
├── notebooks/              # Jupyter Notebooks para ML
├── .env                    # Variables de entorno (no incluir en git)
├── .env.example            # Plantilla de variables de entorno
├── .gitignore
├── requirements.txt        # Dependencias de Python
├── manage.py
└── README.md
```

## 👥 Roles de Usuario

### 1. Administrador
- Gestionar Supervisores
- Ver estadísticas globales
- Configuración del sistema

### 2. Supervisor
- Gestionar Empleados
- Gestionar Dispositivos
- Ver dashboards de su equipo
- Gestionar alertas
- Recibir recomendaciones

### 3. Empleado
- Ver sus propias métricas
- Ver su historial de fatiga
- Recibir alertas personales

## 📊 Características Principales

### Métricas Monitoreadas
- **Ritmo Cardíaco:** BPM, HRV (RMSSD, SDNN)
- **Oxigenación:** SpO2 promedio, mínimo, desaturaciones
- **Movimiento:** Nivel de actividad, varianza, entropía
- **Índice de Fatiga:** 0-100 (calculado por ML)

### Sistema de Alertas
- Fatiga alta (>70%)
- SpO2 bajo (<90%)
- Ritmo cardíaco elevado sostenido
- Inactividad sospechosa

### Machine Learning
- Clustering automático para detección de patrones
- Predicción de niveles de fatiga
- Recomendaciones personalizadas

## 🔧 Comandos Útiles

```bash
# Ejecutar servidor de desarrollo
python manage.py runserver

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Shell interactivo de Django
python manage.py shell

# Ejecutar tests
python manage.py test

# Colectar archivos estáticos
python manage.py collectstatic
```

## 📝 Estado del Proyecto

**Fase Actual:** Fase 9 - Panel de Gestión Admin ✅

### Fase 1: Configuración del Proyecto Base ✅
- ✅ Entorno virtual creado
- ✅ Dependencias instaladas
- ✅ Proyecto Django inicializado
- ✅ Apps creadas (users, devices, sensors, analytics, mqtt_client)
- ✅ Configuración de settings.py
- ✅ Configuración de variables de entorno

### Fase 2: Sistema de Autenticación y Roles ✅
- ✅ Modelo CustomUser con roles (Admin, Supervisor, Empleado)
- ✅ Jerarquía de usuarios implementada
- ✅ Autenticación JWT configurada (60min access, 24hr refresh)
- ✅ 9 vistas de API (registro, login, perfiles, etc.)
- ✅ 7 serializers especializados por operación
- ✅ 7 permisos personalizados por rol
- ✅ Admin panel configurado
- ✅ Migraciones aplicadas
- ✅ Superusuario creado
- ✅ PostgreSQL configurado y funcionando

### Fase 3: Modelos de Base de Datos ✅
- ✅ Modelo Device (dispositivos ESP32)
- ✅ Modelo SensorData (datos raw de sensores)
- ✅ Modelo ProcessedMetrics (métricas procesadas)
- ✅ Modelo FatigueAlert (sistema de alertas)
- ✅ Modelo RoutineRecommendation (optimización de rutinas)
- ✅ 5 modelos con 64 campos totales
- ✅ 15 índices de performance
- ✅ Admin panels personalizados
- ✅ Validaciones y constraints
- ✅ Documentación completa (FASE_3_COMPLETADA.md)

### Fase 4: Integración MQTT ✅
- ✅ Cliente MQTT con callbacks completos (172 líneas)
- ✅ Auto-inicialización en Django startup
- ✅ Procesador de métricas (18+ cálculos, 318 líneas)
- ✅ Simulador ESP32 con 4 modos de actividad (288 líneas)
- ✅ Sistema de ventanas de tiempo (1 minuto)
- ✅ Cálculo de HRV (RMSSD, SDNN)
- ✅ Detección de desaturaciones
- ✅ Análisis de movimiento (RMS, entropía)
- ✅ Scripts de ayuda (setup_mqtt_test_data.py)
- ✅ Guía de pruebas completa (GUIA_PRUEBAS_MQTT.md)
- ✅ Documentación completa (FASE_4_COMPLETADA.md)

### Fase 5: Machine Learning ✅
- ✅ Script de exploración de datos (288 líneas)
- ✅ Feature engineering con 20 features (270 líneas)
- ✅ Modelos de clustering K-Means + DBSCAN (490 líneas)
- ✅ Servicio ML con fallback inteligente (237 líneas)
- ✅ Integración con procesador de métricas
- ✅ Normalización con StandardScaler
- ✅ Validación con 3 métricas (Silhouette, Davies-Bouldin, Calinski-Harabasz)
- ✅ 7 visualizaciones de análisis
- ✅ Sistema de predicción 0-100
- ✅ Documentación completa (FASE_5_COMPLETADA.md)
- ⏳ Validación end-to-end (requiere Mosquitto broker)

### Fase 6: APIs REST ✅
- ✅ 12 serializers con validaciones robustas (497 líneas)
- ✅ 3 ViewSets con 20+ endpoints (550 líneas)
- ✅ DeviceViewSet: CRUD + activate/deactivate/stats/my_device/summary
- ✅ SensorDataViewSet: CRUD + bulk_create/latest
- ✅ ProcessedMetricsViewSet: ReadOnly + stats/latest/timeline
- ✅ Permisos por rol (Admin/Supervisor/Empleado)
- ✅ Filtros avanzados (django-filter)
- ✅ Búsqueda por texto (SearchFilter)
- ✅ Ordenamiento múltiple (OrderingFilter)
- ✅ Paginación (50 registros/página)
- ✅ Optimización de queries (select_related)
- ✅ Documentación completa (FASE_6_COMPLETADA.md)

### Fase 7: Sistema de Alertas y Recomendaciones ✅
- ✅ 10 serializers especializados (1,095 líneas)
- ✅ FatigueAlertViewSet: 9 endpoints con CRUD + resolve/unresolve/stats
- ✅ RoutineRecommendationViewSet: 9 endpoints con CRUD + apply/reject/stats
- ✅ Sistema de detección automática de anomalías (293 líneas)
- ✅ 6 métodos de detección: fatiga, SpO2, FC, desaturaciones, riesgos combinados, offline
- ✅ Umbrales configurables (crítico ≥85, alto ≥70, medio ≥50)
- ✅ Integración con ML de Fase 5
- ✅ Prevención de alertas duplicadas
- ✅ Permisos por rol (Admin/Supervisor/Empleado)
- ✅ Filtros avanzados por severity, resolved, employee, device
- ✅ Endpoints de estadísticas agregadas
- ✅ Documentación completa (FASE_7_COMPLETADA.md)

### Fase 8: Dashboards y Visualizaciones ✅
- ✅ 19 serializers de dashboard (2,450 líneas totales)
- ✅ DashboardViewSet: 5 endpoints (overview, real_time, employee/supervisor/admin dashboards)
- ✅ VisualizationViewSet: 8 endpoints de visualización
- ✅ ReportViewSet: 5 endpoints de exportación (CSV/JSON)
- ✅ Sistema de métricas agregadas (diarias, semanales, mensuales)
- ✅ Tendencias de fatiga (por día/hora)
- ✅ Distribuciones: horaria (0-23h), semanal (Lun-Dom), por niveles
- ✅ Heatmap de fatiga (día × hora)
- ✅ Historial de alertas con severidad
- ✅ Efectividad de recomendaciones (antes/después)
- ✅ Análisis de correlaciones
- ✅ Métricas en tiempo real (últimos 5 min)
- ✅ Comparación entre empleados
- ✅ Estado de salud de dispositivos
- ✅ Reportes exportables: empleado, equipo, alertas, métricas, resumen ejecutivo
- ✅ Filtrado automático por rol (Admin/Supervisor/Empleado)
- ✅ Documentación completa (FASE_8_COMPLETADA.md)

### Fase 9: Panel de Gestión Admin ✅
- ✅ Modelo ActivityLog (auditoría completa del sistema)
- ✅ 6 serializers para administración (1,500 líneas totales)
- ✅ AdminViewSet: 7 endpoints de gestión
- ✅ CRUD completo de supervisores
- ✅ Dashboard del administrador
- ✅ Estadísticas del sistema (usuarios, dispositivos, alertas, métricas)
- ✅ Logs de actividad con filtros avanzados
- ✅ AdminStatsService: servicio de estadísticas
- ✅ Índice de salud del sistema (0-100)
- ✅ Ranking de supervisores por rendimiento
- ✅ Auditoría automática de acciones (IP, user-agent)
- ✅ Permisos IsAdmin
- ✅ Soft delete de supervisores
- ✅ Documentación completa (FASE_9_COMPLETADA.md)

### Próximas Fases:
- ⏳ Fase 10: Frontend React + TypeScript
- ⏳ Fase 11: Testing completo
- ⏳ Fase 12: Despliegue y documentación final

## 📚 Próximos Pasos

### Fase 10: Frontend React + TypeScript
1. Configurar React + Vite + TypeScript
2. Implementar autenticación JWT
3. Dashboards para cada rol
4. Gráficas interactivas con Chart.js
5. UI con DaisyUI + TailwindCSS

## 📖 Documentación Adicional

- **FASE_2_COMPLETADA.md** - Sistema de autenticación y roles
- **FASE_3_COMPLETADA.md** - Modelos de base de datos
- **FASE_4_COMPLETADA.md** - Integración MQTT
- **FASE_5_COMPLETADA.md** - Machine Learning
- **FASE_6_COMPLETADA.md** - APIs REST para dispositivos y sensores
- **FASE_7_COMPLETADA.md** - Sistema de alertas y recomendaciones
- **FASE_8_COMPLETADA.md** - Dashboards y visualizaciones
- **FASE_9_COMPLETADA.md** - Panel de gestión admin
- **GUIA_PRUEBAS_MQTT.md** - Guía de pruebas MQTT

## 🔌 API Endpoints

### Autenticación (`/api/auth/`)
- `POST /api/auth/register/` - Registro de usuarios
- `POST /api/auth/login/` - Login con JWT
- `POST /api/auth/token/refresh/` - Refresh token
- `GET /api/auth/profile/` - Perfil del usuario
- `PUT /api/auth/profile/update/` - Actualizar perfil

### Dispositivos (`/api/devices/`)
- `GET /api/devices/` - Listar dispositivos (filtros: status, is_active, employee, supervisor)
- `POST /api/devices/` - Crear dispositivo
- `GET /api/devices/{id}/` - Detalle del dispositivo
- `PUT/PATCH /api/devices/{id}/` - Actualizar dispositivo
- `DELETE /api/devices/{id}/` - Eliminar dispositivo
- `POST /api/devices/{id}/activate/` - Activar dispositivo
- `POST /api/devices/{id}/deactivate/` - Desactivar dispositivo
- `GET /api/devices/{id}/stats/?days=7` - Estadísticas del dispositivo
- `GET /api/devices/my_device/` - Dispositivo del empleado actual
- `GET /api/devices/summary/` - Resumen agregado

### Datos de Sensores (`/api/sensor-data/`)
- `GET /api/sensor-data/` - Listar datos (filtros: device, device_id, start_date, end_date, hours)
- `POST /api/sensor-data/` - Crear registro
- `GET /api/sensor-data/{id}/` - Detalle del registro
- `POST /api/sensor-data/bulk_create/` - Crear múltiples registros (hasta 1000)
- `GET /api/sensor-data/latest/` - Últimos datos por dispositivo

### Métricas Procesadas (`/api/processed-metrics/`)
- `GET /api/processed-metrics/` - Listar métricas (filtros: device, employee, fatigue_level, dates)
- `GET /api/processed-metrics/{id}/` - Detalle de métrica
- `GET /api/processed-metrics/stats/?days=7` - Estadísticas agregadas
- `GET /api/processed-metrics/latest/` - Últimas métricas por empleado
- `GET /api/processed-metrics/timeline/?hours=24&interval=60` - Timeline para gráficas

### Alertas de Fatiga (`/api/alerts/`)
- `GET /api/alerts/` - Listar alertas (filtros: severity, resolved, employee, supervisor, device)
- `POST /api/alerts/` - Crear alerta
- `GET /api/alerts/{id}/` - Detalle de alerta
- `PUT/PATCH /api/alerts/{id}/` - Actualizar alerta
- `DELETE /api/alerts/{id}/` - Eliminar alerta
- `POST /api/alerts/{id}/resolve/` - Resolver alerta
- `POST /api/alerts/{id}/unresolve/` - Reabrir alerta
- `GET /api/alerts/stats/` - Estadísticas de alertas
- `GET /api/alerts/my_alerts/` - Alertas del empleado actual

### Recomendaciones de Rutinas (`/api/recommendations/`)
- `GET /api/recommendations/` - Listar recomendaciones (filtros: recommendation_type, applied, employee)
- `POST /api/recommendations/` - Crear recomendación
- `GET /api/recommendations/{id}/` - Detalle de recomendación
- `PUT/PATCH /api/recommendations/{id}/` - Actualizar recomendación
- `DELETE /api/recommendations/{id}/` - Eliminar recomendación
- `POST /api/recommendations/{id}/apply/` - Aplicar recomendación
- `POST /api/recommendations/{id}/reject/` - Rechazar recomendación
- `GET /api/recommendations/stats/` - Estadísticas de recomendaciones
- `GET /api/recommendations/my_recommendations/` - Recomendaciones del empleado actual

### Dashboard (`/api/dashboard/`)
- `GET /api/dashboard/overview/` - Estadísticas generales del sistema
- `GET /api/dashboard/real_time/` - Métricas en tiempo real (últimos 5 min)
- `GET /api/dashboard/employee_dashboard/` - Dashboard personal del empleado
- `GET /api/dashboard/supervisor_dashboard/` - Dashboard de supervisor con métricas de equipo
- `GET /api/dashboard/admin_dashboard/` - Dashboard completo de administrador

### Visualizaciones (`/api/visualizations/`)
- `GET /api/visualizations/fatigue_trends/?days=7&interval=day` - Tendencias de fatiga
- `GET /api/visualizations/hourly_distribution/?days=30` - Distribución por hora (0-23)
- `GET /api/visualizations/weekly_distribution/?days=90` - Distribución por día de semana
- `GET /api/visualizations/fatigue_levels/?days=30` - Distribución de niveles de fatiga
- `GET /api/visualizations/alert_history/?days=30` - Historial de alertas
- `GET /api/visualizations/recommendation_effectiveness/` - Efectividad de recomendaciones
- `GET /api/visualizations/correlations/?days=30` - Análisis de correlaciones
- `GET /api/visualizations/heatmap_data/?days=30` - Heatmap día × hora

### Reportes (`/api/reports/`)
- `GET /api/reports/employee_report/?employee_id=5&days=30&format=csv` - Reporte de empleado (JSON/CSV)
- `GET /api/reports/team_report/?days=30&format=csv` - Reporte de equipo (JSON/CSV)
- `GET /api/reports/alerts_report/?days=30&format=csv` - Reporte de alertas (JSON/CSV)
- `GET /api/reports/metrics_report/?days=30&format=csv` - Reporte de métricas (JSON/CSV)
- `GET /api/reports/executive_summary/?format=csv` - Resumen ejecutivo (JSON/CSV)

### Administración (`/api/admin/`)
- `GET /api/admin/supervisors/?is_active=true&search=nombre` - Listar supervisores
- `POST /api/admin/supervisors/` - Crear supervisor
- `GET /api/admin/supervisors/{id}/` - Detalle de supervisor
- `PUT /api/admin/supervisors/{id}/` - Actualizar supervisor
- `DELETE /api/admin/supervisors/{id}/` - Desactivar supervisor
- `GET /api/admin/dashboard/` - Dashboard del administrador
- `GET /api/admin/system-stats/?period=week` - Estadísticas del sistema
- `GET /api/admin/activity-logs/?days=7&action=create` - Logs de actividad

## 👨‍💻 Autor

Luis Iván Islas Reyes - [GitHub](https://github.com/LuisIvanIslasReyes)

## 📄 Licencia

Este es un proyecto escolar.

---

**Nota:** Este proyecto simula un wearable mediante sensores IoT en ESP32 debido a limitaciones de hardware físico.
