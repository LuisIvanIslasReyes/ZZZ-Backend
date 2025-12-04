# 🔌 Guía de Conexiones - Configuración Actualizada

## 📊 Resumen de Sensores

### XD58C - Sensor de Pulso (Analógico)
- **Tipo**: Salida analógica (NO I2C)
- **Pines**: 3 (VCC, GND, Señal)
- **Conexión ESP32**: GPIO34 (ADC1_CH6)

### ADXL345 - Acelerómetro (I2C)
- **Tipo**: Digital I2C
- **Dirección**: 0x53
- **Conexión ESP32**: GPIO16 (SDA), GPIO17 (SCL)

---

## 🔗 Diagrama de Conexiones

```
┌────────────────────────────────────────────┐
│              ESP32 DevKit                  │
│                                            │
│  GPIO34 (ADC) ──────────┐                 │
│                          │                 │
│  GPIO16 (SDA) ───────┐  │                 │
│  GPIO17 (SCL) ───────┼──┼────────         │
│                       │  │                 │
│  3.3V  ──────────────┼──┼────────         │
│  GND   ──────────────┼──┼────────         │
│                       │  │                 │
└───────────────────────┼──┼─────────────────┘
                        │  │
         ┌──────────────┘  └──────────────┐
         │                                │
    ┌────▼─────┐                   ┌──────▼───┐
    │ ADXL345  │                   │  XD58C   │
    │          │                   │          │
    │ VCC  3.3V│                   │ VCC  3.3V│
    │ GND  GND │                   │ GND  GND │
    │ SDA  GP16│                   │ OUT  GP34│
    │ SCL  GP17│                   └──────────┘
    │ SDO  GND │ ⚠️ IMPORTANTE
    │ CS   3.3V│ ⚠️ IMPORTANTE
    └──────────┘
```

---

## 📝 Conexiones Detalladas

### XD58C (Sensor de Pulso Analógico)

| Pin XD58C | Conexión ESP32 | Descripción |
|-----------|----------------|-------------|
| VCC       | 3.3V          | Alimentación |
| GND       | GND           | Tierra |
| OUT/Signal| GPIO34        | Señal analógica (ADC1_CH6) |

**Características:**
- ✅ Salida analógica 0-3.3V
- ✅ Señal proporcional al pulso cardíaco
- ✅ Sin necesidad de protocolo de comunicación
- ✅ Lectura directa con ADC del ESP32

**Notas:**
- GPIO34 es solo entrada (input-only)
- Rango ADC: 0-4095 (12 bits)
- Se recomienda filtrado por software para ruido

### ADXL345 (Acelerómetro I2C)

| Pin ADXL345 | Conexión ESP32 | Descripción |
|-------------|----------------|-------------|
| VCC         | 3.3V          | Alimentación |
| GND         | GND           | Tierra |
| SDA         | GPIO16        | Datos I2C |
| SCL         | GPIO17        | Clock I2C |
| SDO         | GND           | ⚠️ Dirección I2C (0x53) |
| CS          | 3.3V          | ⚠️ Habilitar modo I2C |

**Características:**
- ✅ Protocolo I2C (400 kHz)
- ✅ Dirección I2C: 0x53 (SDO=GND)
- ✅ Resolución: ±2g por defecto
- ✅ Frecuencia: 100 Hz

**Notas:**
- SDO conectado a GND = dirección 0x53
- SDO conectado a 3.3V = dirección 0x1D
- CS debe estar en HIGH (3.3V) para modo I2C

---

## ⚙️ Configuración en Código

### XD58C (ADC)

**Header (`xd58c_driver.h`):**
```c
#define XD58C_ADC_CHANNEL ADC1_CHANNEL_6  // GPIO34
#define XD58C_ADC_WIDTH   ADC_WIDTH_BIT_12
#define XD58C_ADC_ATTEN   ADC_ATTEN_DB_11  // Rango 0-3.3V
```

**Funciones disponibles:**
```c
esp_err_t xd58c_init(void);                    // Inicializar ADC
esp_err_t xd58c_read_analog(uint32_t *value);  // Leer valor ADC (0-4095)
esp_err_t xd58c_read_voltage(uint32_t *mv);    // Leer voltaje (0-3300 mV)
```

### ADXL345 (I2C)

**Header (`adxl345_driver.h`):**
```c
#define I2C_MASTER_SDA_IO      16  // GPIO16
#define I2C_MASTER_SCL_IO      17  // GPIO17
#define ADXL345_I2C_ADDR       0x53
```

**Funciones disponibles:**
```c
esp_err_t adxl345_i2c_init(void);              // Inicializar bus I2C
esp_err_t adxl345_init(void);                  // Inicializar sensor
esp_err_t adxl345_read_accel(adxl345_accel_t*); // Leer aceleración
esp_err_t adxl345_calibrate(void);             // Calibrar sensor
```

---

## 🐍 Uso desde Python (MicroPython)

### XD58C

```python
import sensors

# Inicializar
sensors.xd58c_init()

# Leer valor ADC (0-4095)
adc_value = sensors.xd58c_read()
print(f"Valor ADC: {adc_value}")

# Leer voltaje en mV (0-3300)
voltage = sensors.xd58c_voltage()
print(f"Voltaje: {voltage}mV")

# Normalizar a porcentaje
pulse_percent = (adc_value / 4095) * 100
print(f"Señal: {pulse_percent:.1f}%")
```

### ADXL345

```python
import sensors

# Inicializar
sensors.adxl345_init()

# Calibrar (sensor en superficie plana)
sensors.adxl345_calibrate()

# Leer aceleración
x, y, z = sensors.adxl345_read()
print(f"X: {x:.3f}g, Y: {y:.3f}g, Z: {z:.3f}g")

# Calcular magnitud
import math
magnitude = math.sqrt(x**2 + y**2 + z**2)
print(f"Magnitud: {magnitude:.3f}g")
```

---

## 🔍 Verificación de Conexiones

### Escanear Bus I2C

Agregar este código en `main.c` para verificar dispositivos I2C:

```c
void scan_i2c_bus(void) {
    ESP_LOGI(TAG, "Escaneando bus I2C...");
    
    for (uint8_t addr = 1; addr < 127; addr++) {
        i2c_cmd_handle_t cmd = i2c_cmd_link_create();
        i2c_master_start(cmd);
        i2c_master_write_byte(cmd, (addr << 1) | I2C_MASTER_WRITE, true);
        i2c_master_stop(cmd);
        
        esp_err_t ret = i2c_master_cmd_begin(I2C_NUM_0, cmd, 50 / portTICK_PERIOD_MS);
        i2c_cmd_link_delete(cmd);
        
        if (ret == ESP_OK) {
            ESP_LOGI(TAG, "Dispositivo I2C encontrado en 0x%02X", addr);
        }
    }
    
    ESP_LOGI(TAG, "Escaneo completado");
}
```

**Salida esperada:**
```
I (1234) MAIN: Dispositivo I2C encontrado en 0x53  ← ADXL345
```

### Probar ADC del XD58C

```c
void test_xd58c_adc(void) {
    uint32_t adc_value, voltage_mv;
    
    xd58c_read_analog(&adc_value);
    xd58c_read_voltage(&voltage_mv);
    
    ESP_LOGI(TAG, "XD58C -> ADC: %lu, Voltaje: %lu mV", adc_value, voltage_mv);
}
```

**Salida esperada (sin dedo en el sensor):**
```
I (2000) MAIN: XD58C -> ADC: 2048, Voltaje: 1650 mV
```

**Salida esperada (con dedo en el sensor):**
```
I (2000) MAIN: XD58C -> ADC: 2500-3000 (varía con pulso), Voltaje: 2000-2400 mV
```

---

## 🛠️ Solución de Problemas

### ❌ "ADXL345 no responde"

**Verificar:**
1. ✅ SDA en GPIO16, SCL en GPIO17
2. ✅ SDO conectado a GND (dirección 0x53)
3. ✅ CS conectado a 3.3V (modo I2C)
4. ✅ Resistencias pull-up de 4.7kΩ en SDA/SCL
5. ✅ Escanear bus I2C para confirmar dirección

**Comando:**
```c
scan_i2c_bus();  // Debe mostrar 0x53
```

### ❌ "XD58C siempre lee el mismo valor"

**Verificar:**
1. ✅ Pin OUT del sensor conectado a GPIO34
2. ✅ VCC en 3.3V (NO 5V)
3. ✅ Sensor detecta pulso (colocar dedo suavemente)
4. ✅ GPIO34 es un pin ADC válido

**Probar:**
```python
import sensors
sensors.xd58c_init()

# Leer 10 veces
for i in range(10):
    adc = sensors.xd58c_read()
    print(f"Lectura {i+1}: {adc}")
    time.sleep(0.5)
```

**Debe variar** si hay pulso detectado (ej: 2000-3500).

### ❌ "Lecturas del XD58C muy ruidosas"

**Solución 1 - Promediar en software:**

Ya implementado en el driver:
```c
#define XD58C_ADC_SAMPLES 10  // Promedio de 10 muestras
```

**Solución 2 - Filtro paso-bajo en Python:**

```python
def filtro_paso_bajo(valores, alpha=0.3):
    """Filtro exponencial"""
    if len(valores) < 2:
        return valores[-1]
    return alpha * valores[-1] + (1 - alpha) * valores[-2]
```

### ❌ "I2C error (bus busy)"

**Posibles causas:**
1. Cables I2C muy largos (>30cm)
2. Sin resistencias pull-up
3. Múltiples dispositivos sin direcciones únicas

**Solución:**
1. Acortar cables
2. Agregar resistencias pull-up de 4.7kΩ
3. Verificar que solo haya un ADXL345

---

## 📊 Valores Típicos

### XD58C (Sin dedo)
- ADC: ~2048 (centro del rango)
- Voltaje: ~1650 mV

### XD58C (Con dedo, pulso normal 60-100 BPM)
- ADC: 2000-3500 (varía con pulsación)
- Voltaje: 1600-2800 mV
- Frecuencia: ~1 Hz (60 BPM)

### ADXL345 (Reposo, sensor horizontal)
- X: ~0.00g ±0.05g
- Y: ~0.00g ±0.05g
- Z: ~1.00g ±0.05g (gravedad)

### ADXL345 (Movimiento)
- Sacudida suave: ±0.5g
- Golpe: ±2g
- Caída libre: ~0g en todos los ejes

---

## 🚀 Ejemplo Completo

```c
void app_main(void) {
    // Inicializar XD58C (ADC)
    ESP_ERROR_CHECK(xd58c_init());
    
    // Inicializar I2C
    ESP_ERROR_CHECK(adxl345_i2c_init());
    
    // Inicializar ADXL345
    ESP_ERROR_CHECK(adxl345_init());
    
    // Calibrar acelerómetro
    adxl345_calibrate();
    
    // Loop de lectura
    while (1) {
        // Leer XD58C
        uint32_t adc, voltage;
        xd58c_read_analog(&adc);
        xd58c_read_voltage(&voltage);
        ESP_LOGI(TAG, "XD58C: ADC=%lu, V=%lumV", adc, voltage);
        
        // Leer ADXL345
        adxl345_accel_t accel;
        adxl345_read_accel(&accel);
        ESP_LOGI(TAG, "ADXL345: X=%.3fg, Y=%.3fg, Z=%.3fg", 
                 accel.x, accel.y, accel.z);
        
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}
```

---

## 📚 Referencias

- **ESP32 ADC**: [ESP-IDF ADC Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/adc.html)
- **ESP32 I2C**: [ESP-IDF I2C Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/i2c.html)
- **ADXL345 Datasheet**: [Analog Devices](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL345.pdf)

---

**¡Configuración lista! 🎉**

Pines configurados:
- ✅ XD58C: GPIO34 (ADC)
- ✅ ADXL345: GPIO16 (SDA), GPIO17 (SCL)
