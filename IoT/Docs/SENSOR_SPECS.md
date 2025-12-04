# 📊 Especificaciones Técnicas de Sensores

## XD58C - Sensor de Pulso Analógico

### Características Principales
- **Tipo**: Sensor óptico de frecuencia cardíaca con salida analógica
- **Interfaz**: ⚠️ **Salida analógica DC (NO I2C)**
- **Voltaje**: 3.3V-5V (usar 3.3V con ESP32)
- **Corriente**: ~20mA típico
- **Pines**: 3 (VCC, GND, OUT/Signal)

### Especificaciones Técnicas

| Parámetro | Valor |
|-----------|-------|
| Interfaz | **Analógica** (0-3.3V) |
| Conexión ESP32 | **GPIO34** (ADC1_CH6) |
| Tipo de salida | Voltaje proporcional al pulso |
| Rango de voltaje | 0-3.3V |
| Frecuencia cardíaca | 30-240 BPM |
| LED emisor | Rojo (~660nm) o verde (~525nm) |
| Fotodetector | Fotodiodo |

### Configuración del ADC en ESP32

```c
#define XD58C_ADC_CHANNEL ADC1_CHANNEL_6    // GPIO34
#define XD58C_ADC_WIDTH   ADC_WIDTH_BIT_12  // 12 bits (0-4095)
#define XD58C_ADC_ATTEN   ADC_ATTEN_DB_11   // Rango 0-3.3V
#define XD58C_ADC_SAMPLES 10                // Muestras para promediar
```

### Inicialización del ADC

```c
// Configurar canal ADC
adc1_config_width(ADC_WIDTH_BIT_12);
adc1_config_channel_atten(ADC1_CHANNEL_6, ADC_ATTEN_DB_11);

// Calibrar ADC para voltaje
esp_adc_cal_characteristics_t adc_chars;
esp_adc_cal_characterize(ADC_UNIT_1, ADC_ATTEN_DB_11, 
                         ADC_WIDTH_BIT_12, 1100, &adc_chars);
```

### Lectura de Datos

**Lectura de valor ADC (0-4095)**:
```c
uint32_t adc_value = 0;
for (int i = 0; i < XD58C_ADC_SAMPLES; i++) {
    adc_value += adc1_get_raw(XD58C_ADC_CHANNEL);
}
adc_value /= XD58C_ADC_SAMPLES;  // Promedio
```

**Conversión a voltaje (mV)**:
```c
uint32_t voltage = esp_adc_cal_raw_to_voltage(adc_value, &adc_chars);
```

### Valores Típicos

| Condición | Valor ADC | Voltaje (mV) | Observación |
|-----------|-----------|--------------|-------------|
| Sin contacto | ~2048 | ~1650 | Centro del rango |
| Dedo sin pulso | 1800-2200 | 1450-1800 | Línea base |
| Pico sistólico | 2800-3500 | 2250-2800 | Máximo durante latido |
| Valle diastólico | 2000-2500 | 1600-2000 | Mínimo entre latidos |

### Detección de Frecuencia Cardíaca

**Algoritmo básico**:
1. **Filtrado**: Promediar 10+ muestras para reducir ruido
2. **Detección de picos**: 
   ```c
   if (current > threshold && current > previous && current > next) {
       // Pico detectado
   }
   ```
3. **Cálculo de BPM**:
   ```c
   uint32_t interval_ms = current_time - last_peak_time;
   uint32_t bpm = 60000 / interval_ms;
   ```
4. **Validación**: Aceptar solo BPM entre 30-240

**Filtro paso-bajo** (opcional):
```c
float filtered = alpha * current + (1 - alpha) * previous;
// alpha = 0.3 para filtrado suave
```

### Calibración

**Valores de referencia**:
```c
// Leer línea base (sin dedo)
uint32_t baseline = xd58c_read_analog();  // ~2048

// Definir umbral para detección de pico
uint32_t threshold = baseline + 400;  // +400 ADC counts
```

### Aplicaciones
- Monitores de fitness simples
- Medición de frecuencia cardíaca
- Detección de presencia de pulso
- Proyectos educativos/DIY

### ⚠️ Limitaciones
- No mide SpO2 (solo un LED)
- Sensible a movimiento
- Requiere buen contacto con la piel
- No certificado para uso médico

### 💡 Consejos de Uso
1. ✅ Colocar dedo suavemente (no presionar fuerte)
2. ✅ Mantener dedo quieto durante medición
3. ✅ Esperar 2-3 segundos para estabilizar
4. ✅ Usar filtrado por software
5. ✅ Promediar múltiples lecturas

---

## ADXL345 - Acelerómetro de 3 Ejes

### Características Principales
- **Fabricante**: Analog Devices
- **Tipo**: Acelerómetro MEMS de 3 ejes
- **Interfaz**: I2C (hasta 400 kHz) o SPI (hasta 5 MHz)
- **Voltaje**: 2.0-3.6V
- **Corriente**: 40µA en medición, 0.1µA en standby

### Especificaciones Técnicas

| Parámetro | Valor |
|-----------|-------|
| Dirección I2C (SDO=0) | 0x53 ← **Usado en este proyecto** |
| Dirección I2C (SDO=1) | 0x1D |
| **Pin SDA (ESP32)** | ⚠️ **GPIO16** (personalizado) |
| **Pin SCL (ESP32)** | ⚠️ **GPIO17** (personalizado) |
| Resolución | 10-13 bits (según rango) |
| Rango | ±2g, ±4g, ±8g, ±16g |
| Sensibilidad (±2g) | 3.9 mg/LSB |
| Frecuencia de salida | 0.1 - 3200 Hz |
| FIFO | 32 niveles |
| Temperatura de operación | -40°C a +85°C |

### Registros Importantes

```c
#define ADXL345_REG_DEVID           0x00  // ID del dispositivo (0xE5)
#define ADXL345_REG_POWER_CTL       0x2D  // Control de energía
#define ADXL345_REG_DATA_FORMAT     0x31  // Formato de datos
#define ADXL345_REG_BW_RATE         0x2C  // Frecuencia de muestreo
#define ADXL345_REG_DATAX0          0x32  // Datos X (LSB)
#define ADXL345_REG_DATAX1          0x33  // Datos X (MSB)
#define ADXL345_REG_DATAY0          0x34  // Datos Y (LSB)
#define ADXL345_REG_DATAY1          0x35  // Datos Y (MSB)
#define ADXL345_REG_DATAZ0          0x36  // Datos Z (LSB)
#define ADXL345_REG_DATAZ1          0x37  // Datos Z (MSB)
```

### Modos de Medición

**Configuración de Rango** (DATA_FORMAT register):

| Valor | Rango | Sensibilidad |
|-------|-------|--------------|
| 0x00  | ±2g   | 3.9 mg/LSB ← **Usado** |
| 0x01  | ±4g   | 7.8 mg/LSB |
| 0x02  | ±8g   | 15.6 mg/LSB |
| 0x03  | ±16g  | 31.2 mg/LSB |

**Frecuencias de Muestreo** (BW_RATE register):

| Valor | Frecuencia |
|-------|------------|
| 0x07  | 12.5 Hz |
| 0x08  | 25 Hz |
| 0x09  | 50 Hz |
| 0x0A  | 100 Hz ← **Usado** |
| 0x0B  | 200 Hz |
| 0x0C  | 400 Hz |
| 0x0D  | 800 Hz |
| 0x0E  | 1600 Hz |
| 0x0F  | 3200 Hz |

### Configuración I2C Personalizada

⚠️ **Este proyecto usa pines I2C NO estándar**:

```c
#define I2C_MASTER_SDA_IO    16     // GPIO16 (en lugar de GPIO21)
#define I2C_MASTER_SCL_IO    17     // GPIO17 (en lugar de GPIO22)
#define I2C_MASTER_FREQ_HZ   100000 // 100 kHz

// Inicializar bus I2C personalizado
esp_err_t adxl345_i2c_init(void) {
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    
    ESP_ERROR_CHECK(i2c_param_config(I2C_NUM_0, &conf));
    ESP_ERROR_CHECK(i2c_driver_install(I2C_NUM_0, conf.mode, 0, 0, 0));
    
    return ESP_OK;
}
```

### Configuración del Sensor

```c
// Modo de resolución completa, rango ±2g
adxl345_write_register(ADXL345_REG_DATA_FORMAT, 0x08);

// Frecuencia de muestreo: 100 Hz
adxl345_write_register(ADXL345_REG_BW_RATE, 0x0A);

// Habilitar modo de medición
adxl345_write_register(ADXL345_REG_POWER_CTL, 0x08);
```

### Lectura de Datos

Los datos se almacenan en formato **little-endian** (LSB primero):

```c
// Leer 6 bytes (X, Y, Z)
uint8_t data[6];
adxl345_read_registers(ADXL345_REG_DATAX0, data, 6);

// Combinar bytes
int16_t x = (int16_t)((data[1] << 8) | data[0]);
int16_t y = (int16_t)((data[3] << 8) | data[2]);
int16_t z = (int16_t)((data[5] << 8) | data[4]);

// Convertir a g
float x_g = x * 0.0039f;  // Para rango ±2g
float y_g = y * 0.0039f;
float z_g = z * 0.0039f;
```

### Calibración

El ADXL345 tiene registros de offset para calibración:

```c
#define ADXL345_REG_OFSX  0x1E  // Offset X
#define ADXL345_REG_OFSY  0x1F  // Offset Y
#define ADXL345_REG_OFSZ  0x20  // Offset Z
```

**Proceso de calibración**:
1. Colocar sensor en superficie plana
2. Tomar 100+ muestras
3. Calcular promedio
4. Escribir offset = -promedio / 4
5. El eje Z debería leer ~1g (gravedad)

### Aplicaciones
- Detección de orientación
- Detección de caídas
- Podómetros
- Control de gestos
- Monitoreo de vibración
- Sistemas de seguridad

### Eventos Detectables

El ADXL345 puede generar interrupciones para:
- **Activity**: Movimiento detectado
- **Inactivity**: Sin movimiento
- **Tap**: Golpe simple
- **Double Tap**: Golpe doble
- **Free Fall**: Caída libre

---

## 🔌 Conexión I2C Compartida

Ambos sensores pueden compartir el mismo bus I2C:

```
ESP32 (SDA, SCL) ───┬─── MAX30102 (0x57)
                    └─── ADXL345 (0x53)
```

### Ventajas del Bus Compartido
✅ Solo usa 2 pines GPIO  
✅ Comunicación simultánea (dirección única)  
✅ Fácil escalabilidad (agregar más sensores)  

### Consideraciones
- Usar resistencias pull-up de 4.7kΩ en SDA y SCL
- Mantener cables cortos (<30cm recomendado)
- Velocidad máxima: 400 kHz (Fast Mode)
- Verificar niveles de voltaje compatibles (3.3V)

---

## 📈 Comparativa de Rendimiento

| Característica | MAX30102 | ADXL345 |
|----------------|----------|---------|
| Frecuencia max | 3200 Hz | 3200 Hz |
| Corriente | 600 µA | 40 µA |
| Resolución | 18 bits | 13 bits |
| Tamaño datos | 6 bytes/lectura | 6 bytes/lectura |
| FIFO | 32 muestras | 32 muestras |
| Tiempo inicio | ~100 ms | ~10 ms |

---

## 🧮 Fórmulas Útiles

### MAX30102

**Frecuencia de Muestreo Real**:
```
fs = 1000000 / (SPO2_SR * LED_PW * ADC_RANGE)
```

**Tamaño de Muestra**:
```
bytes = num_samples * 3 * num_leds  // 3 bytes por LED
```

### ADXL345

**Magnitud de Aceleración**:
```
magnitude = sqrt(x² + y² + z²)
```

**Ángulo de Inclinación**:
```
pitch = atan2(x, sqrt(y² + z²))
roll = atan2(y, sqrt(x² + z²))
```

**Detección de Caída Libre**:
```
if (magnitude < 0.5g) → Caída libre
```

---

## 📚 Referencias

- [MAX30102 Datasheet](https://datasheets.maximintegrated.com/en/ds/MAX30102.pdf)
- [ADXL345 Datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL345.pdf)
- [ESP32 I2C Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/i2c.html)
