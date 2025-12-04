# 🚀 Guía Completa: ESP32 + MicroPython + Sensores

## 📋 Índice
1. [Introducción](#introducción)
2. [Requisitos Previos](#requisitos-previos)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Configuración de MicroPython como Componente](#configuración-de-micropython-como-componente)
5. [Compilación del Proyecto](#compilación-del-proyecto)
6. [Carga de Scripts Python sin Recompilar](#carga-de-scripts-python-sin-recompilar)
7. [Ejemplos de Uso](#ejemplos-de-uso)
8. [Monitoreo y Debugging](#monitoreo-y-debugging)
9. [Conexión de Sensores](#conexión-de-sensores)
10. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Introducción

Este proyecto integra **MicroPython como componente** dentro de un firmware ESP-IDF, permitiendo:

✅ **Código C nativo** para drivers de bajo nivel de sensores  
✅ **Scripts Python** para lógica de alto nivel  
✅ **Comunicación bidireccional** entre C y Python  
✅ **Actualización de scripts** sin recompilar firmware  
✅ **Sistema de archivos SPIFFS** para almacenar scripts  

### Sensores Implementados
- **XD58C**: Sensor de pulso cardíaco analógico (GPIO34 - ADC)
- **ADXL345**: Acelerómetro de 3 ejes (GPIO16/17 - I2C)

---

## 📦 Requisitos Previos

### Software Necesario

1. **ESP-IDF v5.0 o superior**
   ```powershell
   # Verificar instalación
   idf.py --version
   ```

2. **Python 3.8+**
   ```powershell
   python --version
   ```

3. **Git**
   ```powershell
   git --version
   ```

4. **Visual Studio Code** con extensiones:
   - ESP-IDF
   - C/C++
   - Python

### Hardware Necesario

- ESP32 DevKit (con ADC y I2C)
- Sensor XD58C (sensor analógico de pulso - 3 pines)
- Sensor ADXL345 (módulo I2C)
- Cables Dupont
- Cable USB

⚠️ **Ver `CONEXIONES.md` para diagrama detallado de conexiones**

---

## 📁 Estructura del Proyecto

```
IoT/
├── CMakeLists.txt              # Configuración principal del proyecto
├── sdkconfig.defaults          # Configuración por defecto
├── partitions.csv              # Tabla de particiones (incluye SPIFFS)
├── main/
│   ├── CMakeLists.txt          # Configuración del componente main
│   ├── main.c                  # Punto de entrada del firmware
│   ├── xd58c_driver.h          # Header del driver XD58C
│   ├── xd58c_driver.c          # Implementación XD58C
│   ├── adxl345_driver.h        # Header del driver ADXL345
│   ├── adxl345_driver.c        # Implementación ADXL345
│   ├── micropython_bindings.h  # Header de bindings Python-C
│   └── micropython_bindings.c  # Implementación de bindings
├── components/
│   └── micropython/            # MicroPython como componente (clonar aquí)
├── scripts/
│   ├── sensor_monitor.py       # Script de monitoreo completo
│   ├── test_basic.py           # Prueba básica de sensores
│   └── bidirectional_example.py # Ejemplo bidireccional C-Python
└── README.md                   # Esta guía
```

---

## ⚙️ Configuración de MicroPython como Componente

### Paso 1: Clonar MicroPython

**Nota importante**: MicroPython debe integrarse como componente ESP-IDF. Aquí hay dos opciones:

#### Opción A: Usar el port ESP32 de MicroPython (Recomendado)

```powershell
# Navegar a la carpeta del proyecto
cd C:\Utt\ZZZ\ZZZ-Backend\IoT

# Crear carpeta de componentes si no existe
New-Item -ItemType Directory -Force -Path components

# Clonar MicroPython
cd components
git clone --recursive https://github.com/micropython/micropython.git

# Navegar al port ESP32
cd micropython\ports\esp32
```

#### Opción B: Usar MicroPython como submódulo git

```powershell
cd C:\Utt\ZZZ\ZZZ-Backend\IoT
git submodule add https://github.com/micropython/micropython.git components/micropython
git submodule update --init --recursive
```

### Paso 2: Preparar MicroPython para ESP-IDF

```powershell
# Desde components/micropython/ports/esp32
cd C:\Utt\ZZZ\ZZZ-Backend\IoT\components\micropython\ports\esp32

# Construir componentes de MicroPython
idf.py set-target esp32
```

### Paso 3: Actualizar CMakeLists.txt principal

El archivo `IoT/CMakeLists.txt` ya está configurado para incluir MicroPython. Verifica que contenga:

```cmake
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(esp32_micropython_sensors)
```

### Paso 4: Configurar componente main

El archivo `main/CMakeLists.txt` debe incluir las dependencias necesarias:

```cmake
idf_component_register(
    SRCS 
        "main.c"
        "max30102_driver.c"
        "adxl345_driver.c"
        "micropython_bindings.c"
    INCLUDE_DIRS "."
    REQUIRES 
        driver
        nvs_flash
        spiffs
)
```

---

## 🔨 Compilación del Proyecto

### Paso 1: Configurar el proyecto

```powershell
cd C:\Utt\ZZZ\ZZZ-Backend\IoT

# Configurar target (ESP32)
idf.py set-target esp32

# Configuración interactiva (opcional)
idf.py menuconfig
```

### Paso 2: Compilar el firmware

```powershell
# Compilar todo
idf.py build
```

**Tiempo estimado**: 5-15 minutos la primera vez (descarga dependencias)

### Paso 3: Flashear al ESP32

```powershell
# Detectar puerto COM automáticamente y flashear
idf.py flash

# O especificar puerto manualmente
idf.py -p COM3 flash
```

### Paso 4: Verificar funcionamiento

```powershell
# Abrir monitor serial
idf.py monitor

# Salir del monitor: Ctrl+]
```

---

## 📤 Carga de Scripts Python sin Recompilar

Una de las ventajas principales es poder actualizar scripts Python sin recompilar todo el firmware.

### Método 1: Usando `parttool.py` (ESP-IDF)

```powershell
# Escribir un archivo directamente a SPIFFS
cd C:\Utt\ZZZ\ZZZ-Backend\IoT

# Crear imagen SPIFFS
python $Env:IDF_PATH\components\spiffs\spiffsgen.py 1048576 scripts spiffs.bin

# Flashear partición SPIFFS
python $Env:IDF_PATH\components\partition_table\parttool.py -p COM3 write_partition --partition-name storage --input spiffs.bin
```

### Método 2: Usando `mpremote` (Más fácil)

**Instalar mpremote**:
```powershell
pip install mpremote
```

**Copiar archivo al ESP32**:
```powershell
# Conectar a ESP32
mpremote connect COM3

# Copiar archivo
mpremote fs cp scripts\sensor_monitor.py :/spiffs/sensor_monitor.py

# Listar archivos
mpremote fs ls /spiffs

# Ejecutar script
mpremote exec "exec(open('/spiffs/sensor_monitor.py').read())"
```

### Método 3: WebREPL (Wi-Fi)

**Habilitar WebREPL en el código**:
```python
import webrepl
webrepl.start()
```

Luego usar el cliente web: http://micropython.org/webrepl/

**Cargar archivo via WebREPL**:
1. Abrir http://micropython.org/webrepl/
2. Conectar a la IP del ESP32
3. Usar botón "Send a file"
4. Seleccionar `sensor_monitor.py`

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Lectura desde C

El archivo `main.c` incluye una tarea que lee los sensores directamente desde C:

```c
void test_sensors_task_c(void *pvParameters) {
    while (1) {
        // Leer XD58C
        uint32_t red, ir;
        xd58c_read_fifo(&red, &ir);
        ESP_LOGI(TAG, "Red: %lu, IR: %lu", red, ir);
        
        // Leer ADXL345
        adxl345_accel_t accel;
        adxl345_read_accel(&accel);
        ESP_LOGI(TAG, "X: %.3fg, Y: %.3fg, Z: %.3fg", 
                 accel.x, accel.y, accel.z);
        
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}
```

**Activar**: La tarea ya está activa por defecto en `main.c`.

### Ejemplo 2: Lectura desde Python

Script: `scripts/test_basic.py`

```python
import sensors
import time

# Inicializar sensores
sensors.xd58c_init()
sensors.adxl345_init()

for i in range(10):
    # Leer pulso
    red, ir = sensors.xd58c_read()
    print(f"Pulso -> Red: {red}, IR: {ir}")
    
    # Leer acelerómetro
    x, y, z = sensors.adxl345_read()
    print(f"Aceleración -> X: {x:.3f}g, Y: {y:.3f}g, Z: {z:.3f}g")
    
    time.sleep(1)
```

**Ejecutar desde C**:
```c
// En main.c, cambiar línea 120:
// xTaskCreate(test_sensors_task_c, "test_c", 4096, NULL, 5, NULL);
// Por:
xTaskCreate(test_sensors_task_python, "test_python", 8192, NULL, 5, NULL);
```

### Ejemplo 3: Python llamando C

```python
import sensors

# Llamar función nativa en C
sensors.log_message("¡Hola desde Python!")

# Inicializar hardware (driver en C)
sensors.xd58c_init()
sensors.adxl345_init()

# Leer datos (procesados en C)
red, ir = sensors.xd58c_read()
temp = sensors.xd58c_temperature()
x, y, z = sensors.adxl345_read()
```

### Ejemplo 4: C llamando Python

Para que C pueda llamar funciones Python, necesitas modificar `main.c`:

```c
// Agregar al inicio de app_main():
const char *python_function = 
    "def process_data(value):\n"
    "    result = value * 2 + 10\n"
    "    print(f'Resultado: {result}')\n"
    "    return result\n";

micropython_exec_string(python_function);

// Luego llamar la función:
const char *call_function = "process_data(42)";
micropython_exec_string(call_function);
```

---

## 🔍 Monitoreo y Debugging

### Monitor Serial Básico

```powershell
# Abrir monitor
idf.py monitor

# Salir: Ctrl+]
```

### Monitor con filtros de log

```powershell
# Solo mostrar logs de nivel INFO o superior
idf.py monitor --print_filter="*:I"

# Mostrar solo logs de componente específico
idf.py monitor --print_filter="MAX30102:*"
```

### Ver logs de Python

Los prints de Python aparecen en el monitor serial automáticamente:

```python
print("Esto aparece en el monitor")
sensors.log_message("Esto usa ESP_LOGI desde C")
```

### Debugging con GDB

```powershell
# Compilar con símbolos de debug
idf.py build

# Iniciar OpenOCD (en terminal separada)
openocd -f board/esp32-wrover-kit-3.3v.cfg

# En otra terminal, iniciar GDB
xtensa-esp32-elf-gdb build/esp32_micropython_sensors.elf
(gdb) target remote :3333
(gdb) monitor reset halt
(gdb) continue
```

### Capturar logs en archivo

```powershell
idf.py monitor > logs.txt 2>&1
```

---

## 🔌 Conexión de Sensores

⚠️ **IMPORTANTE**: Ver documento detallado `CONEXIONES.md` para guía completa.

### XD58C (Sensor de Pulso) - **ANALÓGICO**

**Conexiones**:

| XD58C    | ESP32  | Descripción |
|----------|--------|-------------|
| VCC      | 3.3V   | Alimentación |
| GND      | GND    | Tierra |
| OUT/Signal | **GPIO34** | ⚠️ Señal analógica (ADC1_CH6) |

**Características**:
- ✅ **Sensor analógico** (NO I2C)
- ✅ Salida: 0-3.3V proporcional al pulso
- ✅ GPIO34 es input-only (ADC1_CH6)
- ✅ Rango ADC: 0-4095 (12 bits)

**Notas**:
- Requiere contacto con la piel para lecturas precisas
- Colocar dedo suavemente sobre el sensor
- Los valores varían con cada pulsación (2000-3500 típico)

### ADXL345 (Acelerómetro) - **I2C**

**Conexiones I2C**:

| ADXL345  | ESP32  | Descripción |
|----------|--------|-------------|
| VCC      | 3.3V   | Alimentación |
| GND      | GND    | Tierra |
| SCL      | **GPIO17** | ⚠️ Clock I2C |
| SDA      | **GPIO16** | ⚠️ Datos I2C |
| SDO      | GND    | ← Importante (dirección I2C 0x53) |
| CS       | 3.3V   | ← Modo I2C

**Notas**:
- SDO debe estar conectado a GND para dirección 0x53
- Si SDO está en 3.3V, la dirección será 0x1D (modificar código)
- Calibrar antes de usar para mejores resultados

### Diagrama de Conexión

```
ESP32 DevKit          XD58C             ADXL345
┌────────────┌       ┌─────────┌       ┌─────────┌
│            │       │         │       │         │
│  3.3V ─────┤───────┤ VIN     │       │ VCC     │
│            │       │         │       │         │
│  GND  ─────┤───────┤ GND     ├───────┤ GND     │
│            │       │         │       │         │
│  GPIO22────┤───────┤ SCL     ├───────┤ SCL     │
│   (SCL)    │       │         │       │         │
│  GPIO21────┤───────┤ SDA     ├───────┤ SDA     │
│   (SDA)    │       │         │       │         │
└────────────┘       └─────────┘       │ SDO─GND │
                                       │ CS──3.3V│
                                       └─────────┘
```

---

## 🛠️ Solución de Problemas

### Problema: "No se detecta el sensor"

**Síntomas**:
```
E (1234) XD58C: Error leyendo PART_ID
```

**Soluciones**:
1. Verificar conexiones físicas (especialmente GND)
2. Verificar voltaje (usar 3.3V, NO 5V)
3. Verificar dirección I2C con scanner:
   ```c
   // Agregar en main.c para escanear I2C
   for (uint8_t addr = 1; addr < 127; addr++) {
       i2c_cmd_handle_t cmd = i2c_cmd_link_create();
       i2c_master_start(cmd);
       i2c_master_write_byte(cmd, (addr << 1) | I2C_MASTER_WRITE, true);
       i2c_master_stop(cmd);
       
       if (i2c_master_cmd_begin(I2C_NUM_0, cmd, 50/portTICK_PERIOD_MS) == ESP_OK) {
           printf("Dispositivo encontrado en 0x%02X\n", addr);
       }
       i2c_cmd_link_delete(cmd);
   }
   ```

### Problema: "Error compilando MicroPython"

**Síntomas**:
```
fatal error: py/runtime.h: No such file or directory
```

**Soluciones**:
1. Verificar que MicroPython esté clonado en `components/micropython`
2. Ejecutar `git submodule update --init --recursive`
3. Verificar que el archivo `components/micropython/py/runtime.h` existe

### Problema: "Out of memory al ejecutar Python"

**Síntomas**:
```
RuntimeError: Out of memory
```

**Soluciones**:
1. Aumentar heap de MicroPython en `micropython_bindings.c`:
   ```c
   static uint8_t heap[256 * 1024];  // Aumentar a 256KB
   ```
2. Aumentar stack de tarea Python en `main.c`:
   ```c
   xTaskCreate(test_sensors_task_python, "test_python", 16384, NULL, 5, NULL);
   ```
3. Habilitar SPIRAM en `sdkconfig`:
   ```
   idf.py menuconfig
   → Component config → ESP32-specific → Support for external SPI RAM
   ```

### Problema: "Scripts Python no se cargan desde SPIFFS"

**Síntomas**:
```
E (5678) MAIN: Fallo al montar o formatear filesystem
```

**Soluciones**:
1. Verificar tabla de particiones `partitions.csv`
2. Flashear particiones nuevamente:
   ```powershell
   idf.py partition_table-flash
   ```
3. Formatear SPIFFS manualmente:
   ```powershell
   python $Env:IDF_PATH\components\partition_table\parttool.py -p COM3 erase_partition --partition-name storage
   ```

### Problema: "Lecturas erráticas del MAX30102"

**Síntomas**:
- Valores muy altos o muy bajos
- Valores que no cambian

**Soluciones**:
1. Asegurar buen contacto con la piel
2. No presionar demasiado fuerte (bloquea circulación)
3. Esperar 2-3 segundos para estabilización
4. Ajustar corriente de LEDs en `max30102_driver.c`:
   ```c
   // Aumentar corriente (0x24 = 6.4mA, 0x3F = 12.5mA)
   max30102_write_register(MAX30102_REG_LED1_PA, 0x3F);
   max30102_write_register(MAX30102_REG_LED2_PA, 0x3F);
   ```

### Problema: "ADXL345 siempre lee ~0g en todos los ejes"

**Síntomas**:
```
X: 0.000g, Y: 0.000g, Z: 0.000g
```

**Soluciones**:
1. Verificar que SDO esté conectado correctamente
2. Verificar modo de medición:
   ```c
   // En adxl345_init(), verificar:
   adxl345_write_register(ADXL345_REG_POWER_CTL, 0x08);  // Bit 3 = Measure mode
   ```
3. Probar con dirección alternativa (cambiar `ADXL345_I2C_ADDR` a `0x1D`)

---

## 📚 Recursos Adicionales

### Documentación
- [ESP-IDF Programming Guide](https://docs.espressif.com/projects/esp-idf/en/latest/)
- [MicroPython Documentation](https://docs.micropython.org/)
- [MAX30102 Datasheet](https://datasheets.maximintegrated.com/en/ds/MAX30102.pdf)
- [ADXL345 Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL345.pdf)

### Herramientas Útiles
- **ESPHome**: Para integración con Home Assistant
- **Thonny**: IDE Python para MicroPython
- **PlatformIO**: IDE alternativo para ESP32

### Comandos Útiles de IDF

```powershell
# Limpiar build
idf.py fullclean

# Ver configuración actual
idf.py show_efuse_table

# Borrar flash completo
idf.py erase_flash

# Compilar y flashear en un solo comando
idf.py build flash monitor

# Ver tamaño de componentes
idf.py size-components
```

---

## 🎓 Próximos Pasos

1. **Implementar algoritmos de frecuencia cardíaca** más precisos
2. **Agregar WiFi** para enviar datos a servidor
3. **Implementar MQTT** para IoT
4. **Crear interfaz web** con datos en tiempo real
5. **Agregar más sensores** (temperatura, presión, GPS)
6. **Implementar deep sleep** para ahorro de energía

---

## 📝 Notas Finales

- Siempre desconectar antes de cambiar conexiones
- No mezclar 3.3V y 5V en el mismo bus I2C
- SPIFFS es ideal para scripts pequeños (<1MB)
- Para proyectos grandes, considerar LittleFS
- MicroPython tiene overhead de memoria (~100KB)
- Para máximo rendimiento, usar solo C

---

**¡Proyecto listo para compilar y probar! 🎉**

Para cualquier duda, revisa los comentarios en el código o consulta la documentación oficial.
