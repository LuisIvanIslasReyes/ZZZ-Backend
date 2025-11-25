# 🤖 Sistema de Procesamiento Automático de Métricas

## 📖 Descripción

El sistema de procesamiento automático elimina la necesidad de ejecutar manualmente `python manage.py process_metrics`. Ahora los datos de los sensores se procesan automáticamente cada 2 minutos en segundo plano.

---

## ⚙️ Cómo Funciona

### 1. **Recepción de Datos (MQTT)**
Los dispositivos ESP32 envían datos cada 5 segundos al broker MQTT:
```json
{
  "device_id": "ESP32-001",
  "timestamp": "2025-11-20T14:30:00Z",
  "heart_rate": 75.5,
  "spo2": 98.2,
  "accel": {"x": 0.12, "y": -0.05, "z": 9.81}
}
```

Estos datos se guardan automáticamente en la tabla `SensorData`.

### 2. **Procesamiento Automático (Scheduler)**
Cada **2 minutos**, el scheduler ejecuta automáticamente:
- Lee los datos crudos de `SensorData`
- Los agrupa en ventanas de 1 minuto
- Calcula métricas avanzadas (HRV, variabilidad SpO2, nivel de actividad)
- Calcula el índice de fatiga
- Guarda todo en `ProcessedMetrics`

### 3. **Visualización en Tiempo Real**
Las gráficas del frontend consultan `ProcessedMetrics` y se actualizan automáticamente.

---

## 🚀 Inicio Automático

### Opción 1: Con el servidor Django (Recomendado)

El procesador se inicia automáticamente al ejecutar:
```powershell
python manage.py runserver
```

Verás estos mensajes:
```
✅ Scheduler de procesamiento automático activado
📋 Job programado: Procesar métricas cada 2 minutos
🔄 Iniciando procesamiento automático de métricas...
```

### Opción 2: Modo Standalone (Opcional)

Si quieres ejecutar SOLO el procesador sin el servidor Django:
```powershell
python manage.py start_auto_processor
```

Para cambiar el intervalo:
```powershell
python manage.py start_auto_processor --interval 5  # Cada 5 minutos
```

---

## 📊 Monitoreo del Procesamiento

### Ver logs en tiempo real:
Los logs muestran el progreso del procesamiento:
```
🔄 Iniciando procesamiento automático de métricas...
  ✅ ESP32-001: 3 ventanas procesadas
  ✅ ESP32-01: 5 ventanas procesadas
✅ Procesamiento automático completado: 8 ventanas totales
```

### Verificar métricas procesadas:
```powershell
python manage.py shell
```

```python
from apps.sensors.models import ProcessedMetrics

# Ver últimas métricas procesadas
metrics = ProcessedMetrics.objects.all().order_by('-window_start')[:10]
for m in metrics:
    print(f"{m.window_start} - {m.employee.email} - Fatiga: {m.fatigue_index}%")
```

---

## ⚙️ Configuración

### Cambiar intervalo de procesamiento:

Edita `apps/sensors/scheduler.py`:
```python
# Cambiar de 2 a 5 minutos
scheduler.add_job(
    process_metrics_job,
    trigger=IntervalTrigger(minutes=5),  # ← Cambiar aquí
    ...
)
```

### Cambiar tamaño de ventana:

Edita `apps/sensors/scheduler.py`:
```python
def process_metrics_job():
    processor = MetricsProcessor(window_minutes=5)  # ← Cambiar de 1 a 5 minutos
    ...
```

---

## 🔧 Comandos Útiles

### Procesar manualmente (una vez):
```powershell
python manage.py process_metrics
```

### Generar datos de prueba:
```powershell
python manage.py generate_test_data --days=7
```

### Ver estado del scheduler:
```powershell
python manage.py shell
```
```python
from django_apscheduler.models import DjangoJob, DjangoJobExecution

# Ver jobs activos
jobs = DjangoJob.objects.all()
for job in jobs:
    print(f"{job.name} - Siguiente ejecución: {job.next_run_time}")

# Ver últimas ejecuciones
executions = DjangoJobExecution.objects.all().order_by('-run_time')[:5]
for exe in executions:
    print(f"{exe.job.name} - {exe.run_time} - Status: {exe.status}")
```

---

## 🛠️ Troubleshooting

### El procesador no arranca automáticamente

**Verificar que django-apscheduler está instalado:**
```powershell
pip install django-apscheduler
python manage.py migrate
```

**Verificar logs:**
```powershell
# Buscar mensajes de error al iniciar
python manage.py runserver --verbosity=2
```

### No se procesan datos nuevos

**Verificar que hay datos en SensorData:**
```powershell
python manage.py shell
```
```python
from apps.sensors.models import SensorData
print(f"Datos disponibles: {SensorData.objects.count()}")
print(f"Últimos 5 registros:")
for s in SensorData.objects.all().order_by('-timestamp')[:5]:
    print(f"  {s.timestamp} - {s.device.device_identifier}")
```

**Verificar que el simulador está enviando datos:**
```
📤 [ESP32-001] Publicando...  ← Debe aparecer cada 5 segundos
```

### El procesador se ejecuta pero no genera métricas

**Revisar ventana de tiempo:**
El procesador solo procesa datos **no procesados anteriormente**. Si ya procesaste todo manualmente, tendrás que esperar a que lleguen datos nuevos o generar datos de prueba.

---

## 📈 Flujo Completo del Sistema

```
┌─────────────┐
│   ESP32     │ → Envía datos cada 5s vía MQTT
└──────┬──────┘
       ↓
┌─────────────┐
│   Broker    │ → Recibe y distribuye mensajes
│   MQTT      │
└──────┬──────┘
       ↓
┌─────────────┐
│  Django     │ → Guarda en SensorData
│  Backend    │
└──────┬──────┘
       ↓
┌─────────────┐
│ Scheduler   │ → Cada 2 minutos procesa datos
│ (Auto)      │
└──────┬──────┘
       ↓
┌─────────────┐
│ Processed   │ → Métricas listas para gráficas
│ Metrics     │
└──────┬──────┘
       ↓
┌─────────────┐
│  Frontend   │ → Muestra gráficas en tiempo real
│  (React)    │
└─────────────┘
```

---

## 🎯 Ventajas del Sistema Automático

✅ **No necesitas ejecutar comandos manualmente**  
✅ **Procesamiento continuo en background**  
✅ **Datos siempre actualizados para las gráficas**  
✅ **Se adapta automáticamente a nuevos dispositivos**  
✅ **Robusto ante errores (continúa procesando otros dispositivos)**  
✅ **Limpieza automática de logs antiguos**  

---

## 📝 Notas Importantes

- El scheduler se ejecuta **solo en el servidor Django** (`runserver` o `gunicorn`)
- **NO se ejecuta** en comandos de gestión como `migrate`, `makemigrations`, etc.
- El procesamiento es **incremental**: solo procesa datos nuevos
- Las métricas se procesan en **ventanas de 1 minuto** por defecto
- El índice de fatiga se calcula usando el modelo ML (o fórmula placeholder si no existe)
