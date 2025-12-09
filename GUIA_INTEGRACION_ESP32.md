# Guía de Integración ESP32 Físico

## ✅ Cambios Realizados

### Backend (Django)
1. ✅ **Script de registro**: `register_esp32_device.py`
   - Registra el dispositivo ESP32-001 en la BD
   - Asigna empleado, supervisor y empresa

2. ✅ **Nuevo endpoint**: `GET /api/devices/{id}/latest_sensor_data/`
   - Retorna último dato del sensor recibido vía MQTT
   - Incluye flag `is_live` (true si < 30 segundos)

### Frontend (React)
1. ✅ **Servicio actualizado**: `device.service.ts`
   - `getMyDevice()`: Obtiene dispositivo del empleado actual
   - `getLatestSensorData()`: Obtiene última lectura del sensor

2. ✅ **Dashboard actualizado**: `EmployeeDashboardPage.tsx`
   - Tarjetas con BPM y SpO2 en tiempo real del ESP32
   - Indicador visual "EN VIVO" cuando datos < 30s
   - Auto-refresh cada 5 segundos

---

## 🚀 Pasos para Completar la Integración

### **1. Registrar el ESP32-001 en la Base de Datos**

```bash
cd C:\Utt\ZZZ\ZZZ-Backend

# Activar entorno virtual
.\env\Scripts\Activate.ps1

# Editar el script si necesitas cambiar el email del empleado
# Por defecto usa: german.garmendia@zero.com
notepad register_esp32_device.py

# Ejecutar el script
python manage.py shell < register_esp32_device.py
```

**Salida esperada:**
```
============================================================
REGISTRANDO DISPOSITIVO ESP32 FÍSICO
============================================================
✓ Empleado encontrado: Germán Garmendia
✓ Supervisor: [Nombre del supervisor]
✓ Empresa: [Nombre de la empresa]
✓ Dispositivo ESP32-001 creado exitosamente

============================================================
RESUMEN DEL DISPOSITIVO
============================================================
ID del dispositivo: ESP32-001
Empleado:           Germán Garmendia
Email:              german.garmendia@zero.com
Supervisor:         [Supervisor]
Empresa:            [Empresa]
Estado:             Activo
Última conexión:    Nunca
============================================================

✅ DISPOSITIVO LISTO PARA RECIBIR DATOS VÍA MQTT
   Topic: devices/ESP32-001/sensors
============================================================
```

---

### **2. Verificar que el Cliente MQTT esté Corriendo**

El cliente MQTT debe estar corriendo en el backend para recibir datos del ESP32.

```bash
# En tu terminal de Django, verifica los logs
# Deberías ver algo como:
# 🚀 Cliente MQTT iniciando (192.168.3.67:1883)...
# ✅ MQTT conectado y suscrito
```

Si NO está corriendo, verifica:
- `config/settings.py` debe tener:
  ```python
  MQTT_BROKER = '192.168.3.67'
  MQTT_PORT = 1883
  MQTT_KEEPALIVE = 60
  ```
- El cliente MQTT se inicia automáticamente con `python manage.py runserver`
- Verifica que Mosquitto esté corriendo: `mosquitto -v`

---

### **3. Compilar y Flashear el ESP32**

```bash
cd C:\Utt\ZZZ\ZZZ-Backend\IoT

# Compilar firmware
.\build.ps1

# Flashear y monitorear
.\flash.ps1 monitor
```

**Salida esperada cada 5 segundos:**
```
I (5000) MAIN: ━━━ DIAGNÓSTICO XD58C ━━━
I (5000) MAIN:   Señal actual:     1650 mV
I (5000) MAIN:   Baseline:         2220 mV
I (5000) MAIN:   Rango [min-max]:  [1650 - 2700] = 1050 mV
I (5000) MAIN:   Umbral dinámico:  315 mV
I (5000) MAIN:   Dedo detectado:   ✓ SI
I (5000) MAIN:   Pulsos en ventana: 5 pulsos
I (5000) MAIN:   BPM actual:       75

I (5010) MQTT_PUB: 📤 Datos publicados (msg_id=1234)
```

---

### **4. Verificar Datos en el Backend**

#### Opción A: Con `mosquitto_sub` (Verificar MQTT)
```bash
mosquitto_sub -h 192.168.3.67 -t "devices/+/sensors" -v
```

**Salida esperada:**
```json
devices/ESP32-001/sensors {
  "device_id": "ESP32-001",
  "timestamp": "2025-12-04T10:30:00Z",
  "heart_rate": 75.0,
  "spo2": 98.0,
  "accel": {"x": 0.01, "y": -0.05, "z": 0.98}
}
```

#### Opción B: Verificar en Django Admin
1. Ir a: http://localhost:8000/admin/
2. Navegar a: `Sensors` → `Sensor Data`
3. Deberías ver registros del dispositivo `ESP32-001`

#### Opción C: Desde API
```bash
# Obtener último dato del sensor
curl http://localhost:8000/api/devices/1/latest_sensor_data/
```

**Respuesta esperada:**
```json
{
  "device_id": "ESP32-001",
  "timestamp": "2025-12-04T10:30:00Z",
  "heart_rate": 75.0,
  "spo2": 98.0,
  "accel_x": 0.01,
  "accel_y": -0.05,
  "accel_z": 0.98,
  "is_live": true,
  "seconds_ago": 2.3
}
```

---

### **5. Probar el Frontend**

```bash
cd C:\Utt\ZZZ\ZZZ-Web\fatigue-frontend

# Iniciar el frontend
npm run dev
```

1. **Login como empleado**: `german.garmendia@zero.com`
2. **Ir al Dashboard**: `/employee/dashboard`
3. **Verificar las tarjetas de sensores**:
   - ✅ "Ritmo Cardíaco (XD58C)" debe mostrar el BPM real
   - ✅ "Saturación de Oxígeno (SpO2)" debe mostrar el SpO2
   - ✅ Badge "ESP32 EN VIVO" debe estar visible
   - ✅ Datos se actualizan cada 5 segundos

---

## 🔧 Troubleshooting

### Problema 1: "No hay datos de sensor disponibles"
**Causa**: El ESP32 no ha enviado datos todavía.

**Solución**:
1. Verifica que el ESP32 esté conectado a WiFi
2. Verifica que Mosquitto esté corriendo
3. Verifica los logs del ESP32 con `.\flash.ps1 monitor`

---

### Problema 2: "is_live: false" (datos antiguos)
**Causa**: Hace más de 30 segundos que no llegan datos.

**Solución**:
1. Verifica que el ESP32 esté enviando datos cada 5 segundos
2. Verifica conexión WiFi del ESP32
3. Verifica que el cliente MQTT de Django esté activo

---

### Problema 3: BPM = 0
**Causa**: Sensor XD58C no detecta el dedo o mala calidad de señal.

**Solución**:
1. Presiona firmemente el dedo sobre el sensor
2. Verifica que el rango de señal sea > 100 mV en los logs
3. El algoritmo requiere **señal < 2000 mV** para buena presión
4. Espera al menos 5 segundos para que se calcule el BPM

---

### Problema 4: "No tienes un dispositivo asignado"
**Causa**: El dispositivo no está registrado para ese empleado.

**Solución**:
1. Ejecuta nuevamente `python manage.py shell < register_esp32_device.py`
2. Verifica que el email en el script coincida con tu usuario

---

## 📊 Flujo de Datos Completo

```
ESP32 (C Firmware)
  ↓ Cada 5 segundos
MQTT Broker (Mosquitto @ 192.168.3.67:1883)
  ↓ Topic: devices/ESP32-001/sensors
Django MQTT Client (apps/mqtt_client/client.py)
  ↓ Guarda en BD
Django REST API (/api/devices/{id}/latest_sensor_data/)
  ↓ Cada 5 segundos
React Frontend (EmployeeDashboardPage)
  ↓ Renderiza
UI: Tarjetas con BPM y SpO2 en tiempo real
```

---

## 🎯 Estado Actual

### ✅ Completado
- Script de registro de dispositivo
- Endpoint de datos en tiempo real
- Servicio de dispositivos en frontend
- UI del dashboard con sensores en vivo
- Auto-refresh cada 5 segundos

### ⏳ Pendiente
- Registrar ESP32-001 en la BD (ejecutar script)
- Verificar flujo completo E2E
- Ajustar algoritmo del XD58C si es necesario

---

## 📝 Notas Importantes

1. **La fatiga sigue siendo simulada**: Solo el ritmo cardíaco (XD58C) es real. La fatiga se calcula del simulador.

2. **SpO2 es valor fijo (98%)**: El ESP32 no tiene sensor de oxígeno, envía valor fijo.

3. **Auto-refresh**: Los datos se actualizan automáticamente cada 5 segundos sin recargar la página.

4. **Indicador "EN VIVO"**: Solo se muestra si los datos tienen menos de 30 segundos de antigüedad.

5. **Threshold del sensor**: El nuevo algoritmo detecta mejor cuando hay **buena presión** (señal < 2000 mV).

---

¿Listo para probar? 🚀
