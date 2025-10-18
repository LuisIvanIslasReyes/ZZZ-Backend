# 📚 API Documentation - Proyecto ZZZ Backend

## 🎯 **Descripción General**

El proyecto ZZZ (Zero to Zero-Fatigue Zone) es un sistema integral para monitorear y prevenir la fatiga laboral en tiempo real. Esta API proporciona todos los endpoints necesarios para gestionar usuarios, dispositivos, alertas, recomendaciones, analytics y configuraciones del sistema.

---

## 📋 **ÍNDICE DE ENDPOINTS**

### 🔐 **Autenticación** (`/api/auth/`)
- `POST /api/auth/login/` - Iniciar sesión
- `POST /api/auth/refresh/` - Renovar token JWT
- `POST /api/auth/register/` - Registrar usuario
- `GET/PUT /api/auth/profile/` - Perfil de usuario
- `POST /api/auth/change-password/` - Cambiar contraseña
- `POST /api/auth/fcm-token/` - Registrar token FCM
- `GET /api/auth/employees/` - Listar empleados
- `GET /api/auth/employees/<id>/` - Detalle de empleado

### 📱 **Dispositivos y Sensores** (`/api/`)
- `GET/POST /api/devices/` - Gestionar dispositivos
- `GET/PUT/DELETE /api/devices/<id>/` - Dispositivo específico
- `POST /api/sensor-data/` - Enviar datos de sensores
- `GET /api/employees/<id>/stress/` - Datos de estrés
- `GET /api/employees/<id>/stress/summary/` - Resumen de estrés
- `GET /api/supervisor/reports/` - Reportes para supervisores

### 🚨 **Sistema de Alertas** (`/api/alerts/`)
- `GET/POST /api/alerts/` - Gestionar alertas
- `GET/PUT/DELETE /api/alerts/<id>/` - Alerta específica
- `PUT /api/alerts/<id>/acknowledge/` - Reconocer alerta
- `PUT /api/alerts/<id>/resolve/` - Resolver alerta
- `GET /api/alerts/active/` - Alertas activas
- `GET /api/alerts/stats/` - Estadísticas de alertas
- `GET /api/alerts/employees/<id>/` - Alertas de empleado
- `GET/POST /api/alerts/rules/` - Reglas de alertas
- `GET/PUT/DELETE /api/alerts/rules/<id>/` - Gestionar reglas

### 💡 **Recomendaciones** (`/api/recommendations/`)
- `GET/POST /api/recommendations/` - Gestionar recomendaciones
- `GET/PUT/DELETE /api/recommendations/<id>/` - Recomendación específica
- `PUT /api/recommendations/<id>/apply/` - Aplicar recomendación
- `GET /api/recommendations/stats/` - Estadísticas
- `GET /api/recommendations/employees/<id>/` - Recomendaciones de empleado
- `GET/POST /api/recommendations/templates/` - Plantillas
- `GET/PUT/DELETE /api/recommendations/templates/<id>/` - Gestionar plantillas
- `GET/POST /api/recommendations/feedback/` - Feedback

### 📊 **Analytics** (`/api/analytics/`)
- `GET /api/analytics/patterns/<id>/` - Análisis de patrones
- `GET /api/analytics/comparatives/` - Análisis comparativo
- `GET /api/analytics/trends/` - Análisis de tendencias
- `GET /api/analytics/historical/<id>/` - Análisis histórico
- `GET /api/analytics/predictions/<id>/` - Predicciones
- `GET /api/analytics/dashboard/` - Dashboard

### 🏢 **Departamentos** (`/api/departments/`)
- `GET/POST /api/departments/` - Gestionar departamentos
- `GET/PUT/DELETE /api/departments/<id>/` - Departamento específico
- `GET /api/departments/<id>/employees/` - Empleados del departamento
- `POST /api/departments/<id>/employees/add/` - Agregar empleado
- `DELETE /api/departments/<id>/employees/<user_id>/` - Remover empleado
- `GET /api/departments/<id>/analytics/` - Analytics del departamento
- `GET/POST /api/departments/workshifts/` - Turnos de trabajo
- `GET/PUT/DELETE /api/departments/workshifts/<id>/` - Gestionar turno
- `GET /api/departments/workshifts/<id>/employees/` - Empleados en turno
- `POST /api/departments/workshifts/<id>/employees/assign/` - Asignar a turno

### ⚙️ **Configuración** (`/api/config/`)
- `GET /api/config/` - Configuraciones del sistema
- `GET/PUT /api/config/<key>/` - Configuración específica
- `GET /api/config/categories/` - Categorías de configuración
- `POST /api/config/reset/` - Resetear configuraciones
- `GET/POST /api/config/thresholds/` - Umbrales del sistema
- `GET/PUT/DELETE /api/config/thresholds/<id>/` - Gestionar umbrales
- `GET/PUT /api/config/notifications/` - Config de notificaciones
- `GET/PUT /api/config/notifications/<user_id>/` - Config por usuario
- `GET/PUT /api/config/system/` - Configuración general

### 🔔 **Notificaciones** (`/api/notifications/`)
- `GET /api/notifications/` - Listar notificaciones
- `GET /api/notifications/<id>/` - Detalle de notificación
- `PUT /api/notifications/<id>/read/` - Marcar como leída
- `PUT /api/notifications/mark-read/` - Marcar múltiples como leídas
- `GET /api/notifications/stats/` - Estadísticas
- `POST /api/notifications/send/` - Enviar notificación
- `GET /api/notifications/history/` - Historial
- `GET/POST /api/notifications/templates/` - Plantillas
- `GET/PUT/DELETE /api/notifications/templates/<id>/` - Gestionar plantillas
- `POST /api/notifications/templates/<id>/render/` - Previsualizar
- `GET /api/notifications/preferences/` - Preferencias
- `GET/PUT /api/notifications/preferences/<id>/` - Gestionar preferencias
- `PUT /api/notifications/preferences/bulk/` - Actualización masiva

---

## 🔐 **AUTENTICACIÓN**

### `POST /api/auth/login/`
**Descripción:** Iniciar sesión y obtener tokens JWT

**Permisos:** Público

**Body:**
```json
{
    "email": "usuario@ejemplo.com",
    "password": "contraseña123"
}
```

**Respuesta:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### `POST /api/auth/refresh/`
**Descripción:** Renovar token de acceso usando refresh token

**Permisos:** Público

**Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Respuesta:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### `POST /api/auth/register/`
**Descripción:** Registrar nuevo usuario

**Permisos:** Público

**Body:**
```json
{
    "email": "nuevo@ejemplo.com",
    "password": "contraseña123",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "employee"
}
```

**Respuesta:**
```json
{
    "id": 1,
    "email": "nuevo@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "employee"
}
```

### `GET /api/auth/profile/`
**Descripción:** Obtener perfil del usuario autenticado

**Permisos:** Autenticado

**Respuesta:**
```json
{
    "id": 1,
    "email": "usuario@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "employee",
    "employee_id": "EMP-001",
    "supervisor": 2
}
```

### `PUT /api/auth/profile/`
**Descripción:** Actualizar perfil del usuario

**Permisos:** Autenticado

**Body:**
```json
{
    "first_name": "Juan Carlos",
    "last_name": "Pérez González"
}
```

### `POST /api/auth/change-password/`
**Descripción:** Cambiar contraseña del usuario

**Permisos:** Autenticado

**Body:**
```json
{
    "old_password": "contraseña_actual",
    "new_password": "nueva_contraseña123"
}
```

**Respuesta:**
```json
{
    "message": "Contraseña actualizada exitosamente"
}
```

### `POST /api/auth/fcm-token/`
**Descripción:** Registrar token FCM para notificaciones push

**Permisos:** Autenticado

**Body:**
```json
{
    "fcm_token": "dA7X8K9L2M3N4O5P6Q7R8S9T0U1V2W3X4Y5Z"
}
```

### `GET /api/auth/employees/`
**Descripción:** Listar empleados (según permisos del usuario)

**Permisos:** Autenticado

**Query Parameters:**
- `role`: Filtrar por rol
- `department`: Filtrar por departamento

**Respuesta:**
```json
[
    {
        "id": 1,
        "email": "empleado@ejemplo.com",
        "first_name": "Ana",
        "last_name": "García",
        "role": "employee",
        "employee_id": "EMP-001"
    }
]
```

### `GET /api/auth/employees/<id>/`
**Descripción:** Obtener detalles de un empleado específico

**Permisos:** Supervisor o propietario

**Respuesta:**
```json
{
    "id": 1,
    "email": "empleado@ejemplo.com",
    "first_name": "Ana",
    "last_name": "García",
    "role": "employee",
    "employee_id": "EMP-001",
    "supervisor": 2,
    "department": "Desarrollo"
}
```

---

## 📱 **DISPOSITIVOS Y SENSORES**

### `GET /api/devices/`
**Descripción:** Listar dispositivos del usuario

**Permisos:** Autenticado

**Query Parameters:**
- `is_active`: Filtrar por estado activo
- `device_type`: Filtrar por tipo de dispositivo

**Respuesta:**
```json
[
    {
        "id": 1,
        "name": "Smartwatch Ana",
        "hardware_id": "SW001",
        "device_type": "smartwatch",
        "is_active": true,
        "employee": 1,
        "last_seen": "2025-10-17T10:30:00Z",
        "battery_level": 85
    }
]
```

### `POST /api/devices/`
**Descripción:** Registrar nuevo dispositivo

**Permisos:** Autenticado

**Body:**
```json
{
    "name": "Mi Smartwatch",
    "hardware_id": "SW002",
    "device_type": "smartwatch"
}
```

### `GET /api/devices/<id>/`
**Descripción:** Obtener detalles de un dispositivo específico

**Permisos:** Propietario o Supervisor

**Respuesta:**
```json
{
    "id": 1,
    "name": "Smartwatch Ana",
    "hardware_id": "SW001",
    "device_type": "smartwatch",
    "is_active": true,
    "employee": 1,
    "employee_name": "Ana García",
    "last_seen": "2025-10-17T10:30:00Z",
    "battery_level": 85,
    "firmware_version": "1.2.3"
}
```

### `PUT /api/devices/<id>/`
**Descripción:** Actualizar dispositivo

**Permisos:** Propietario o Supervisor

**Body:**
```json
{
    "name": "Smartwatch Ana - Actualizado",
    "is_active": false
}
```

### `DELETE /api/devices/<id>/`
**Descripción:** Eliminar dispositivo

**Permisos:** Propietario o Supervisor

### `POST /api/sensor-data/`
**Descripción:** Enviar datos de sensores en lotes

**Permisos:** Autenticado

**Body:**
```json
{
    "device_id": "SW001",
    "firmware_version": "1.2.3",
    "samples": [
        {
            "timestamp": "2025-10-17T10:30:00Z",
            "hr": 75,
            "spo2": 98,
            "accel_x": 0.1,
            "accel_y": 0.2,
            "accel_z": 9.8,
            "steps": 1250,
            "battery": 85
        }
    ]
}
```

**Respuesta:**
```json
{
    "message": "Datos recibidos exitosamente",
    "packet_id": 123,
    "samples_count": 1
}
```

### `GET /api/employees/<id>/stress/`
**Descripción:** Obtener datos de estrés de un empleado

**Permisos:** Propietario o Supervisor

**Query Parameters:**
- `days`: Días hacia atrás (default: 7)
- `start_date`: Fecha de inicio
- `end_date`: Fecha de fin

**Respuesta:**
```json
[
    {
        "id": 1,
        "employee": 1,
        "stress_score": 65.5,
        "window_start": "2025-10-17T09:00:00Z",
        "window_end": "2025-10-17T10:00:00Z",
        "avg_heart_rate": 75.2,
        "activity_level": "moderate"
    }
]
```

### `GET /api/employees/<id>/stress/summary/`
**Descripción:** Obtener resumen estadístico de estrés

**Permisos:** Propietario o Supervisor

**Query Parameters:**
- `days`: Días hacia atrás (default: 7)

**Respuesta:**
```json
{
    "avg_stress": 62.3,
    "min_stress": 45.1,
    "max_stress": 78.9,
    "current_stress": 65.5,
    "trend": "stable",
    "data_points": 168
}
```

### `GET /api/supervisor/reports/`
**Descripción:** Obtener reportes consolidados para supervisores

**Permisos:** Supervisor

**Query Parameters:**
- `days`: Días hacia atrás (default: 7)

**Respuesta:**
```json
{
    "employees_count": 5,
    "date_range_days": 7,
    "reports": [
        {
            "employee_id": 1,
            "employee_name": "Ana García",
            "avg_stress": 65.2,
            "max_stress": 78.9,
            "current_stress": 67.1,
            "data_points": 168
        }
    ]
}
```

---

## 🚨 **SISTEMA DE ALERTAS**

### `GET /api/alerts/`
**Descripción:** Listar alertas según permisos del usuario

**Permisos:** Autenticado

**Query Parameters:**
- `is_active`: Filtrar por alertas activas
- `is_acknowledged`: Filtrar por alertas reconocidas
- `alert_type`: Filtrar por tipo de alerta
- `severity`: Filtrar por severidad
- `employee_id`: Filtrar por empleado

**Respuesta:**
```json
[
    {
        "id": 1,
        "title": "Estrés Alto Detectado",
        "message": "Se ha detectado un nivel de estrés alto en el empleado",
        "alert_type": "stress_high",
        "severity": "high",
        "employee": 1,
        "employee_name": "Ana García",
        "device": 1,
        "device_name": "Smartwatch Ana",
        "is_active": true,
        "is_acknowledged": false,
        "created_at": "2025-10-17T10:30:00Z"
    }
]
```

### `POST /api/alerts/`
**Descripción:** Crear nueva alerta

**Permisos:** Supervisor

**Body:**
```json
{
    "title": "Alerta Personalizada",
    "message": "Descripción de la alerta",
    "alert_type": "custom",
    "severity": "medium",
    "employee": 1,
    "device": 1,
    "data": {
        "custom_field": "valor"
    }
}
```

### `GET /api/alerts/<id>/`
**Descripción:** Obtener detalles de una alerta específica

**Permisos:** Propietario o Supervisor

**Respuesta:**
```json
{
    "id": 1,
    "title": "Estrés Alto Detectado",
    "message": "Se ha detectado un nivel de estrés alto",
    "alert_type": "stress_high",
    "severity": "high",
    "employee": 1,
    "employee_name": "Ana García",
    "device": 1,
    "device_name": "Smartwatch Ana",
    "is_active": true,
    "is_acknowledged": false,
    "acknowledged_at": null,
    "acknowledged_by": null,
    "data": {},
    "created_at": "2025-10-17T10:30:00Z",
    "resolved_at": null
}
```

### `PUT /api/alerts/<id>/acknowledge/`
**Descripción:** Reconocer una alerta

**Permisos:** Propietario o Supervisor

**Body:**
```json
{
    "notes": "Alerta revisada y en seguimiento"
}
```

**Respuesta:**
```json
{
    "message": "Alerta reconocida exitosamente",
    "acknowledged_at": "2025-10-17T10:35:00Z",
    "acknowledged_by": "Juan Supervisor"
}
```

### `PUT /api/alerts/<id>/resolve/`
**Descripción:** Resolver una alerta (solo supervisores)

**Permisos:** Supervisor

**Respuesta:**
```json
{
    "message": "Alerta resuelta exitosamente",
    "resolved_at": "2025-10-17T10:40:00Z"
}
```

### `GET /api/alerts/active/`
**Descripción:** Listar solo alertas activas

**Permisos:** Autenticado

**Respuesta:** Similar a `GET /api/alerts/` pero solo alertas activas

### `GET /api/alerts/stats/`
**Descripción:** Obtener estadísticas de alertas

**Permisos:** Supervisor

**Query Parameters:**
- `days`: Días hacia atrás (default: 7)

**Respuesta:**
```json
{
    "total_alerts": 25,
    "active_alerts": 8,
    "acknowledged_alerts": 15,
    "critical_alerts": 3,
    "alerts_by_type": {
        "stress_high": 10,
        "fatigue_critical": 5,
        "device_offline": 3
    },
    "alerts_by_severity": {
        "low": 5,
        "medium": 12,
        "high": 6,
        "critical": 2
    }
}
```

### `GET /api/alerts/employees/<employee_id>/`
**Descripción:** Obtener alertas de un empleado específico

**Permisos:** Propietario o Supervisor

**Respuesta:** Lista de alertas del empleado

### `GET /api/alerts/rules/`
**Descripción:** Listar reglas de alertas

**Permisos:** Supervisor

**Respuesta:**
```json
[
    {
        "id": 1,
        "name": "Regla Estrés Alto",
        "description": "Generar alerta cuando el estrés supere 70",
        "alert_type": "stress_high",
        "severity": "high",
        "conditions": {
            "stress_score": {"gt": 70},
            "duration_minutes": 15
        },
        "is_active": true
    }
]
```

### `POST /api/alerts/rules/`
**Descripción:** Crear nueva regla de alerta

**Permisos:** Supervisor

**Body:**
```json
{
    "name": "Nueva Regla",
    "description": "Descripción de la regla",
    "alert_type": "custom",
    "severity": "medium",
    "conditions": {
        "field": "value"
    }
}
```

---

## 💡 **RECOMENDACIONES**

### `GET /api/recommendations/`
**Descripción:** Listar recomendaciones según permisos

**Permisos:** Autenticado

**Query Parameters:**
- `is_active`: Filtrar por activas
- `is_applied`: Filtrar por aplicadas
- `recommendation_type`: Filtrar por tipo
- `priority`: Filtrar por prioridad
- `employee_id`: Filtrar por empleado
- `include_expired`: Incluir expiradas

**Respuesta:**
```json
[
    {
        "id": 1,
        "title": "Tomar un Descanso",
        "description": "Se recomienda tomar un descanso de 15 minutos",
        "recommendation_type": "break",
        "priority": "high",
        "employee": 1,
        "employee_name": "Ana García",
        "template": 1,
        "template_name": "Descanso Estándar",
        "instructions": "1. Alejarse del puesto de trabajo\n2. Realizar respiración profunda",
        "duration_minutes": 15,
        "is_active": true,
        "is_applied": false,
        "created_at": "2025-10-17T10:30:00Z",
        "expires_at": "2025-10-17T18:00:00Z",
        "is_expired": false
    }
]
```

### `POST /api/recommendations/`
**Descripción:** Crear nueva recomendación

**Permisos:** Supervisor

**Body:**
```json
{
    "title": "Hidratación",
    "description": "Beber agua para mantenerse hidratado",
    "recommendation_type": "hydration",
    "priority": "medium",
    "employee": 1,
    "instructions": "Beber al menos 250ml de agua",
    "duration_minutes": 5,
    "expires_at": "2025-10-17T18:00:00Z"
}
```

### `GET /api/recommendations/<id>/`
**Descripción:** Obtener detalles de una recomendación

**Permisos:** Propietario o Supervisor

**Respuesta:** Detalles completos de la recomendación

### `PUT /api/recommendations/<id>/apply/`
**Descripción:** Marcar recomendación como aplicada

**Permisos:** Propietario o Supervisor

**Body:**
```json
{
    "effectiveness_rating": 4,
    "feedback_notes": "La recomendación fue muy útil"
}
```

**Respuesta:**
```json
{
    "message": "Recomendación aplicada exitosamente",
    "applied_at": "2025-10-17T10:45:00Z"
}
```

### `GET /api/recommendations/stats/`
**Descripción:** Estadísticas de recomendaciones

**Permisos:** Supervisor

**Query Parameters:**
- `days`: Días hacia atrás (default: 30)

**Respuesta:**
```json
{
    "total_recommendations": 50,
    "active_recommendations": 15,
    "applied_recommendations": 30,
    "pending_recommendations": 20,
    "avg_effectiveness_rating": 4.2,
    "recommendations_by_type": {
        "break": 20,
        "hydration": 15,
        "exercise": 10
    },
    "recommendations_by_priority": {
        "low": 10,
        "medium": 25,
        "high": 15
    }
}
```

### `GET /api/recommendations/employees/<employee_id>/`
**Descripción:** Recomendaciones de un empleado específico

**Permisos:** Propietario o Supervisor

**Query Parameters:**
- `include_expired`: Incluir expiradas

**Respuesta:** Lista de recomendaciones del empleado

### `GET /api/recommendations/templates/`
**Descripción:** Listar plantillas de recomendaciones

**Permisos:** Supervisor

**Respuesta:**
```json
[
    {
        "id": 1,
        "name": "Descanso Estándar",
        "title": "Tomar un Descanso",
        "description": "Plantilla para descansos regulares",
        "recommendation_type": "break",
        "priority": "medium",
        "instructions": "Pasos para tomar un descanso efectivo",
        "duration_minutes": 15,
        "is_active": true
    }
]
```

### `POST /api/recommendations/templates/`
**Descripción:** Crear plantilla de recomendación

**Permisos:** Supervisor

**Body:**
```json
{
    "name": "Nueva Plantilla",
    "title": "Título de la Recomendación",
    "description": "Descripción de la plantilla",
    "recommendation_type": "custom",
    "priority": "medium",
    "instructions": "Instrucciones detalladas",
    "duration_minutes": 10
}
```

### `GET /api/recommendations/feedback/`
**Descripción:** Listar feedback de recomendaciones

**Permisos:** Supervisor (ver todo) o Empleado (solo suyo)

**Respuesta:**
```json
[
    {
        "id": 1,
        "recommendation": 1,
        "recommendation_title": "Tomar un Descanso",
        "usefulness_rating": 5,
        "ease_of_implementation": 4,
        "effectiveness_rating": 4,
        "comments": "Muy útil para reducir el estrés",
        "would_recommend": true,
        "created_at": "2025-10-17T11:00:00Z"
    }
]
```

### `POST /api/recommendations/feedback/`
**Descripción:** Crear feedback para recomendación

**Permisos:** Empleado (para sus recomendaciones)

**Body:**
```json
{
    "recommendation": 1,
    "usefulness_rating": 5,
    "ease_of_implementation": 4,
    "effectiveness_rating": 4,
    "comments": "Muy útil",
    "would_recommend": true,
    "implementation_time_minutes": 15
}
```

---

## 📊 **ANALYTICS**

### `GET /api/analytics/patterns/<employee_id>/`
**Descripción:** Análisis de patrones de fatiga/estrés de un empleado

**Permisos:** Propietario o Supervisor

**Query Parameters:**
- `days`: Días hacia atrás (default: 30)

**Respuesta:**
```json
{
    "employee_id": 1,
    "employee_name": "Ana García",
    "patterns": {
        "daily_patterns": {
            "0": 62.5,
            "1": 58.3,
            "2": 65.2
        },
        "weekly_consistency": true,
        "stress_variability": 23.4
    },
    "peak_stress_hours": [14, 16, 10],
    "average_stress_by_hour": {
        "9": 55.2,
        "10": 68.1,
        "11": 62.3
    },
    "stress_trend": "increasing",
    "fatigue_indicators": {
        "high_stress_frequency_percent": 25.5,
        "avg_stress_level": 64.2,
        "stress_spikes_per_week": 3,
        "recovery_time_hours": 2.5
    }
}
```

### `GET /api/analytics/comparatives/`
**Descripción:** Análisis comparativo entre empleados, departamentos o períodos

**Permisos:** Supervisor

**Query Parameters:**
- `type`: employees, departments, time_periods
- `days`: Días hacia atrás

**Respuesta para type=employees:**
```json
{
    "comparison_type": "employees",
    "baseline_period": {
        "days": 30,
        "start_date": "2025-09-17T00:00:00Z"
    },
    "comparison_period": {
        "end_date": "2025-10-17T00:00:00Z"
    },
    "employees": [
        {
            "employee_id": 1,
            "employee_name": "Ana García",
            "avg_stress": 65.2,
            "max_stress": 78.9,
            "min_stress": 45.1,
            "data_points": 720
        }
    ],
    "metrics": {
        "total_employees": 5,
        "avg_stress_overall": 62.3
    },
    "insights": [
        "2 empleados con estrés alto (>70)",
        "3 empleados con estrés bajo (<40)"
    ]
}
```

### `GET /api/analytics/trends/`
**Descripción:** Análisis de tendencias

**Permisos:** Supervisor

**Query Parameters:**
- `entity_type`: overall, department, shift
- `entity_id`: ID de la entidad (si aplica)
- `period`: daily, weekly, monthly

**Respuesta:**
```json
{
    "period": "weekly",
    "entity_type": "overall",
    "entity_id": null,
    "trends": {
        "stress_trend": [65.2, 63.1, 67.8, 62.4],
        "alert_trend": [5, 3, 8, 4],
        "productivity_indicators": {
            "efficiency_score": 85.2,
            "wellness_index": 78.9
        }
    },
    "predictions": {
        "next_week_stress_avg": 64.5,
        "potential_high_risk_days": ["2025-10-18", "2025-10-20"],
        "confidence_score": 0.75
    },
    "recommendations": [
        "Implementar pausas adicionales en horarios de alto estrés",
        "Revisar carga de trabajo en días de pico"
    ]
}
```

### `GET /api/analytics/historical/<employee_id>/`
**Descripción:** Análisis histórico completo de un empleado

**Permisos:** Propietario o Supervisor

**Respuesta:**
```json
{
    "employee_id": 1,
    "employee_name": "Ana García",
    "time_range": {
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-10-17T00:00:00Z",
        "total_days": 290
    },
    "metrics": {
        "total_measurements": 6960,
        "avg_stress": 63.4,
        "max_stress": 89.2,
        "min_stress": 32.1
    },
    "milestones": [
        {
            "type": "highest_stress",
            "date": "2025-08-15",
            "value": 89.2,
            "description": "Nivel de estrés más alto: 89.2"
        },
        {
            "type": "lowest_stress",
            "date": "2025-06-20",
            "value": 32.1,
            "description": "Nivel de estrés más bajo: 32.1"
        }
    ],
    "progression": {
        "monthly_averages": [58.2, 61.5, 65.8, 63.2],
        "overall_trend": "stable",
        "improvement_rate": 0.5
    }
}
```

### `GET /api/analytics/predictions/<employee_id>/`
**Descripción:** Predicciones de fatiga/estrés

**Permisos:** Propietario o Supervisor

**Query Parameters:**
- `hours`: Horizonte de predicción en horas (default: 24)

**Respuesta:**
```json
{
    "employee_id": 1,
    "employee_name": "Ana García",
    "prediction_horizon_hours": 24,
    "predicted_stress_levels": [
        {
            "hour": 1,
            "predicted_stress": 66.2,
            "confidence": 0.95
        },
        {
            "hour": 2,
            "predicted_stress": 68.1,
            "confidence": 0.93
        }
    ],
    "risk_assessment": {
        "risk_level": "medium",
        "risk_score": 0.6,
        "max_predicted_stress": 75.3,
        "avg_predicted_stress": 67.8
    },
    "recommended_actions": [
        "Tomar descanso de 10 minutos cada hora",
        "Hidratarse adecuadamente",
        "Revisar postura de trabajo"
    ]
}
```

### `GET /api/analytics/dashboard/`
**Descripción:** Estadísticas para dashboard principal

**Permisos:** Supervisor

**Respuesta:**
```json
{
    "total_employees": 25,
    "active_devices": 22,
    "avg_stress_level": 63.4,
    "high_risk_employees": 3,
    "alerts_today": 8,
    "recommendations_pending": 12,
    "stress_distribution": {
        "low": 8,
        "medium": 12,
        "high": 5
    },
    "hourly_stress_trend": [
        {
            "hour": 9,
            "avg_stress": 55.2,
            "employee_count": 20
        }
    ],
    "department_comparison": [
        {
            "department_name": "Desarrollo",
            "avg_stress": 65.3,
            "employee_count": 10
        }
    ],
    "alert_trends": [
        {
            "date": "2025-10-17",
            "alert_count": 8
        }
    ]
}
```

---

## 🏢 **DEPARTAMENTOS**

### `GET /api/departments/`
**Descripción:** Listar departamentos

**Permisos:** Supervisor

**Respuesta:**
```json
[
    {
        "id": 1,
        "name": "Desarrollo",
        "description": "Departamento de desarrollo de software",
        "code": "DEV",
        "parent_department": null,
        "parent_department_name": null,
        "manager": 2,
        "manager_name": "Juan Supervisor",
        "employee_count": 10,
        "sub_departments": ["Frontend", "Backend"],
        "is_active": true,
        "location": "Piso 3",
        "email": "dev@empresa.com",
        "phone": "+1234567890",
        "created_at": "2025-01-01T00:00:00Z"
    }
]
```

### `POST /api/departments/`
**Descripción:** Crear nuevo departamento

**Permisos:** Supervisor

**Body:**
```json
{
    "name": "Nuevo Departamento",
    "description": "Descripción del departamento",
    "code": "NEW",
    "manager": 2,
    "location": "Piso 2",
    "email": "nuevo@empresa.com"
}
```

### `GET /api/departments/<id>/`
**Descripción:** Obtener detalles de un departamento

**Permisos:** Supervisor

**Respuesta:** Detalles completos del departamento

### `GET /api/departments/<id>/employees/`
**Descripción:** Listar empleados del departamento

**Permisos:** Supervisor

**Respuesta:**
```json
[
    {
        "id": 1,
        "user": 1,
        "user_name": "Ana García",
        "user_email": "ana@empresa.com",
        "department": 1,
        "department_name": "Desarrollo",
        "position": "Desarrolladora Senior",
        "is_primary": true,
        "joined_at": "2025-01-15T00:00:00Z",
        "left_at": null
    }
]
```

### `POST /api/departments/<id>/employees/add/`
**Descripción:** Agregar empleado al departamento

**Permisos:** Manager del departamento o Admin

**Body:**
```json
{
    "user_id": 3,
    "position": "Desarrollador Junior",
    "is_primary": true
}
```

### `DELETE /api/departments/<id>/employees/<user_id>/`
**Descripción:** Remover empleado del departamento

**Permisos:** Manager del departamento o Admin

**Respuesta:**
```json
{
    "message": "Empleado removido del departamento exitosamente"
}
```

### `GET /api/departments/<id>/analytics/`
**Descripción:** Analytics del departamento

**Permisos:** Manager del departamento o Supervisor

**Query Parameters:**
- `days`: Días hacia atrás (default: 7)

**Respuesta:**
```json
{
    "department_id": 1,
    "department_name": "Desarrollo",
    "total_employees": 10,
    "active_employees": 8,
    "avg_stress_level": 64.2,
    "high_stress_employees": 2,
    "total_alerts": 15,
    "active_devices": 9,
    "stress_distribution": {
        "low": 3,
        "medium": 5,
        "high": 2
    },
    "shift_performance": [
        {
            "shift_name": "Mañana",
            "employee_count": 6,
            "avg_stress": 62.1
        }
    ],
    "trends": {
        "stress_trend": "stable",
        "alert_trend": "decreasing",
        "productivity_trend": "improving"
    }
}
```

### `GET /api/departments/workshifts/`
**Descripción:** Listar turnos de trabajo

**Permisos:** Supervisor

**Query Parameters:**
- `department_id`: Filtrar por departamento

**Respuesta:**
```json
[
    {
        "id": 1,
        "name": "Turno Mañana",
        "description": "Turno matutino estándar",
        "start_time": "08:00:00",
        "end_time": "16:00:00",
        "work_days": [0, 1, 2, 3, 4],
        "department": 1,
        "department_name": "Desarrollo",
        "duration_hours": 8.0,
        "employee_count": 6,
        "is_active": true,
        "break_duration_minutes": 60
    }
]
```

### `POST /api/departments/workshifts/`
**Descripción:** Crear turno de trabajo

**Permisos:** Supervisor

**Body:**
```json
{
    "name": "Turno Noche",
    "description": "Turno nocturno",
    "start_time": "22:00:00",
    "end_time": "06:00:00",
    "work_days": [0, 1, 2, 3, 4],
    "department": 1,
    "break_duration_minutes": 90
}
```

### `GET /api/departments/workshifts/<id>/employees/`
**Descripción:** Empleados asignados al turno

**Permisos:** Supervisor

**Respuesta:**
```json
[
    {
        "id": 1,
        "user": 1,
        "user_name": "Ana García",
        "work_shift": 1,
        "shift_name": "Turno Mañana",
        "department_name": "Desarrollo",
        "start_date": "2025-10-01",
        "end_date": null,
        "is_active": true,
        "created_at": "2025-10-01T00:00:00Z"
    }
]
```

### `POST /api/departments/workshifts/<id>/employees/assign/`
**Descripción:** Asignar empleado a turno

**Permisos:** Manager del departamento o Admin

**Body:**
```json
{
    "user": 3,
    "start_date": "2025-10-18",
    "end_date": null,
    "is_active": true
}
```

---

## ⚙️ **CONFIGURACIÓN**

### `GET /api/config/`
**Descripción:** Listar configuraciones del sistema

**Permisos:** Supervisor

**Query Parameters:**
- `category`: Filtrar por categoría

**Respuesta:**
```json
[
    {
        "id": 1,
        "key": "stress_alert_threshold",
        "value": 70,
        "category": "thresholds",
        "description": "Umbral para generar alertas de estrés",
        "data_type": "integer",
        "min_value": 0,
        "max_value": 100,
        "is_active": true,
        "is_editable": true,
        "updated_by": 2,
        "updated_by_name": "Admin User",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-10-15T10:00:00Z"
    }
]
```

### `GET /api/config/<key>/`
**Descripción:** Obtener configuración específica

**Permisos:** Supervisor

**Respuesta:** Detalles de la configuración

### `PUT /api/config/<key>/`
**Descripción:** Actualizar configuración

**Permisos:** Supervisor

**Body:**
```json
{
    "value": 75,
    "description": "Umbral actualizado para alertas de estrés"
}
```

### `GET /api/config/categories/`
**Descripción:** Listar categorías de configuración

**Permisos:** Supervisor

**Respuesta:**
```json
{
    "categories": [
        {
            "key": "thresholds",
            "name": "Umbrales",
            "config_count": 5
        },
        {
            "key": "system",
            "name": "Sistema",
            "config_count": 8
        }
    ]
}
```

### `POST /api/config/reset/`
**Descripción:** Resetear configuraciones a valores por defecto

**Permisos:** Supervisor

**Body:**
```json
{
    "category": "thresholds"
}
```
o
```json
{
    "key": "stress_alert_threshold"
}
```

### `GET /api/config/thresholds/`
**Descripción:** Listar umbrales del sistema

**Permisos:** Supervisor

**Respuesta:**
```json
[
    {
        "id": 1,
        "name": "stress_score",
        "description": "Umbrales para puntuación de estrés",
        "low_threshold": 40.0,
        "medium_threshold": 60.0,
        "high_threshold": 75.0,
        "critical_threshold": 85.0,
        "metric_type": "stress_score",
        "is_active": true,
        "updated_by": 2,
        "updated_by_name": "Admin User",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-10-15T10:00:00Z"
    }
]
```

### `POST /api/config/thresholds/`
**Descripción:** Crear nuevo umbral

**Permisos:** Supervisor

**Body:**
```json
{
    "name": "heart_rate_rest",
    "description": "Umbrales para ritmo cardíaco en reposo",
    "low_threshold": 60.0,
    "medium_threshold": 80.0,
    "high_threshold": 100.0,
    "critical_threshold": 120.0,
    "metric_type": "heart_rate"
}
```

### `GET /api/config/notifications/`
**Descripción:** Obtener configuración de notificaciones del usuario actual

**Permisos:** Autenticado

**Respuesta:**
```json
{
    "id": 1,
    "user": 1,
    "user_name": "Ana García",
    "email_alerts_enabled": true,
    "email_recommendations_enabled": true,
    "email_reports_enabled": false,
    "email_frequency": "immediate",
    "push_alerts_enabled": true,
    "push_recommendations_enabled": true,
    "push_quiet_hours_start": "22:00:00",
    "push_quiet_hours_end": "07:00:00",
    "stress_alert_threshold": "high",
    "weekly_report_enabled": true,
    "monthly_report_enabled": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-10-15T10:00:00Z"
}
```

### `PUT /api/config/notifications/`
**Descripción:** Actualizar configuración de notificaciones

**Permisos:** Autenticado

**Body:**
```json
{
    "email_alerts_enabled": false,
    "push_quiet_hours_start": "23:00:00",
    "stress_alert_threshold": "critical"
}
```

### `GET /api/config/system/`
**Descripción:** Obtener configuración general del sistema

**Permisos:** Supervisor

**Respuesta:**
```json
{
    "stress_thresholds": {
        "id": 1,
        "name": "stress_score",
        "low_threshold": 40.0,
        "medium_threshold": 60.0,
        "high_threshold": 75.0,
        "critical_threshold": 85.0
    },
    "heart_rate_thresholds": {
        "id": 2,
        "name": "heart_rate",
        "low_threshold": 60.0,
        "medium_threshold": 80.0,
        "high_threshold": 100.0,
        "critical_threshold": 120.0
    },
    "alert_settings": {
        "auto_resolve_hours": 24,
        "escalation_enabled": true
    },
    "notification_settings": {
        "batch_notifications": true,
        "max_notifications_per_hour": 10
    },
    "device_settings": {
        "offline_threshold_minutes": 30,
        "battery_alert_threshold": 20
    },
    "analytics_settings": {
        "data_retention_days": 365,
        "ml_predictions_enabled": true
    }
}
```

### `PUT /api/config/system/`
**Descripción:** Actualizar configuración del sistema

**Permisos:** Supervisor

**Body:**
```json
{
    "stress_thresholds": {
        "low_threshold": 35.0,
        "medium_threshold": 65.0,
        "high_threshold": 80.0,
        "critical_threshold": 90.0
    },
    "alert_settings": {
        "auto_resolve_hours": 48
    }
}
```

---

## 🔔 **NOTIFICACIONES**

### `GET /api/notifications/`
**Descripción:** Listar notificaciones del usuario actual

**Permisos:** Autenticado

**Query Parameters:**
- `is_read`: Filtrar por leídas/no leídas
- `type`: Filtrar por tipo de notificación
- `priority`: Filtrar por prioridad
- `days`: Días hacia atrás

**Respuesta:**
```json
[
    {
        "id": 1,
        "title": "Alerta de Estrés Alto",
        "message": "Se ha detectado un nivel de estrés alto en tu dispositivo",
        "notification_type": "alert",
        "priority": "high",
        "recipient": 1,
        "recipient_name": "Ana García",
        "sender": 2,
        "sender_name": "Sistema",
        "channels": ["push", "email"],
        "is_read": false,
        "read_at": null,
        "delivery_status": "delivered",
        "related_alert": 1,
        "related_recommendation": null,
        "data": {},
        "scheduled_for": null,
        "sent_at": "2025-10-17T10:30:00Z",
        "created_at": "2025-10-17T10:30:00Z"
    }
]
```

### `GET /api/notifications/<id>/`
**Descripción:** Obtener detalles de notificación (la marca como leída automáticamente)

**Permisos:** Propietario

**Respuesta:** Detalles completos de la notificación

### `PUT /api/notifications/<id>/read/`
**Descripción:** Marcar notificación específica como leída

**Permisos:** Propietario

**Respuesta:**
```json
{
    "message": "Notificación marcada como leída"
}
```

### `PUT /api/notifications/mark-read/`
**Descripción:** Marcar múltiples notificaciones como leídas

**Permisos:** Autenticado

**Body (opcional):**
```json
{
    "notification_ids": [1, 2, 3]
}
```

Si no se proporcionan IDs, marca todas las no leídas como leídas.

**Respuesta:**
```json
{
    "message": "3 notificaciones marcadas como leídas"
}
```

### `GET /api/notifications/stats/`
**Descripción:** Estadísticas de notificaciones del usuario

**Permisos:** Autenticado

**Respuesta:**
```json
{
    "total_notifications": 45,
    "unread_notifications": 8,
    "notifications_today": 5,
    "notifications_by_type": {
        "alert": 20,
        "recommendation": 15,
        "system": 10
    },
    "notifications_by_priority": {
        "low": 10,
        "medium": 25,
        "high": 8,
        "urgent": 2
    },
    "delivery_success_rate": 98.5
}
```

### `POST /api/notifications/send/`
**Descripción:** Enviar notificación a usuarios (solo supervisores)

**Permisos:** Supervisor

**Body:**
```json
{
    "title": "Reunión de Equipo",
    "message": "Recordatorio: Reunión de equipo mañana a las 10:00 AM",
    "notification_type": "system",
    "priority": "medium",
    "recipients": [1, 3, 5],
    "channels": ["push", "email"],
    "scheduled_for": "2025-10-18T09:00:00Z",
    "data": {
        "meeting_id": "123",
        "location": "Sala de Juntas"
    }
}
```

**Respuesta:**
```json
{
    "message": "Notificaciones creadas para 3 usuarios",
    "notification_ids": [10, 11, 12]
}
```

### `GET /api/notifications/history/`
**Descripción:** Historial de notificaciones (para supervisores)

**Permisos:** Supervisor

**Query Parameters:**
- `type`: Filtrar por tipo
- `recipient_id`: Filtrar por destinatario
- `days`: Días hacia atrás (default: 30)

**Respuesta:** Lista de notificaciones según permisos

### `GET /api/notifications/templates/`
**Descripción:** Listar plantillas de notificaciones

**Permisos:** Supervisor

**Respuesta:**
```json
[
    {
        "id": 1,
        "name": "Alerta Estrés Alto",
        "description": "Plantilla para alertas de estrés alto",
        "title_template": "Alerta: Estrés Alto Detectado",
        "message_template": "Se ha detectado un nivel de estrés de {{stress_level}} en {{employee_name}}",
        "notification_type": "alert",
        "default_priority": "high",
        "default_channels": ["push", "email"],
        "available_variables": ["stress_level", "employee_name", "timestamp"],
        "is_active": true,
        "created_at": "2025-01-01T00:00:00Z"
    }
]
```

### `POST /api/notifications/templates/`
**Descripción:** Crear plantilla de notificación

**Permisos:** Supervisor

**Body:**
```json
{
    "name": "Nueva Plantilla",
    "description": "Descripción de la plantilla",
    "title_template": "{{title}}",
    "message_template": "Hola {{employee_name}}, {{message}}",
    "notification_type": "system",
    "default_priority": "medium",
    "default_channels": ["push"],
    "available_variables": ["title", "message", "employee_name"]
}
```

### `POST /api/notifications/templates/<id>/render/`
**Descripción:** Previsualizar plantilla con contexto

**Permisos:** Supervisor

**Body:**
```json
{
    "context": {
        "employee_name": "Ana García",
        "stress_level": 75,
        "timestamp": "2025-10-17T10:30:00Z"
    }
}
```

**Respuesta:**
```json
{
    "rendered_title": "Alerta: Estrés Alto Detectado",
    "rendered_message": "Se ha detectado un nivel de estrés de 75 en Ana García",
    "available_variables": ["stress_level", "employee_name", "timestamp"]
}
```

### `GET /api/notifications/preferences/`
**Descripción:** Obtener preferencias de notificación del usuario

**Permisos:** Autenticado

**Respuesta:**
```json
[
    {
        "id": 1,
        "user": 1,
        "user_name": "Ana García",
        "notification_type": "alert",
        "email_enabled": true,
        "push_enabled": true,
        "sms_enabled": false,
        "in_app_enabled": true,
        "frequency": "immediate",
        "quiet_hours_enabled": true,
        "quiet_hours_start": "22:00:00",
        "quiet_hours_end": "07:00:00",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-10-15T10:00:00Z"
    }
]
```

### `GET /api/notifications/preferences/<id>/`
**Descripción:** Obtener preferencia específica

**Permisos:** Propietario

**Respuesta:** Detalles de la preferencia

### `PUT /api/notifications/preferences/<id>/`
**Descripción:** Actualizar preferencia de notificación

**Permisos:** Propietario

**Body:**
```json
{
    "email_enabled": false,
    "frequency": "daily",
    "quiet_hours_start": "23:00:00"
}
```

### `PUT /api/notifications/preferences/bulk/`
**Descripción:** Actualizar múltiples preferencias

**Permisos:** Autenticado

**Body:**
```json
{
    "preferences": [
        {
            "id": 1,
            "email_enabled": false,
            "push_enabled": true
        },
        {
            "id": 2,
            "frequency": "daily"
        }
    ]
}
```

**Respuesta:**
```json
{
    "message": "Actualizadas 2 preferencias",
    "updated_count": 2,
    "errors": []
}
```

---

## 🔒 **AUTENTICACIÓN Y PERMISOS**

### **Roles de Usuario:**
- **Employee (Empleado):** Puede ver sus propios datos, alertas y recomendaciones
- **Supervisor:** Puede gestionar empleados asignados, crear alertas/recomendaciones, ver analytics
- **Admin:** Acceso completo a todo el sistema

### **Headers Requeridos:**
```
Authorization: Bearer <token_jwt>
Content-Type: application/json
```

### **Códigos de Estado HTTP:**
- `200 OK` - Operación exitosa
- `201 Created` - Recurso creado exitosamente
- `400 Bad Request` - Error en los datos enviados
- `401 Unauthorized` - Token inválido o faltante
- `403 Forbidden` - Sin permisos para la operación
- `404 Not Found` - Recurso no encontrado
- `500 Internal Server Error` - Error del servidor

---

## 📚 **DOCUMENTACIÓN ADICIONAL**

### **Swagger/OpenAPI:**
- Documentación interactiva disponible en `/api/docs/`
- Schema disponible en `/api/schema/`

### **Filtros Comunes:**
La mayoría de endpoints LIST soportan filtros via query parameters:
- `days`: Filtrar por días hacia atrás
- `start_date` / `end_date`: Rango de fechas
- `is_active`: Filtrar por estado activo
- `type`: Filtrar por tipo de recurso
- `priority`: Filtrar por prioridad

### **Paginación:**
Los endpoints que retornan listas soportan paginación:
- `page`: Número de página
- `page_size`: Elementos por página (default: 20, max: 100)

### **Ordenamiento:**
Usar parámetro `ordering`:
- `ordering=created_at` - Ascendente
- `ordering=-created_at` - Descendente

---

**🎉 ¡Esta documentación cubre todos los 80+ endpoints implementados en el proyecto ZZZ Backend!**