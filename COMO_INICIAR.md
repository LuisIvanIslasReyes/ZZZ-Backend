# 🚀 GUÍA RÁPIDA DE INICIO - Sistema de Detección de Fatiga

## 📋 REQUISITOS PREVIOS

Antes de iniciar, asegúrate de tener instalado:

- ✅ **Python 3.11+** - Instalado
- ✅ **Node.js 18+** - Para el frontend
- ✅ **PostgreSQL** - Base de datos
- ✅ **Mosquitto MQTT Broker** - Instalado como servicio de Windows

---

## 🔧 SERVICIOS DE WINDOWS (DEBEN ESTAR CORRIENDO)

### Verificar Mosquitto:
```powershell
Get-Service -Name mosquitto
```

Si no está corriendo, iniciar como **Administrador**:
```powershell
net start mosquitto
```

### Verificar PostgreSQL:
```powershell
Get-Service -Name postgresql*
```

---

## 🎯 INICIO RÁPIDO - 3 TERMINALES

### **TERMINAL 1: Django Backend + MQTT Client**

```powershell
cd C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

**¿Qué hace?**
- Inicia el servidor Django en http://127.0.0.1:8000/
- Conecta automáticamente el cliente MQTT
- Espera datos de sensores

**Mensajes esperados:**
```
✅ Conectado al broker MQTT
📡 Suscrito a topic: devices/+/sensors
Starting development server at http://127.0.0.1:8000/
```

---

### **TERMINAL 2: Simulador ESP32**

```powershell
cd C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
.\venv\Scripts\Activate.ps1
python SCRIPTS\esp32_simulator.py
```

**Cuando pregunte:**
- `Device ID:` → `ESP32-001`
- `Broker:` → Presiona Enter (usa localhost)
- `Puerto:` → Presiona Enter (usa 1883)

**Mensajes esperados:**
```
✅ [ESP32-001] Conectado al broker MQTT
📤 Publicando datos cada 5 segundos...
📊 [ESP32-001] HR:75.2 BPM | SpO2:98.1% | Fatiga:23.0
```

---

### **TERMINAL 3: Frontend React**

```powershell
cd C:\Users\bauti\Downloads\respaldos\ZZZ-Web\fatigue-frontend
npm run dev
```

**URL Frontend:** http://localhost:5173/

---

## 🔍 VERIFICAR QUE TODO FUNCIONA

En **otra terminal** ejecuta:

```powershell
cd C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
.\venv\Scripts\Activate.ps1
python UTILS\diagnose_mqtt.py
```

**Deberías ver:**
```
1️⃣  VERIFICANDO MOSQUITTO... ✅ Mosquitto está corriendo
2️⃣  VERIFICANDO PUERTO 1883... ✅ Puerto 1883 está abierto
3️⃣  VERIFICANDO DJANGO... ✅ Django está corriendo en puerto 8000
4️⃣  VERIFICANDO BASE DE DATOS...
   ✅ Dispositivo ESP32-001 encontrado
   📊 Datos de sensores: 50+ (incrementándose)
   💓 HR: 75.2 BPM
   🫁 SpO2: 98.5%
```

---

## 🛠️ SCRIPTS ÚTILES

Todos los scripts están en la carpeta `UTILS/`

### Verificar datos en tiempo real:
```powershell
python UTILS\monitor_mqtt.py
```

### Verificar usuarios y dispositivos:
```powershell
python UTILS\check_data.py
```

### Crear nuevo dispositivo ESP32:
```powershell
python UTILS\create_esp32_device.py
```

### Diagnóstico completo del sistema:
```powershell
python UTILS\diagnose_mqtt.py
```

---

## 📱 DISPOSITIVOS DISPONIBLES

### **ESP32-001**
- **Empleado:** Ana Rodríguez (employee4@example.com)
- **Supervisor:** Juan Supervisor (supervisor@example.com)
- **Estado:** Activo

Para crear más dispositivos, ejecuta `create_esp32_device.py`

---

## 🔐 USUARIOS DE PRUEBA

### Administrador:
- Email: `admin@example.com`
- Password: `admin123`

### Supervisor:
- Email: `supervisor@example.com`
- Password: `supervisor123`

### Empleado:
- Email: `employee4@example.com`
- Password: `employee123`

---

## 🌐 URLs IMPORTANTES

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:5173 | Interfaz web principal |
| **Backend API** | http://127.0.0.1:8000/api/ | API REST |
| **Admin Panel** | http://127.0.0.1:8000/admin/ | Panel de administración Django |
| **API Docs** | http://127.0.0.1:8000/api/docs/ | Documentación Swagger |
| **MQTT Broker** | mqtt://localhost:1883 | Broker Mosquitto |

---

## ❌ SOLUCIÓN DE PROBLEMAS

### No se conecta al MQTT:
```powershell
# Verificar Mosquitto
Get-Service -Name mosquitto
# Si no corre, iniciar como admin
net start mosquitto
```

### No aparecen datos en la BD:
1. Verifica que Django muestre "✅ Conectado al broker MQTT"
2. Verifica que el simulador muestre "✅ Conectado al broker MQTT"
3. Ejecuta `diagnose_mqtt.py` para ver el problema

### Error de base de datos:
```powershell
python manage.py migrate
```

### Frontend no inicia:
```powershell
cd ZZZ-Web\fatigue-frontend
npm install
npm run dev
```

---

## 🔄 REINICIAR TODO

Si algo no funciona, cierra todas las terminales y:

1. **Reinicia Mosquitto** (como admin):
   ```powershell
   net stop mosquitto
   net start mosquitto
   ```

2. **Inicia en este orden:**
   - Terminal 1: Django
   - Terminal 2: Simulador ESP32
   - Terminal 3: Frontend

3. **Verifica con:**
   ```powershell
   python diagnose_mqtt.py
   ```

---

## 📊 ESTRUCTURA DEL PROYECTO

```
ZZZ-Backend/
├── apps/                    # Aplicaciones Django
│   ├── users/              # Gestión de usuarios
│   ├── devices/            # Dispositivos ESP32
│   ├── sensors/            # Datos de sensores
│   ├── analytics/          # Análisis y alertas
│   └── mqtt_client/        # Cliente MQTT
├── config/                 # Configuración Django
├── SCRIPTS/                # Scripts útiles
│   └── esp32_simulator.py # Simulador ESP32
├── venv/                   # Entorno virtual Python
├── manage.py              # CLI de Django
├── diagnose_mqtt.py       # Diagnóstico del sistema
├── check_data.py          # Verificar datos
└── COMO_INICIAR.md        # Este archivo

ZZZ-Web/
└── fatigue-frontend/      # Aplicación React
    ├── src/               # Código fuente
    ├── public/            # Archivos públicos
    └── package.json       # Dependencias Node
```

---

## 📞 SOPORTE

Si tienes problemas:
1. Ejecuta `diagnose_mqtt.py` y revisa los checks
2. Verifica los logs en las terminales
3. Consulta la documentación en `/MD/`

---

**✨ Sistema creado para detección de fatiga laboral mediante IoT y Machine Learning**
