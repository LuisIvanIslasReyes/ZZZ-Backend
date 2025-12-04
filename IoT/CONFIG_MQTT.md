# Configuración del ESP32 para conexión IoT

## 📝 ANTES DE COMPILAR, DEBES MODIFICAR:

### 1. Credenciales WiFi
Edita `main/main.c` líneas 16-17:

```c
#define WIFI_SSID     "TU_RED_WIFI"        // ⚠️ CAMBIAR
#define WIFI_PASSWORD "TU_CONTRASEÑA_WIFI" // ⚠️ CAMBIAR
```

### 2. Configuración MQTT
Edita `main/mqtt_publisher.h` líneas 8-10:

```c
#define MQTT_BROKER_URI     "mqtt://192.168.1.100:1883"  // IP de tu servidor Django
#define MQTT_USERNAME       ""                            // Usuario MQTT (opcional)
#define MQTT_PASSWORD       ""                            // Contraseña MQTT (opcional)
```

### 3. Identificador del Dispositivo
Edita `main/mqtt_publisher.h` línea 13:

```c
#define DEVICE_ID           "ESP32-001"  // Debe existir en Django
```

---

## 🔧 Instalación del Broker MQTT en el Servidor Django

### Opción 1: Mosquitto (recomendado)

**En Linux/Ubuntu:**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

**En Windows:**
1. Descargar desde: https://mosquitto.org/download/
2. Instalar y ejecutar como servicio

**Configuración básica** (`/etc/mosquitto/mosquitto.conf`):
```
listener 1883
allow_anonymous true
```

**Reiniciar:**
```bash
sudo systemctl restart mosquitto
```

### Opción 2: Usar MQTT en Docker

```bash
cd C:\Utt\ZZZ\ZZZ-Backend
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto
```

---

## 🚀 Flujo de Datos

```
┌─────────────┐      MQTT (JSON)       ┌──────────────┐
│   ESP32     │ ───────────────────────>│  Mosquitto   │
│  (Sensores) │  Topic: devices/+/sensors│   Broker     │
└─────────────┘                         └──────────────┘
                                               │
                                               │ Subscribe
                                               ▼
                                        ┌──────────────┐
                                        │   Django     │
                                        │  (Backend)   │
                                        └──────────────┘
                                               │
                                               │ WebSocket/REST
                                               ▼
                                        ┌──────────────┐
                                        │   Frontend   │
                                        │   (React)    │
                                        └──────────────┘
```

---

## 📡 Formato de Mensaje MQTT

**Topic:** `devices/ESP32-001/sensors`

**Payload (JSON):**
```json
{
  "device_id": "ESP32-001",
  "timestamp": "2025-12-04T00:30:00Z",
  "heart_rate": 75.0,
  "spo2": 98.0,
  "accel": {
    "x": 0.012,
    "y": -0.004,
    "z": 0.998
  }
}
```

---

## ✅ Verificación

### 1. Verificar que Mosquitto está corriendo:
```bash
# Linux
sudo systemctl status mosquitto

# Windows
# Verificar en Servicios de Windows
```

### 2. Probar suscripción manualmente:
```bash
mosquitto_sub -h localhost -t "devices/+/sensors" -v
```

### 3. Ver logs del ESP32:
```bash
cd C:\Utt\ZZZ\ZZZ-Backend\IoT
.\flash.ps1
```

---

## 🐛 Troubleshooting

### ESP32 no se conecta a WiFi
- Verificar SSID y contraseña
- Asegurar que la red es 2.4 GHz (ESP32 no soporta 5 GHz)
- Ver logs: `I (xxx) MQTT_PUB: WiFi conectado - IP: xxx`

### MQTT no conecta
- Verificar IP del broker (usar `ipconfig` o `ifconfig`)
- Verificar firewall no bloquea puerto 1883
- Probar con `mosquitto_pub -h IP -t test -m "hello"`

### Django no recibe datos
- Verificar que el cliente MQTT de Django esté corriendo
- Verificar que el `device_id` existe en la base de datos
- Ver logs del backend: `apps/mqtt_client/client.py`

---

## 📊 Próximos Pasos

1. ✅ Compilar y flashear firmware
2. ✅ Verificar conexión WiFi/MQTT en monitor serial
3. ⏳ Configurar backend Django para recibir datos
4. ⏳ Crear visualización en tiempo real en frontend
5. ⏳ Implementar detección de anomalías (ya existe en `apps/analytics/`)
