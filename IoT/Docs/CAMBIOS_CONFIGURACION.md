# 🔄 Resumen de Cambios de Configuración

## 📌 Cambio Principal

Se actualizó la configuración del proyecto para reflejar el hardware real del usuario:

### XD58C - De I2C a Analógico
**Antes** (Incorrecto):
- Sensor I2C con dirección 0x57
- Pines: SDA=GPIO21, SCL=GPIO22
- Funciones: `xd58c_read()` devolvía `(red, ir)`

**Ahora** (Correcto):
- **Sensor analógico** conectado a GPIO34 (ADC1_CH6)
- Salida: 0-3.3V proporcional al pulso cardíaco
- Funciones:
  - `xd58c_read_analog()` → valor ADC (0-4095)
  - `xd58c_read_voltage()` → voltaje en mV (0-3300)

### ADXL345 - Pines I2C Personalizados
**Antes** (Incorrecto):
- SDA=GPIO21, SCL=GPIO22 (pines I2C estándar)

**Ahora** (Correcto):
- **SDA=GPIO16, SCL=GPIO17** (pines personalizados)
- Se agregó función `adxl345_i2c_init()` para configurar bus I2C
- Mantiene dirección 0x53 (SDO=GND)

---

## 📂 Archivos Modificados

### 1️⃣ Drivers en C

#### `IoT/main/xd58c_driver.h`
- ✅ Removido: Registros I2C, definiciones MAX30102
- ✅ Agregado: Configuración ADC (canal, ancho, atenuación)
- ✅ Nueva función: `xd58c_read_analog(uint32_t *value)`
- ✅ Nueva función: `xd58c_read_voltage(uint32_t *mv)`

#### `IoT/main/xd58c_driver.c`
- ✅ Reescrito completamente de I2C a ADC
- ✅ Usa `adc1_config_channel_atten()` y `esp_adc_cal_characterize()`
- ✅ Promedia 10 muestras para reducir ruido
- ✅ Incluye conversión calibrada a voltaje

#### `IoT/main/adxl345_driver.h`
- ✅ Actualizado: `I2C_MASTER_SDA_IO 16`
- ✅ Actualizado: `I2C_MASTER_SCL_IO 17`
- ✅ Nueva función: `esp_err_t adxl345_i2c_init(void)`

#### `IoT/main/adxl345_driver.c`
- ✅ Agregada función `adxl345_i2c_init()` con pines personalizados
- ✅ Configuración I2C: 100 kHz, pull-ups habilitados

#### `IoT/main/micropython_bindings.c`
- ✅ Actualizado: `mp_xd58c_read()` devuelve `int` (valor ADC)
- ✅ Nueva función: `mp_xd58c_voltage()` devuelve `int` (voltaje mV)
- ✅ Módulo Python 'sensors' actualizado

#### `IoT/main/main.c`
- ✅ Orden de inicialización:
  1. `xd58c_init()` (ADC)
  2. `adxl345_i2c_init()` (bus I2C)
  3. `adxl345_init()` (sensor)
- ✅ Loop de prueba usa valores ADC y voltaje

### 2️⃣ Scripts de Python

#### `IoT/scripts/sensor_monitor.py`
- ✅ Actualizado: Lee `adc_value = sensors.xd58c_read()`
- ✅ Actualizado: Lee `voltage_mv = sensors.xd58c_voltage()`
- ✅ Removido: Referencias a red/IR
- ✅ Mantiene: Detección de BPM con algoritmo de picos

#### `IoT/scripts/test_basic.py`
- ✅ Actualizado: Prueba básica con ADC y voltaje
- ✅ Muestra valores en rango 0-4095 y 0-3300mV

#### `IoT/scripts/bidirectional_example.py`
- ✅ Actualizado: Función `process_sensor_data(adc_value, x, y, z)`
- ✅ Actualizado: Loop principal lee ADC y acelerómetro
- ✅ Mantiene: Ejemplo de comunicación C↔Python

### 3️⃣ Documentación

#### `IoT/CONEXIONES.md` ⭐ **NUEVO**
- ✅ Guía completa de conexiones físicas
- ✅ Diagramas ASCII de pines
- ✅ Tabla de conexiones detallada
- ✅ Ejemplos de código C y Python
- ✅ Valores típicos esperados
- ✅ Solución de problemas comunes

#### `IoT/README.md`
- ✅ Actualizado: Descripción de sensores
- ✅ Actualizado: Sección "Conexión de Sensores"
- ✅ Agregado: Referencia a `CONEXIONES.md`
- ✅ Actualizado: Hardware necesario

#### `IoT/QUICKSTART.md`
- ✅ Actualizado: Diagrama de conexiones (GPIO34, GPIO16/17)
- ✅ Actualizado: Salida esperada del monitor serial
- ✅ Removido: Referencias a lecturas I2C del XD58C

#### `IoT/SENSOR_SPECS.md`
- ✅ Reescrito completamente: Sección XD58C
  - Especificaciones de sensor analógico
  - Configuración ADC del ESP32
  - Algoritmo de detección de frecuencia cardíaca
  - Valores típicos (ADC y voltaje)
  - Consejos de uso
- ✅ Actualizado: Sección ADXL345
  - Pines I2C personalizados (GPIO16/17)
  - Función `adxl345_i2c_init()`

#### `IoT/CAMBIOS_CONFIGURACION.md` ⭐ **NUEVO**
- ✅ Este documento

---

## 🔌 Configuración de Hardware

### Conexiones Finales

```
┌─────────────────────────────────────┐
│           ESP32 DevKit              │
│                                     │
│  GPIO34 (ADC) ──────┐               │
│                      │               │
│  GPIO16 (SDA) ───┐  │               │
│  GPIO17 (SCL) ───┼──┼───            │
│                   │  │               │
│  3.3V  ───────────┼──┼───            │
│  GND   ───────────┼──┼───            │
│                   │  │               │
└───────────────────┼──┼───────────────┘
                    │  │
       ┌────────────┘  └────────────┐
       │                            │
  ┌────▼─────┐                ┌─────▼────┐
  │ ADXL345  │                │  XD58C   │
  │          │                │          │
  │ VCC  3.3V│                │ VCC  3.3V│
  │ GND  GND │                │ GND  GND │
  │ SDA  GP16│                │ OUT  GP34│
  │ SCL  GP17│                └──────────┘
  │ SDO  GND │
  │ CS   3.3V│
  └──────────┘
```

### Tabla de Pines

| Sensor | Pin | ESP32 | Tipo |
|--------|-----|-------|------|
| XD58C | VCC | 3.3V | Alimentación |
| XD58C | GND | GND | Tierra |
| XD58C | OUT | **GPIO34** | ⚠️ Analógico (ADC1_CH6) |
| ADXL345 | VCC | 3.3V | Alimentación |
| ADXL345 | GND | GND | Tierra |
| ADXL345 | SDA | **GPIO16** | ⚠️ I2C Datos |
| ADXL345 | SCL | **GPIO17** | ⚠️ I2C Clock |
| ADXL345 | SDO | GND | Dirección I2C (0x53) |
| ADXL345 | CS | 3.3V | Modo I2C |

---

## 🔧 Cómo Usar

### Compilar y Flashear

```powershell
cd C:\Utt\ZZZ\ZZZ-Backend\IoT

# Limpiar (opcional)
idf.py fullclean

# Compilar
idf.py build

# Flashear y monitorear (cambiar COM3 por tu puerto)
idf.py -p COM3 flash monitor
```

### Salida Esperada

```
I (123) MAIN: Inicializando XD58C (ADC)...
I (234) XD58C: ADC configurado - Canal 6 (GPIO34)
I (345) XD58C: Calibración ADC completada
I (456) XD58C: XD58C inicializado correctamente
I (567) MAIN: Inicializando I2C (GPIO16/GPIO17)...
I (678) MAIN: Inicializando ADXL345...
I (789) ADXL345: ADXL345 detectado - DEVICE_ID: 0xE5
I (890) ADXL345: ADXL345 inicializado correctamente

=== Sistema Listo ===

I (2000) MAIN: [C] XD58C -> ADC: 2048, Voltaje: 1650mV
I (2100) MAIN: [C] ADXL345 -> X: 0.012g, Y: -0.008g, Z: 0.998g
```

### Usar desde Python (MicroPython)

```python
import sensors

# Inicializar
sensors.xd58c_init()
sensors.adxl345_init()

# Leer XD58C
adc = sensors.xd58c_read()      # 0-4095
voltage = sensors.xd58c_voltage()  # mV

print(f"Pulso: ADC={adc}, V={voltage}mV")

# Leer ADXL345
x, y, z = sensors.adxl345_read()
print(f"Aceleración: X={x:.3f}g, Y={y:.3f}g, Z={z:.3f}g")
```

---

## ⚠️ Notas Importantes

### GPIO34 (XD58C)
- ✅ Solo entrada (input-only)
- ✅ ADC1_CH6
- ✅ Sin pull-up/pull-down interno
- ❌ No se puede usar WiFi mientras se lee ADC1

### GPIO16/GPIO17 (ADXL345)
- ✅ Soportan I2C
- ✅ Pull-ups internos habilitados
- ⚠️ NO son los pines I2C estándar (21/22)

### XD58C
- ✅ Sensor analógico simple (NO I2C)
- ✅ Requiere contacto con la piel
- ✅ Valores varían con cada latido
- ❌ No mide SpO2 (solo pulso)

### ADXL345
- ✅ SDO debe estar en GND (dirección 0x53)
- ✅ CS debe estar en HIGH (modo I2C)
- ✅ Soporta 100-400 kHz I2C

---

## 📚 Referencias Rápidas

- **Conexiones detalladas**: `CONEXIONES.md`
- **Inicio rápido**: `QUICKSTART.md`
- **Especificaciones**: `SENSOR_SPECS.md`
- **Guía completa**: `README.md`

---

## ✅ Checklist de Migración

- [x] Reescribir driver XD58C (I2C → ADC)
- [x] Actualizar pines ADXL345 (GPIO21/22 → GPIO16/17)
- [x] Agregar `adxl345_i2c_init()`
- [x] Actualizar bindings MicroPython
- [x] Actualizar main.c
- [x] Actualizar scripts Python (3 archivos)
- [x] Crear CONEXIONES.md
- [x] Actualizar README.md
- [x] Actualizar QUICKSTART.md
- [x] Actualizar SENSOR_SPECS.md
- [x] Crear CAMBIOS_CONFIGURACION.md

---

**Estado**: ✅ **Configuración actualizada completamente**

Todos los archivos han sido modificados para reflejar la configuración real del hardware:
- XD58C en GPIO34 (analógico)
- ADXL345 en GPIO16/17 (I2C)
