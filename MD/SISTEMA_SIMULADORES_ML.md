# 🎮 Sistema de Gestión de Simuladores ESP32 con ML en Tiempo Real

## 📋 Descripción General

Sistema completo de gestión de simuladores ESP32 desde el panel de administrador con análisis de Machine Learning en tiempo real que genera alertas y recomendaciones automáticamente.

---

## ✨ Características Principales

### 1. **Gestión de Simuladores Múltiples**
- ✅ Iniciar múltiples simuladores simultáneamente
- ✅ Cada simulador independiente con su propio thread
- ✅ Asignar simuladores a empleados específicos
- ✅ Configurar perfiles de fatiga personalizados
- ✅ Configurar modos de actividad (reposo, ligero, moderado, intenso)

### 2. **Análisis ML en Tiempo Real**
- 🤖 Detección automática de anomalías cada 2 minutos
- 🤖 Generación de recomendaciones cada 10 minutos
- 🤖 Análisis basado en métricas procesadas
- 🤖 Alertas inteligentes según patrones detectados
- 🤖 Recomendaciones personalizadas por empleado

### 3. **Panel de Control Interactivo**
- 📊 Visualización en tiempo real de simuladores activos
- 📊 Estadísticas de fatiga, mensajes, actividad
- 📊 Auto-refresh cada 5 segundos
- 📊 Configuración dinámica de simuladores en ejecución
- 📊 Control individual o masivo de simuladores

### 4. **Integración con BD**
- 💾 Todos los datos se guardan en PostgreSQL
- 💾 Historial completo de sesiones
- 💾 Alertas y recomendaciones persistentes
- 💾 Métricas procesadas disponibles para análisis

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SimulatorsPage (Panel de Control Admin)               │   │
│  │  - Lista de empleados disponibles                      │   │
│  │  - Crear/Detener simuladores                           │   │
│  │  - Configurar parámetros en caliente                   │   │
│  │  - Visualización en tiempo real                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (Django)                           │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ SimulatorViewSet │  │ SimulatorManager │  │ ML Scheduler │ │
│  │  - API Endpoints │  │  - Control de    │  │  - Análisis  │ │
│  │  - Validaciones  │  │    Threads       │  │    cada 2min │ │
│  │  - Permisos      │  │  - Estado global │  │  - Alertas   │ │
│  └──────────────────┘  └──────────────────┘  │  - Recomen-  │ │
│                                               │    daciones  │ │
│  ┌──────────────────────────────────────┐   └──────────────┘ │
│  │   ESP32SimulatorThread (por sesión)  │                     │
│  │   - Publica MQTT cada 5s             │                     │
│  │   - Simula sensores realistas        │                     │
│  │   - Incrementa fatiga gradualmente   │                     │
│  └──────────────────────────────────────┘                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ MQTT
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MQTT Client + Processor                      │
│  - Recibe datos de sensores                                    │
│  - Guarda en SensorData                                        │
│  - Procesa métricas cada 2 minutos                             │
│  - Calcula índice de fatiga con ML                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                        │
│  - SimulatorSession (sesiones de simuladores)                  │
│  - SensorData (datos crudos)                                   │
│  - ProcessedMetrics (métricas calculadas)                      │
│  - FatigueAlert (alertas generadas)                            │
│  - RoutineRecommendation (recomendaciones ML)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Cómo Usar el Sistema

### **Paso 1: Iniciar el Backend**

```powershell
cd C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

**¿Qué inicia automáticamente?**
- ✅ Servidor Django en http://127.0.0.1:8000/
- ✅ Cliente MQTT (recibe datos de sensores)
- ✅ Procesador de métricas cada 2 minutos
- ✅ **ML Scheduler** (análisis automático cada 2 minutos)

**Mensajes esperados:**
```
✅ Conectado al broker MQTT
✅ Scheduler de procesamiento automático activado
✅ Analytics App: Servicios automáticos iniciados
✅ ML Scheduler iniciado
   📋 Detección de anomalías: cada 2 minutos
   📋 Generación de recomendaciones: cada 10 minutos
```

### **Paso 2: Iniciar el Frontend**

```powershell
cd C:\Users\bauti\Downloads\respaldos\ZZZ-Web\fatigue-frontend
npm run dev
```

Abre http://localhost:5173 en tu navegador.

### **Paso 3: Acceder al Panel de Simuladores**

1. **Login como Admin:**
   - Email: `admin@gmail.com` (o tu admin)
   - Password: tu contraseña

2. **Navegar al Panel de Simuladores:**
   - En el sidebar izquierdo, clic en **"🖥️ Simuladores"**
   - O directamente: http://localhost:5173/admin/simulators

### **Paso 4: Crear un Simulador**

1. **Clic en "➕ Nuevo Simulador"**

2. **Seleccionar Empleado:**
   - Elige un empleado de la lista
   - Solo aparecen empleados sin simulador activo

3. **Configurar Device ID:**
   - Se genera automáticamente (ej: `ESP32-012`)
   - Puedes modificarlo si lo deseas

4. **Elegir Perfil de Fatiga:**
   - **Descansado (0-30%):** Empleado bien descansado
   - **Normal (30-50%):** Estado normal
   - **Cansado (50-70%):** Algo fatigado
   - **Fatigado (70-85%):** Alta fatiga
   - **Crítico (85-100%):** Fatiga crítica

5. **Elegir Modo de Actividad:**
   - 😴 **Reposo:** Sin actividad física
   - 🚶 **Actividad Ligera:** Caminata, tareas leves
   - 🏃 **Actividad Moderada:** Trabajo moderado
   - 💪 **Actividad Intensa:** Trabajo pesado

6. **Clic en "▶️ Iniciar Simulador"**

### **Paso 5: Monitorear en Tiempo Real**

Una vez iniciado el simulador:

- 📊 **Card del Simulador** muestra:
  - Device ID y nombre del empleado
  - Fatiga actual en tiempo real
  - Perfil y modo de actividad
  - Mensajes MQTT enviados
  - Duración de la sesión

- 🔄 **Auto-refresh ON:** Actualiza datos cada 5 segundos

- ⚙️ **Configurar:** Cambiar actividad o nivel de fatiga en caliente

- 🛑 **Detener:** Finalizar el simulador

### **Paso 6: Múltiples Simuladores**

Puedes iniciar **varios simuladores simultáneamente**:

1. Clic en "➕ Nuevo Simulador"
2. Seleccionar otro empleado
3. Configurar con diferentes perfiles
4. Todos correrán en paralelo

**Ejemplo de Prueba:**
- Empleado A: Perfil "Descansado" + Actividad "Ligera"
- Empleado B: Perfil "Fatigado" + Actividad "Intensa"
- Empleado C: Perfil "Crítico" + Actividad "Moderada"

### **Paso 7: Observar Análisis ML**

**Cada 2 minutos**, el sistema automáticamente:

1. **Analiza métricas procesadas**
2. **Detecta anomalías:**
   - Fatiga alta/crítica
   - SpO2 bajo
   - Frecuencia cardíaca elevada
   - Desaturaciones múltiples

3. **Genera alertas** si detecta problemas:
   ```
   🔍 Ejecutando análisis de anomalías ML...
      ⚠️  3 alerta(s) generada(s)
   ```

4. **Cada 10 minutos genera recomendaciones:**
   ```
   💡 Ejecutando generación de recomendaciones ML...
      ✅ 2 recomendación(es) generada(s)
         - Descansos: 1
         - Redistribuciones: 1
   ```

### **Paso 8: Revisar Alertas y Recomendaciones**

Las alertas y recomendaciones generadas se pueden ver en:

- **Panel de Alertas:** `/admin/alerts` o `/supervisor/alerts`
- **Panel de Recomendaciones:** Según rol del usuario
- **Base de Datos:** Tablas `fatigue_alerts` y `routine_recommendations`

---

## 🎯 Perfiles de Fatiga Explicados

| Perfil | Rango | Comportamiento Simulado |
|--------|-------|-------------------------|
| **Descansado** | 0-30% | HR normal, SpO2 alto (98-99%), poca variabilidad |
| **Normal** | 30-50% | HR ligeramente elevado, SpO2 normal (96-98%) |
| **Cansado** | 50-70% | HR moderado, SpO2 desciende levemente (95-97%) |
| **Fatigado** | 70-85% | HR alto, SpO2 bajo (93-95%), más desaturaciones |
| **Crítico** | 85-100% | HR muy alto, SpO2 crítico (<93%), alertas múltiples |

---

## 🧪 Comando de Prueba Rápida

Ejecuta una prueba automática completa del sistema:

```powershell
python manage.py test_simulators --duration 60
```

**¿Qué hace?**
1. ✅ Verifica empleados disponibles
2. ✅ Crea 2 sesiones de simuladores
3. ✅ Inicia los simuladores
4. ✅ Monitorea durante 60 segundos
5. ✅ Muestra estadísticas cada 10 segundos
6. ✅ Detiene los simuladores
7. ✅ Muestra resumen final con alertas y recomendaciones

**Salida esperada:**
```
======================================================================
🚀 PRUEBA DEL SISTEMA COMPLETO DE SIMULADORES
======================================================================

📋 1. Verificando empleados...
   ✅ 9 empleados disponibles

🖥️  2. Creando sesiones de simuladores...
   ✅ Sesión creada: ESP32-TEST-001 para Alberto Plascencia
   ✅ Sesión creada: ESP32-TEST-002 para Brian Bautista

▶️  3. Iniciando simuladores...
   ✅ Simulador iniciado: ESP32-TEST-001
   ✅ Simulador iniciado: ESP32-TEST-002

🤖 4. Verificando ML Scheduler...
   ✅ ML Scheduler está activo

⏱️  5. Monitoreando durante 60 segundos...
   
   📊 Estadísticas actuales:
      - ESP32-TEST-001: Fatiga=25.3%, Mensajes=12, Actividad=light
      - ESP32-TEST-002: Fatiga=42.7%, Mensajes=12, Actividad=moderate
      ⚠️  1 alerta(s) nueva(s) generada(s)

🛑 6. Deteniendo simuladores...
   ✅ ESP32-TEST-001 detenido: 120 mensajes enviados
   ✅ ESP32-TEST-002 detenido: 120 mensajes enviados

======================================================================
📊 RESUMEN FINAL
======================================================================

⚠️  Total de alertas generadas: 1
💡 Total de recomendaciones generadas: 0

======================================================================
✅ PRUEBA COMPLETADA
======================================================================
```

---

## 📊 Endpoints de API

### **Listar Sesiones**
```http
GET /api/simulators/
```

### **Sesiones Activas**
```http
GET /api/simulators/active/
```

### **Crear Simulador**
```http
POST /api/simulators/
Content-Type: application/json

{
  "employee": 12,
  "device_id": "ESP32-012",
  "fatigue_profile": "tired",
  "activity_mode": "moderate"
}
```

### **Detener Simulador**
```http
POST /api/simulators/{id}/stop/
```

### **Actualizar Configuración**
```http
POST /api/simulators/{id}/update_config/
Content-Type: application/json

{
  "activity_mode": "heavy",
  "fatigue_level": 75.0
}
```

### **Empleados Disponibles**
```http
GET /api/simulators/available_employees/
```

### **Estadísticas**
```http
GET /api/simulators/stats/
```

### **Detener Todos**
```http
POST /api/simulators/stop_all/
```

---

## 🔧 Configuración Avanzada

### **Intervalos de Análisis ML**

Edita `apps/analytics/ml_scheduler.py`:

```python
ml_scheduler.start(
    alert_interval_minutes=2,        # Alertas cada 2 min
    recommendation_interval_minutes=10  # Recomendaciones cada 10 min
)
```

### **Umbrales de Detección**

Edita `apps/analytics/anomaly_detector.py`:

```python
FATIGUE_CRITICAL = 85  # Fatiga crítica
FATIGUE_HIGH = 70      # Fatiga alta
SPO2_CRITICAL = 88     # SpO2 crítico
HR_VERY_HIGH = 160     # HR muy alta
```

---

## ✅ Checklist de Funcionamiento

### Backend
- ✅ PostgreSQL corriendo
- ✅ Mosquitto MQTT corriendo
- ✅ `python manage.py runserver` ejecutándose
- ✅ Ver mensaje "ML Scheduler iniciado"
- ✅ Ver mensaje "Scheduler de procesamiento automático activado"

### Frontend
- ✅ `npm run dev` ejecutándose
- ✅ Login exitoso como admin
- ✅ Navegar a `/admin/simulators`
- ✅ Ver lista de empleados disponibles

### Simuladores
- ✅ Crear simulador exitosamente
- ✅ Ver card de simulador con datos
- ✅ Fatiga incrementándose con el tiempo
- ✅ Mensajes MQTT incrementándose
- ✅ Auto-refresh actualizando datos

### Análisis ML
- ✅ Ver en logs del backend: "Ejecutando análisis de anomalías ML"
- ✅ Ver alertas generadas en BD o panel
- ✅ Ver recomendaciones generadas
- ✅ Datos guardados en ProcessedMetrics

---

## 🎉 ¡Todo Listo!

El sistema está completamente funcional con:

✅ **Múltiples simuladores concurrentes**  
✅ **Análisis ML en tiempo real**  
✅ **Alertas automáticas inteligentes**  
✅ **Recomendaciones personalizadas**  
✅ **Panel de control interactivo**  
✅ **Persistencia en BD**  
✅ **Auto-refresh en frontend**  
✅ **Configuración dinámica**  

**¡Disfruta del sistema!** 🚀
