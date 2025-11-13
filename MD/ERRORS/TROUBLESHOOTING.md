# 🔧 Guía Rápida: Solución de Problemas Comunes

## ✅ Servidor funcionando correctamente

El error de MQTT que ves **NO ES CRÍTICO**. El servidor Django está funcionando bien en:
- **URL**: http://127.0.0.1:8000/
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **Admin**: http://127.0.0.1:8000/admin/

---

## 📡 Error MQTT: "No se puede establecer una conexión"

### ¿Por qué ocurre?

El servidor Django intenta conectarse al broker MQTT en `localhost:1883`, pero **no está instalado/ejecutándose**.

### ⚠️ ¿Es necesario arreglarlo ahora?

**NO**, solo necesitas MQTT si:
- Vas a usar el simulador ESP32 (`esp32_simulator.py`)
- Tienes dispositivos ESP32 reales enviando datos

### 🔧 Soluciones (elige una)

#### Opción 1: Instalar Mosquitto en Windows (RECOMENDADO)

```powershell
# 1. Descargar Mosquitto
# Ir a: https://mosquitto.org/download/
# Descargar: mosquitto-X.X.X-install-windows-x64.exe

# 2. Instalar (Next, Next, Install)

# 3. Iniciar servicio
net start mosquitto

# 4. Verificar
mosquitto_sub -h localhost -t test
```

#### Opción 2: Usar Docker (MÁS FÁCIL)

```powershell
# Iniciar solo MQTT
docker-compose up -d mqtt

# Verificar
docker-compose ps
```

#### Opción 3: Desactivar MQTT temporalmente

Edita `apps/mqtt_client/apps.py`:

```python
def ready(self):
    # Comentar estas líneas para desactivar MQTT
    # if not settings.DEBUG:
    #     self.start_mqtt_client()
    pass  # Desactivado temporalmente
```

---

## 🐛 Error corregido: Swagger Schema

Se corrigió el error de campos en `FatigueAlert`:
- ❌ `resolved` → ✅ `is_resolved`
- ❌ `device` → ✅ (campo eliminado, no existe en el modelo)
- ❌ `fatigue_level` → ✅ `fatigue_index`

**Reinicia el servidor:**

```powershell
# Ctrl+C para detener
# Luego:
py manage.py runserver
```

---

## 🚀 Uso sin MQTT

Puedes usar el sistema completamente sin MQTT:

### 1. Crear datos de prueba manualmente

```python
# En Django shell
py manage.py shell

from apps.users.models import CustomUser
from apps.sensors.models import ProcessedMetrics
from datetime import datetime, timedelta

# Crear empleado
employee = CustomUser.objects.create_user(
    username='empleado1',
    email='empleado@test.com',
    password='test123',
    role='employee'
)

# Crear métricas procesadas
for i in range(50):
    ProcessedMetrics.objects.create(
        user=employee,
        timestamp=datetime.now() - timedelta(hours=i),
        heart_rate=75.0 + i,
        spo2=95.0,
        temperature=36.8,
        steps=1000,
        calories=200.0,
        distance=2.0,
        activity_level='moderate',
        fatigue_index=50.0 + i,
        stress_level=40.0,
        recovery_score=60.0
    )
```

### 2. Usar script de prueba

```powershell
py setup_mqtt_test_data.py
```

### 3. Usar API directamente

```powershell
# Crear métricas vía API
curl -X POST http://localhost:8000/api/processed-metrics/ ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -d "{\"heart_rate\": 80, \"fatigue_index\": 65}"
```

---

## ✅ Verificación del Sistema

### 1. Servidor funcionando

```
✅ Django version 4.2.7, using settings 'config.settings'
✅ Starting development server at http://127.0.0.1:8000/
```

### 2. Acceder a Swagger

Abre en el navegador:
```
http://127.0.0.1:8000/api/docs/
```

### 3. Probar endpoints

```powershell
# Sin autenticación (público)
curl http://localhost:8000/api/docs/

# Login
curl -X POST http://localhost:8000/api/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

---

## 📊 Estado Actual

| Componente | Estado |
|------------|--------|
| Django Server | ✅ Funcionando |
| PostgreSQL | ✅ Conectado |
| API REST | ✅ Funcionando |
| Swagger UI | ✅ Funcionando |
| MQTT Broker | ⚠️ No instalado (opcional) |

---

## 🔍 Comandos Útiles

```powershell
# Ver logs del servidor
py manage.py runserver --verbosity 2

# Crear superusuario
py manage.py createsuperuser

# Verificar migraciones
py manage.py showmigrations

# Acceder a shell
py manage.py shell

# Ejecutar tests
pytest apps/analytics/tests.py -v
```

---

## 📚 Próximos Pasos

1. ✅ **Servidor funcionando** - Ya está listo
2. 🔧 **Crear superusuario** - `py manage.py createsuperuser`
3. 🌐 **Acceder a Swagger** - http://localhost:8000/api/docs/
4. 📊 **Probar endpoints** - Desde Swagger UI
5. 📡 **Instalar MQTT** (opcional) - Solo si vas a usar ESP32

---

**Última actualización:** 11 de Noviembre, 2025
