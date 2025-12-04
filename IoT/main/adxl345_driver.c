#include "adxl345_driver.h"
#include "driver/i2c.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <math.h>

static const char *TAG = "ADXL345";

// Escribe un byte en un registro del ADXL345
static esp_err_t adxl345_write_register(uint8_t reg_addr, uint8_t data) {
    uint8_t write_buf[2] = {reg_addr, data};
    return i2c_master_write_to_device(I2C_MASTER_NUM, ADXL345_I2C_ADDR, 
                                      write_buf, sizeof(write_buf), 
                                      I2C_MASTER_TIMEOUT_MS / portTICK_PERIOD_MS);
}

// Lee un byte de un registro del ADXL345
static esp_err_t adxl345_read_register(uint8_t reg_addr, uint8_t *data) {
    return i2c_master_write_read_device(I2C_MASTER_NUM, ADXL345_I2C_ADDR,
                                       &reg_addr, 1, data, 1,
                                       I2C_MASTER_TIMEOUT_MS / portTICK_PERIOD_MS);
}

// Lee múltiples bytes desde un registro
static esp_err_t adxl345_read_registers(uint8_t reg_addr, uint8_t *data, size_t len) {
    return i2c_master_write_read_device(I2C_MASTER_NUM, ADXL345_I2C_ADDR,
                                       &reg_addr, 1, data, len,
                                       I2C_MASTER_TIMEOUT_MS / portTICK_PERIOD_MS);
}

esp_err_t adxl345_i2c_init(void) {
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    
    esp_err_t err = i2c_param_config(I2C_MASTER_NUM, &conf);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error configurando I2C: %s", esp_err_to_name(err));
        return err;
    }
    
    err = i2c_driver_install(I2C_MASTER_NUM, conf.mode, 
                            I2C_MASTER_RX_BUF_DISABLE, 
                            I2C_MASTER_TX_BUF_DISABLE, 0);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error instalando driver I2C: %s", esp_err_to_name(err));
        return err;
    }
    
    ESP_LOGI(TAG, "I2C inicializado correctamente en GPIO16 (SDA) y GPIO17 (SCL)");
    return ESP_OK;
}

esp_err_t adxl345_init(void) {
    esp_err_t err;
    uint8_t device_id;
    
    // Verificar ID del dispositivo
    err = adxl345_read_register(ADXL345_REG_DEVID, &device_id);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error leyendo DEVICE_ID");
        return err;
    }
    
    ESP_LOGI(TAG, "ADXL345 detectado - DEVICE_ID: 0x%02X", device_id);
    
    if (device_id != ADXL345_DEVICE_ID) {
        ESP_LOGE(TAG, "DEVICE_ID no coincide con ADXL345 (esperado: 0x%02X)", ADXL345_DEVICE_ID);
        return ESP_FAIL;
    }
    
    // Configurar Data Format: Full resolution, ±2g
    err = adxl345_write_register(ADXL345_REG_DATA_FORMAT, 0x08);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error configurando DATA_FORMAT");
        return err;
    }
    
    // Configurar BW_RATE: 100Hz
    err = adxl345_write_register(ADXL345_REG_BW_RATE, 0x0A);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error configurando BW_RATE");
        return err;
    }
    
    // Habilitar modo de medición
    err = adxl345_write_register(ADXL345_REG_POWER_CTL, 0x08);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error configurando POWER_CTL");
        return err;
    }
    
    vTaskDelay(pdMS_TO_TICKS(10));
    
    ESP_LOGI(TAG, "ADXL345 inicializado correctamente");
    return ESP_OK;
}

esp_err_t adxl345_read_accel_raw(int16_t *x, int16_t *y, int16_t *z) {
    esp_err_t err;
    uint8_t data[6];
    
    // Leer 6 bytes comenzando desde DATAX0
    err = adxl345_read_registers(ADXL345_REG_DATAX0, data, 6);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error leyendo datos de aceleración");
        return err;
    }
    
    // Combinar bytes (little-endian)
    *x = (int16_t)((data[1] << 8) | data[0]);
    *y = (int16_t)((data[3] << 8) | data[2]);
    *z = (int16_t)((data[5] << 8) | data[4]);
    
    return ESP_OK;
}

esp_err_t adxl345_read_accel(adxl345_accel_t *accel) {
    int16_t x_raw, y_raw, z_raw;
    
    esp_err_t err = adxl345_read_accel_raw(&x_raw, &y_raw, &z_raw);
    if (err != ESP_OK) {
        return err;
    }
    
    // Convertir valores raw a g (usando escala de ±2g)
    accel->x = x_raw * ADXL345_SCALE_MULTIPLIER;
    accel->y = y_raw * ADXL345_SCALE_MULTIPLIER;
    accel->z = z_raw * ADXL345_SCALE_MULTIPLIER;
    
    return ESP_OK;
}

esp_err_t adxl345_calibrate(void) {
    esp_err_t err;
    int32_t sum_x = 0, sum_y = 0, sum_z = 0;
    const int samples = 100;
    
    ESP_LOGI(TAG, "Iniciando calibración... Mantén el sensor quieto");
    
    // Tomar múltiples muestras
    for (int i = 0; i < samples; i++) {
        int16_t x, y, z;
        err = adxl345_read_accel_raw(&x, &y, &z);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Error durante calibración");
            return err;
        }
        
        sum_x += x;
        sum_y += y;
        sum_z += z;
        
        vTaskDelay(pdMS_TO_TICKS(10));
    }
    
    // Calcular promedios
    int16_t avg_x = sum_x / samples;
    int16_t avg_y = sum_y / samples;
    int16_t avg_z = sum_z / samples;
    
    // El eje Z debería leer aproximadamente 256 (1g en escala ±2g)
    // Ajustar offset para compensar la gravedad
    int8_t offset_x = -avg_x / 4;  // Los offsets tienen resolución de 15.6mg (4 LSB)
    int8_t offset_y = -avg_y / 4;
    int8_t offset_z = -(avg_z - 256) / 4;
    
    // Escribir offsets
    err = adxl345_write_register(ADXL345_REG_OFSX, (uint8_t)offset_x);
    if (err != ESP_OK) return err;
    
    err = adxl345_write_register(ADXL345_REG_OFSY, (uint8_t)offset_y);
    if (err != ESP_OK) return err;
    
    err = adxl345_write_register(ADXL345_REG_OFSZ, (uint8_t)offset_z);
    if (err != ESP_OK) return err;
    
    ESP_LOGI(TAG, "Calibración completada - Offsets: X=%d, Y=%d, Z=%d", offset_x, offset_y, offset_z);
    
    return ESP_OK;
}
