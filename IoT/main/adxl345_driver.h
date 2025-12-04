#ifndef ADXL345_DRIVER_H
#define ADXL345_DRIVER_H

#include <stdint.h>
#include "driver/i2c.h"

// Dirección I2C del ADXL345 (con SDO conectado a GND)
#define ADXL345_I2C_ADDR 0x53

// Registros principales
#define ADXL345_REG_DEVID           0x00
#define ADXL345_REG_THRESH_TAP      0x1D
#define ADXL345_REG_OFSX            0x1E
#define ADXL345_REG_OFSY            0x1F
#define ADXL345_REG_OFSZ            0x20
#define ADXL345_REG_DUR             0x21
#define ADXL345_REG_LATENT          0x22
#define ADXL345_REG_WINDOW          0x23
#define ADXL345_REG_THRESH_ACT      0x24
#define ADXL345_REG_THRESH_INACT    0x25
#define ADXL345_REG_TIME_INACT      0x26
#define ADXL345_REG_ACT_INACT_CTL   0x27
#define ADXL345_REG_THRESH_FF       0x28
#define ADXL345_REG_TIME_FF         0x29
#define ADXL345_REG_TAP_AXES        0x2A
#define ADXL345_REG_ACT_TAP_STATUS  0x2B
#define ADXL345_REG_BW_RATE         0x2C
#define ADXL345_REG_POWER_CTL       0x2D
#define ADXL345_REG_INT_ENABLE      0x2E
#define ADXL345_REG_INT_MAP         0x2F
#define ADXL345_REG_INT_SOURCE      0x30
#define ADXL345_REG_DATA_FORMAT     0x31
#define ADXL345_REG_DATAX0          0x32
#define ADXL345_REG_DATAX1          0x33
#define ADXL345_REG_DATAY0          0x34
#define ADXL345_REG_DATAY1          0x35
#define ADXL345_REG_DATAZ0          0x36
#define ADXL345_REG_DATAZ1          0x37
#define ADXL345_REG_FIFO_CTL        0x38
#define ADXL345_REG_FIFO_STATUS     0x39

// Configuración I2C
#define I2C_MASTER_NUM         I2C_NUM_0
#define I2C_MASTER_SDA_IO      16  // GPIO16
#define I2C_MASTER_SCL_IO      17  // GPIO17
#define I2C_MASTER_FREQ_HZ     100000
#define I2C_MASTER_TX_BUF_DISABLE 0
#define I2C_MASTER_RX_BUF_DISABLE 0
#define I2C_MASTER_TIMEOUT_MS  1000

// Constantes
#define ADXL345_DEVICE_ID           0xE5
#define ADXL345_SCALE_MULTIPLIER    0.0039  // Escala para rango ±2g (3.9mg/LSB)

// Estructura para almacenar datos de aceleración
typedef struct {
    float x;  // Aceleración en eje X (en g)
    float y;  // Aceleración en eje Y (en g)
    float z;  // Aceleración en eje Z (en g)
} adxl345_accel_t;

/**
 * @brief Inicializa el bus I2C
 * @return ESP_OK si la inicialización fue exitosa
 */
esp_err_t adxl345_i2c_init(void);

/**
 * @brief Inicializa el sensor ADXL345
 * @return ESP_OK si la inicialización fue exitosa
 */
esp_err_t adxl345_init(void);

/**
 * @brief Lee los datos de aceleración del sensor
 * @param accel Estructura para almacenar los datos de aceleración
 * @return ESP_OK si la lectura fue exitosa
 */
esp_err_t adxl345_read_accel(adxl345_accel_t *accel);

/**
 * @brief Lee los datos RAW de aceleración (valores enteros sin escalar)
 * @param x Puntero para almacenar aceleración X raw
 * @param y Puntero para almacenar aceleración Y raw
 * @param z Puntero para almacenar aceleración Z raw
 * @return ESP_OK si la lectura fue exitosa
 */
esp_err_t adxl345_read_accel_raw(int16_t *x, int16_t *y, int16_t *z);

/**
 * @brief Calibra el sensor (ajusta offsets)
 * @return ESP_OK si la calibración fue exitosa
 */
esp_err_t adxl345_calibrate(void);

#endif // ADXL345_DRIVER_H
