# 🧪 GUÍA DE PRUEBA DE MQTT - Fase 4

## 📋 REQUISITOS PREVIOS

1. **Mosquitto Broker MQTT** instalado y corriendo
2. **PostgreSQL** configurado y corriendo
3. **Django servidor** corriendo
4. **Terminal adicional** para el simulador ESP32

---

## 🚀 PASO 1: Instalar Mosquitto

### Windows:
1. Descargar de: https://mosquitto.org/download/
2. Instalar el .exe
3. Abrir terminal **como Administrador**:
   ```powershell
   net start mosquitto
   ```

### Verificar instalación:
```powershell
mosquitto -h
```

---

## 🔧 PASO 2: Configurar el Sistema

### 1. Crear un dispositivo y empleado de prueba

Ejecuta este script de Python:

```python
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.users.models import CustomUser
from apps.devices.models import Device

# Crear supervisor
supervisor = CustomUser.objects.filter(email='supervisor@test.com').first()
if not supervisor:
    supervisor = CustomUser.objects.create_user(
        email='supervisor@test.com',
        password='test123',
        first_name='Test',
        last_name='Supervisor',
        role='supervisor',
        admin_id=CustomUser.objects.filter(role='admin').first()
    )
    print('✅ Supervisor creado')

# Crear empleado
employee = CustomUser.objects.filter(email='employee@test.com').first()
if not employee:
    employee = CustomUser.objects.create_user(
        email='employee@test.com',
        password='test123',
        first_name='Test',
        last_name='Employee',
        role='employee',
        supervisor=supervisor
    )
    print('✅ Empleado creado')

# Crear dispositivo
device = Device.objects.filter(device_identifier='ESP32-001').first()
if not device:
    device = Device.objects.create(
        device_identifier='ESP32-001',
        employee=employee,
        supervisor=supervisor,
        is_active=True
    )
    print('✅ Dispositivo ESP32-001 creado')
else:
    print('⚠️  Dispositivo ESP32-001 ya existe')
"
```

---

## 🔥 PASO 3: Iniciar Componentes

### Terminal 1: Mosquitto Broker
```powershell
# Si no está como servicio, iniciar manualmente:
mosquitto -v
```

### Terminal 2: Django Server
```powershell
cd C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

El cliente MQTT se iniciará automáticamente y verás:
```
🚀 Iniciando cliente MQTT desde AppConfig...
✅ Conectado al broker MQTT
📡 Suscrito a topic: devices/+/sensors
```

### Terminal 3: ESP32 Simulator
```powershell
cd C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
.\venv\Scripts\Activate.ps1
python esp32_simulator.py
```

Cuando te pregunte:
- **Device ID:** `ESP32-001`
- **Broker:** `localhost` (Enter)
- **Puerto:** `1883` (Enter)

---

## 📊 PASO 4: Verificar Flujo de Datos

### Verificar en la base de datos:

```python
python manage.py shell

# En el shell:
from apps.sensors.models import SensorData, ProcessedMetrics
from apps.devices.models import Device

# Ver últimos datos de sensores
print(SensorData.objects.all().count())
print(SensorData.objects.last())

# Ver dispositivo
device = Device.objects.get(device_identifier='ESP32-001')
print(f"Última conexión: {device.last_connection}")

# Ver métricas procesadas
print(ProcessedMetrics.objects.all().count())
print(ProcessedMetrics.objects.last())
```

### Procesar métricas manualmente:

```python
python manage.py shell

# En el shell:
from apps.sensors.processors import metrics_processor

# Procesar ventanas de los últimos minutos
result = metrics_processor.process_latest_windows()
print(f"Procesadas {result} ventanas")
```

---

## 🔄 PASO 5: Procesamiento Automático

Para procesar métricas automáticamente cada minuto, puedes:

### Opción 1: Comando de management
```python
python manage.py shell

from apps.sensors.processors import metrics_processor
import time

while True:
    metrics_processor.process_latest_windows()
    time.sleep(60)  # Cada 60 segundos
```

### Opción 2: Celery (para producción)
```python
# Instalar: pip install celery redis
# Crear task en apps/sensors/tasks.py
# Configurar beat schedule
```

---

## 📈 PASO 6: Visualizar en Admin Panel

1. Abrir http://localhost:8000/admin/
2. Login con: `admin@example.com` / `admin123`
3. Ver secciones:
   - **Dispositivos** → Ver ESP32-001 y última conexión
   - **Datos de Sensores** → Ver stream en tiempo real
   - **Métricas Procesadas** → Ver fatigue_index calculado

---

## 🧪 PRUEBAS ESPERADAS

### ✅ Flujo correcto:

1. **ESP32 Simulator** publica cada 5 segundos:
   ```
   📤 [ESP32-001] HR:75.2 BPM | SpO2:98.1% | Fatiga:12.3 | Actividad:light
   ```

2. **Django MQTT Client** recibe y guarda:
   ```
   ✅ Datos guardados: ESP32-001 - HR: 75.2 BPM, SpO2: 98.1%
   ```

3. **Procesador** calcula métricas (cada 1 min):
   ```
   ✅ Métricas procesadas: ESP32-001 | Fatiga: 15.5 | HR: 76.3 | SpO2: 98.0
   ```

4. **Base de datos** contiene:
   - 12 registros SensorData por minuto (5s cada uno)
   - 1 registro ProcessedMetrics por minuto
   - Device.last_connection actualizado

---

## 🐛 TROUBLESHOOTING

### Error: "Dispositivo no encontrado"
```python
# Verificar que existe:
python manage.py shell
from apps.devices.models import Device
print(Device.objects.all())

# Crear manualmente si no existe (ver PASO 2)
```

### Error: "No se puede conectar al broker MQTT"
```powershell
# Verificar que Mosquitto está corriendo:
netstat -ano | findstr :1883

# Iniciar Mosquitto:
net start mosquitto
# o
mosquitto -v
```

### No llegan datos a Django
```python
# Verificar cliente MQTT en Django:
python manage.py shell
from apps.mqtt_client.client import mqtt_client
print(f"Conectado: {mqtt_client.connected}")

# Reiniciar servidor si es necesario
```

---

## 📝 COMANDOS ÚTILES

### Ver logs en tiempo real:
```python
# En manage.py, configurar logging a nivel DEBUG en settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'apps.mqtt_client': {'handlers': ['console'], 'level': 'DEBUG'},
        'apps.sensors': {'handlers': ['console'], 'level': 'DEBUG'},
    },
}
```

### Limpiar datos de prueba:
```python
python manage.py shell

from apps.sensors.models import SensorData, ProcessedMetrics
SensorData.objects.all().delete()
ProcessedMetrics.objects.all().delete()
```

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [ ] Mosquitto broker corriendo en puerto 1883
- [ ] Django server corriendo en puerto 8000
- [ ] Cliente MQTT de Django conectado
- [ ] Dispositivo ESP32-001 existe en BD
- [ ] Empleado asignado al dispositivo
- [ ] ESP32 Simulator publicando datos
- [ ] SensorData incrementando en BD
- [ ] ProcessedMetrics generándose cada minuto
- [ ] Fatigue_index calculándose correctamente
- [ ] Last_connection del device actualizándose

---

**🎯 Si todo funciona, verás datos fluyendo en tiempo real desde el simulador hasta la base de datos.**
