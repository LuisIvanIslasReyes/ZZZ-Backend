# 🚀 Inicio Rápido - ESP32 con Sensores

## ⚡ Empezar en 5 minutos

### 1. Verificar Requisitos

```powershell
# Verificar ESP-IDF
idf.py --version

# Verificar Python
python --version

# Verificar Git
git --version
```

### 2. Compilar Proyecto (Solo C, sin MicroPython)

```powershell
# Navegar al proyecto
cd C:\Utt\ZZZ\ZZZ-Backend\IoT

# Configurar target
idf.py set-target esp32

# Compilar
idf.py build
```

### 3. Conectar Hardware

⚠️ **IMPORTANTE**: Ver `CONEXIONES.md` para guía detallada y solución de problemas.

#### XD58C (Sensor de Pulso) - **ANALÓGICO**
```
XD58C → ESP32
VCC     → 3.3V
GND     → GND
OUT/Signal → GPIO34  ⚠️ ANALÓGICO (ADC1_CH6)
```

#### ADXL345 (Acelerómetro) - **I2C**
```
ADXL345 → ESP32
VCC  → 3.3V
GND  → GND
SCL  → GPIO17   ⚠️ PERSONALIZADO
SDA  → GPIO16   ⚠️ PERSONALIZADO
SDO  → GND      ← IMPORTANTE (dirección 0x53)
CS   → 3.3V     ← IMPORTANTE (modo I2C)
```

### 4. Flashear y Monitorear

```powershell
# Flashear (cambiar COM3 por tu puerto)
idf.py -p COM3 flash monitor

# Salir del monitor: Ctrl + ]
```

---

## 📊 Qué Esperar

Después de flashear, verás en el monitor:

```
===================================
ESP32 + MicroPython + Sensores
===================================
I (123) MAIN: Inicializando XD58C (ADC)...
I (234) XD58C: ADC configurado - Canal 6 (GPIO34)
I (345) XD58C: Calibración ADC completada
I (456) XD58C: XD58C inicializado correctamente
I (567) MAIN: Inicializando I2C (GPIO16/GPIO17)...
I (678) MAIN: Inicializando ADXL345...
I (789) ADXL345: ADXL345 detectado - DEVICE_ID: 0xE5
I (890) ADXL345: ADXL345 inicializado correctamente
I (1000) MAIN: Calibrando ADXL345...
I (1234) ADXL345: Calibración completada - Offsets: X=0, Y=1, Z=-2
===================================
Sistema inicializado correctamente
===================================
I (2000) MAIN: [C] XD58C -> ADC: 2048, Voltaje: 1650mV
I (2100) MAIN: [C] ADXL345 -> X: 0.012g, Y: -0.008g, Z: 0.998g
```

---

## 🔧 Comandos Útiles

### Compilación

```powershell
# Compilar solo
idf.py build

# Limpiar build
idf.py fullclean

# Ver tamaño
idf.py size

# Ver componentes
idf.py size-components
```

### Flash

```powershell
# Flash rápido (solo app)
idf.py app-flash

# Flash completo
idf.py flash

# Borrar flash
idf.py erase-flash
```

### Monitor

```powershell
# Monitor básico
idf.py monitor

# Monitor con filtros
idf.py monitor --print_filter="*:I"

# Solo errores
idf.py monitor --print_filter="*:E"
```

### Todo en uno

```powershell
# Compilar + Flash + Monitor
idf.py build flash monitor
```

---

## 🐛 Solución Rápida de Problemas

### ❌ "No se puede abrir puerto COM3"

```powershell
# Listar puertos disponibles
mode

# Buscar dispositivos USB
Get-PnpDevice -Class Ports

# Instalar driver CH340/CP2102 si es necesario
```

### ❌ "Error leyendo MAX30102"

1. Verificar conexiones físicas
2. Verificar voltaje (usar 3.3V, NO 5V)
3. Agregar resistencias pull-up 4.7kΩ en SDA/SCL
4. Escanear bus I2C:

```c
// Agregar en main.c para debug
for (uint8_t addr = 1; addr < 127; addr++) {
    i2c_cmd_handle_t cmd = i2c_cmd_link_create();
    i2c_master_start(cmd);
    i2c_master_write_byte(cmd, (addr << 1) | I2C_MASTER_WRITE, true);
    i2c_master_stop(cmd);
    
    if (i2c_master_cmd_begin(I2C_NUM_0, cmd, 50) == ESP_OK) {
        printf("I2C device at 0x%02X\n", addr);
    }
    i2c_cmd_link_delete(cmd);
}
```

### ❌ "ADXL345 lee 0g en todos los ejes"

1. Verificar que SDO esté conectado a GND
2. Verificar que CS esté conectado a 3.3V (modo I2C)
3. Verificar dirección I2C (debe ser 0x53)

### ❌ "Compilación falla"

```powershell
# Limpiar completamente
idf.py fullclean

# Reconfigurar
idf.py set-target esp32

# Compilar de nuevo
idf.py build
```

---

## 📝 Modificar Comportamiento

### Cambiar frecuencia de lectura

En `main.c`, línea ~120:

```c
// Cambiar 2000 por valor deseado (en milisegundos)
vTaskDelay(pdMS_TO_TICKS(2000));  // 2 segundos
vTaskDelay(pdMS_TO_TICKS(500));   // 0.5 segundos
vTaskDelay(pdMS_TO_TICKS(100));   // 0.1 segundos
```

### Cambiar pines I2C

En `xd58c_driver.h`, líneas 33-34:

```c
#define I2C_MASTER_SCL_IO      22  // Cambiar aquí
#define I2C_MASTER_SDA_IO      21  // Cambiar aquí
```

### Cambiar corriente de LEDs MAX30102

En `max30102_driver.c`, líneas 90-94:

```c
// Valores: 0x00 = 0mA, 0x24 = 6.4mA, 0x3F = 12.5mA, 0xFF = 50mA
max30102_write_register(MAX30102_REG_LED1_PA, 0x24);  // LED rojo
max30102_write_register(MAX30102_REG_LED2_PA, 0x24);  // LED IR
```

### Cambiar rango del ADXL345

En `adxl345_driver.c`, línea 42:

```c
// 0x08 = ±2g, 0x09 = ±4g, 0x0A = ±8g, 0x0B = ±16g
adxl345_write_register(ADXL345_REG_DATA_FORMAT, 0x08);
```

---

## 🎯 Próximos Pasos

1. ✅ **Verificar que funciona con C** (este documento)
2. 🔄 **Agregar MicroPython** (ver `SETUP_MICROPYTHON.md`)
3. 📊 **Implementar algoritmos** (frecuencia cardíaca, detección de caídas)
4. 🌐 **Agregar WiFi** (enviar datos a servidor)
5. 📱 **Crear app móvil** (BLE o WiFi)

---

## 📚 Documentos Relacionados

- `README.md` - Guía completa del proyecto
- `SETUP_MICROPYTHON.md` - Cómo integrar MicroPython
- `SENSOR_SPECS.md` - Especificaciones técnicas de sensores

---

## 💬 Necesitas Ayuda?

1. Revisa logs en `idf.py monitor`
2. Verifica conexiones físicas
3. Consulta `README.md` para troubleshooting detallado
4. Revisa datasheets en `SENSOR_SPECS.md`

---

**¡Listo para empezar! 🎉**

```powershell
cd C:\Utt\ZZZ\ZZZ-Backend\IoT
idf.py set-target esp32
idf.py build
idf.py -p COM3 flash monitor
```
