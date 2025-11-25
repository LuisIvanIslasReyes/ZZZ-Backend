# 🤖 RESUMEN EJECUTIVO - SISTEMA DE RECOMENDACIONES ML

## ✅ ESTADO ACTUAL

**El sistema de recomendaciones con Machine Learning YA EXISTE y está COMPLETAMENTE FUNCIONAL.**

### Archivos Clave:
- ✅ `apps/analytics/ml_service.py` - Servicio de ML para predicción de fatiga
- ✅ `apps/analytics/recommendation_service.py` - Generador de recomendaciones inteligentes
- ✅ `apps/analytics/models.py` - Modelo RoutineRecommendation
- ✅ `apps/analytics/views.py` - API REST completa
- ✅ `apps/analytics/management/commands/generate_recommendations.py` - Comando Django

### Componentes Corregidos:
- ✅ Corregido bug en recommendation_service.py (campo `rejected` → `is_applied`)
- ✅ Actualizado comando generate_recommendations.py

---

## 🎯 CÓMO FUNCIONA

### 1. **Recolección de Datos**
```
ESP32 → MQTT → SensorData (cada 5 segundos)
```

### 2. **Procesamiento Automático**
```python
# Cada 2 minutos (automático con runserver)
SensorData → MetricsProcessor → ML Service → ProcessedMetrics
                                   ↓
                         Calcula fatigue_index (0-100)
```

### 3. **Análisis de Patrones**
```python
# Manual o programado
python manage.py generate_recommendations --all

RecommendationService:
  - Analiza últimos 7 días de métricas
  - Detecta empleados con fatiga alta
  - Identifica desbalances en equipos
  - Encuentra patrones horarios/semanales
  ↓
  Genera 3 tipos de recomendaciones:
  • Descansos preventivos
  • Redistribución de tareas
  • Rotación de turnos
```

### 4. **Consumo en Frontend**
```javascript
// API REST disponible
GET /api/recommendations/                  // Listar
GET /api/recommendations/?type=break       // Filtrar
POST /api/recommendations/{id}/apply/      // Aplicar
GET /api/recommendations/stats/            // Estadísticas
```

---

## 🔧 MODELO DE MACHINE LEARNING

### Tipo: **K-Means Clustering**

**Estado:** Modelo opcional (sistema funciona sin él usando heurísticas)

**Si existe el modelo entrenado:**
- Usa clustering para clasificar niveles de fatiga
- 15-20 features (HR, HRV, SpO2, actividad)
- Predice fatigue_index con mayor precisión

**Si NO existe:**
- Usa cálculo heurístico ponderado:
  - HR/Actividad ratio (40%)
  - SpO2 (30%)
  - HRV (20%)
  - Desaturaciones (10%)

**Para entrenar el modelo:**
```bash
python SCRIPTS/train_ml_model.py
# O paso por paso:
python notebooks/01_data_exploration.py
python notebooks/02_feature_engineering.py
python notebooks/03_clustering_model.py
```

---

## 📊 TIPOS DE RECOMENDACIONES

### 1. ☕ Descansos Preventivos (`break`)
**Se genera cuando:**
- Fatiga promedio ≥ 50 en últimos 7 días
- Más de 5 episodios de fatiga alta (>70)
- Pico de fatiga ≥ 85

**Incluye:**
- Horarios sugeridos para descansos
- Estadísticas de fatiga
- Frecuencia recomendada

### 2. ⚖️ Redistribución de Tareas (`task_redistribution`)
**Se genera cuando:**
- Diferencia >20 puntos entre empleados
- Desbalance significativo en el equipo

**Incluye:**
- Lista de empleados sobrecargados
- Lista de empleados con menor carga
- Sugerencias de redistribución

### 3. 🔄 Rotación de Turnos (`shift_rotation`)
**Se genera cuando:**
- Fatiga alta en horarios específicos
- Patrones cronológicos consistentes
- Fatiga elevada en ciertos días

**Incluye:**
- Horarios problemáticos
- Horarios con mejor desempeño
- Días con mejor/peor rendimiento

---

## 🚀 GUÍA DE USO RÁPIDA

### Paso 1: Verificar el Sistema
```bash
cd c:\Users\bauti\Downloads\respaldos\ZZZ-Backend
python SCRIPTS\setup_ml_recommendations.py
```

### Paso 2: Generar Datos (si es necesario)
```bash
# Opción A: Simulador ESP32
python SCRIPTS\esp32_simulator.py

# Opción B: Datos sintéticos
python manage.py generate_monthly_data --days 7
```

### Paso 3: Procesar Métricas
```bash
# Automático (se ejecuta cada 2 minutos)
python manage.py runserver

# O manual
python manage.py process_metrics
```

### Paso 4: Generar Recomendaciones
```bash
# Para todos los supervisores
python manage.py generate_recommendations --all

# Para un supervisor específico
python manage.py generate_recommendations --supervisor-id 5
```

### Paso 5: Consumir en Frontend
```javascript
// React/TypeScript
import { recommendationService } from '@/services';

// Listar recomendaciones
const recommendations = await recommendationService.getAll();

// Filtrar por tipo
const breakRecs = await recommendationService.getAll({ type: 'break' });

// Aplicar recomendación
await recommendationService.apply(recommendationId);
```

---

## 🧪 PROBAR EL SISTEMA

```bash
# Prueba end-to-end completa
python SCRIPTS\test_recommendation_system.py

# Este script:
# 1. Verifica usuarios
# 2. Genera datos de prueba
# 3. Procesa métricas
# 4. Verifica ML
# 5. Genera recomendaciones
# 6. Muestra ejemplos
```

---

## 📚 DOCUMENTACIÓN

### Archivo Principal:
**`MD/SISTEMA_RECOMENDACIONES_ML.md`** - Documentación completa con:
- Arquitectura detallada
- Explicación del modelo ML
- Flujo completo del sistema
- Ejemplos de código
- Casos de uso
- Guías de integración

### Otros Archivos:
- `MD/PROJECT_CONTEXT.md` - Contexto general del proyecto
- `MD/PROCESAMIENTO_AUTOMATICO.md` - Procesamiento de métricas
- `MD/ANALISIS_ESTADO_SISTEMA.md` - Estado completo del backend
- `notebooks/README.md` - Guías de notebooks ML

---

## 🎓 EXPLICACIÓN TÉCNICA

### Algoritmo de Recomendaciones

```python
Para cada supervisor:
    empleados = obtener_empleados(supervisor)
    
    Para cada empleado:
        # 1. Obtener datos históricos
        metricas = ProcessedMetrics.filter(
            employee=empleado,
            window_start__gte=hace_7_dias
        )
        
        # 2. Calcular estadísticas
        fatiga_promedio = metricas.avg('fatigue_index')
        fatiga_maxima = metricas.max('fatigue_index')
        episodios_altos = metricas.filter(fatigue_index__gte=70).count()
        
        # 3. Detectar patrones
        if fatiga_promedio >= 50:
            generar_recomendacion_descanso()
        
        if episodios_altos > 5:
            generar_recomendacion_descanso(prioridad=alta)
        
        # 4. Analizar horarios
        horarios_pico = analizar_fatiga_por_hora()
        if horarios_pico:
            generar_recomendacion_rotacion()
    
    # 5. Analizar equipo completo
    desbalance = calcular_desbalance_equipo(empleados)
    if desbalance > 20:
        generar_recomendacion_redistribucion()
```

### Priorización

```python
Prioridad 5 (MÁS URGENTE):
    - Fatiga promedio > 70
    - Desbalance de equipo > 30 puntos
    
Prioridad 4:
    - Fatiga máxima > 85
    - Episodios frecuentes de fatiga alta
    
Prioridad 3:
    - Fatiga promedio 50-70
    - Patrones detectados
    
Prioridad 2-1:
    - Recomendaciones preventivas
```

---

## 🔌 ENDPOINTS DE LA API

### Recomendaciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/recommendations/` | Listar todas |
| GET | `/api/recommendations/?type=break` | Filtrar por tipo |
| GET | `/api/recommendations/?priority=5` | Filtrar por prioridad |
| GET | `/api/recommendations/{id}/` | Ver detalle |
| POST | `/api/recommendations/{id}/apply/` | Aplicar recomendación |
| GET | `/api/recommendations/stats/` | Estadísticas |

### Filtros Disponibles

```javascript
// Por tipo
?type=break
?type=task_redistribution
?type=shift_rotation

// Por prioridad
?priority=5
?priority__gte=4  // Prioridad alta (4-5)

// Por estado
?is_applied=false  // Pendientes
?is_applied=true   // Aplicadas

// Por supervisor
?supervisor__id=5

// Por empleado
?employee__id=10

// Combinados
?type=break&priority__gte=4&is_applied=false
```

---

## 💡 CASOS DE USO REALES

### Caso 1: Empleado Individual con Fatiga Alta
```
Juan Pérez:
- Fatiga promedio: 68/100 (últimos 7 días)
- 9 episodios con fatiga > 70
- Picos a las 14:00, 15:00, 16:00

→ Recomendación: Descansos de 15 min en esos horarios
→ Prioridad: 4
```

### Caso 2: Desbalance de Equipo
```
Equipo de María (Supervisora):
- Juan: 75/100 fatiga promedio
- Pedro: 72/100
- Carlos: 40/100
- Ana: 35/100

→ Recomendación: Redistribuir tareas de Juan/Pedro a Carlos/Ana
→ Prioridad: 5 (urgente)
```

### Caso 3: Patrón Cronológico
```
María López:
- Lunes: 78/100
- Martes: 75/100
- Miércoles: 70/100
- Jueves: 45/100
- Viernes: 42/100

→ Recomendación: Rotación de días o carga reducida al inicio de semana
→ Prioridad: 4
```

---

## ✅ CONCLUSIÓN

**El sistema de recomendaciones con ML está COMPLETO y FUNCIONAL.**

### Lo que EXISTE:
✅ Servicio de ML para predicción de fatiga  
✅ Generador automático de 3 tipos de recomendaciones  
✅ API REST completa con filtros  
✅ Comandos Django para operación  
✅ Documentación exhaustiva  
✅ Scripts de prueba y configuración  

### Lo que FALTA (opcional):
⚠️ Modelo ML entrenado (usa heurísticas mientras tanto)  
⚠️ Programación automática de generación de recomendaciones  
⚠️ Integración completa en el frontend  

### Próximos Pasos:
1. **Entrenar modelo ML** (opcional): `python SCRIPTS/train_ml_model.py`
2. **Programar generación automática** de recomendaciones (cronjob/celery)
3. **Integrar en frontend** React usando los endpoints

### Para Empezar:
```bash
# 1. Verificar sistema
python SCRIPTS\setup_ml_recommendations.py

# 2. Probar funcionamiento
python SCRIPTS\test_recommendation_system.py

# 3. Leer documentación
# Ver: MD/SISTEMA_RECOMENDACIONES_ML.md
```

---

**Fecha:** 24 de noviembre de 2025  
**Estado:** ✅ Sistema Completo y Funcional
