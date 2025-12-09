#ifndef XD58C_DRIVER_H
#define XD58C_DRIVER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"

// Pin analógico del XD58C
#define XD58C_ADC_CHANNEL ADC_CHANNEL_6  // GPIO34
#define XD58C_ADC_UNIT    ADC_UNIT_1

// Configuración ADC
#define XD58C_ADC_ATTEN         ADC_ATTEN_DB_12  // Rango 0-3.3V (nuevo en v5.x)
#define XD58C_ADC_BITWIDTH      ADC_BITWIDTH_12
#define XD58C_ADC_SAMPLES       10  // Número de muestras para promedio

// Configuración AUTO-CALIBRADA (se adapta a luz ambiente)
// El sensor XD58C es una fotoresistencia que varía con:
// - Luz ambiente (afecta baseline)
// - Presión del dedo (afecta amplitud)
// - Flujo sanguíneo (crea pulsos)
#define XD58C_CALIBRATION_TIME_MS   10000  // 10 segundos de calibración inicial
#define XD58C_MIN_RANGE_MV          30    // Rango mínimo para detección válida (REDUCIDO)
#define XD58C_BASELINE_SAMPLES      50    // Muestras para baseline adaptativo
#define XD58C_SAMPLE_WINDOW         5000  // Ventana de 5 segundos para calcular BPM
#define XD58C_MIN_BPM               40    // BPM mínimo válido
#define XD58C_MAX_BPM               180   // BPM máximo válido
#define XD58C_MIN_SIGNAL_CHANGE     10    // Cambio mínimo en mV para detectar dedo (10mV)

/**
 * @brief Estructura para algoritmo adaptativo de detección de pulso
 */
typedef struct {
    uint32_t bpm;              // Pulsaciones por minuto (promedio de ventana de 5s)
    
    // Baseline adaptativo (promedio móvil de 50 muestras)
    int baseline;              // Promedio actual
    int baseline_buffer[XD58C_BASELINE_SAMPLES];
    uint8_t baseline_index;
    uint32_t baseline_sum;
    
    // Detección de dedo y pulsos
    bool finger_detected;      // true si señal > 2000 mV
    bool last_peak_state;      // Estado anterior del pico
    uint32_t last_peak_time;   // Timestamp del último pulso detectado (ms)
    
    // Ventana de 5 segundos para BPM
    uint32_t intervals_sum;    // Suma de intervalos entre pulsos
    uint8_t intervals_count;   // Cantidad de intervalos válidos
    uint32_t window_start;     // Inicio de ventana (ms)
    uint8_t peaks_count;       // Total de picos detectados
    
    // Estadísticas para umbral dinámico
    int min_signal;            // Señal mínima en ventana
    int max_signal;            // Señal máxima en ventana
    
    // AUTO-CALIBRACIÓN
    bool calibration_done;     // true cuando calibración completa
    uint32_t calibration_start;// Timestamp inicio calibración
    int calibration_samples;   // Muestras recolectadas
    int ambient_baseline;      // Baseline del ambiente (sin dedo)
    int signal_with_finger;    // Señal con dedo puesto
    bool auto_threshold;       // Usar umbral automático
} xd58c_heartrate_t;

/**
 * @brief Inicializa el ADC para el sensor XD58C
 * @return ESP_OK si la inicialización fue exitosa
 */
esp_err_t xd58c_init(void);

/**
 * @brief Lee el valor analógico del sensor (señal de pulso)
 * @param value Puntero para almacenar el valor ADC (0-4095)
 * @return ESP_OK si la lectura fue exitosa
 */
esp_err_t xd58c_read_analog(uint32_t *value);

/**
 * @brief Lee el valor analógico en mV
 * @param voltage_mv Puntero para almacenar el voltaje en mV
 * @return ESP_OK si la lectura fue exitosa
 */
esp_err_t xd58c_read_voltage(uint32_t *voltage_mv);

/**
 * @brief Inicializa la estructura de detección de ritmo cardíaco
 * @param hr Puntero a la estructura xd58c_heartrate_t
 */
void xd58c_heartrate_init(xd58c_heartrate_t *hr);

/**
 * @brief Procesa una muestra de voltaje y detecta picos (latidos)
 * @param hr Puntero a la estructura xd58c_heartrate_t
 * @param voltage_mv Voltaje actual en mV
 * @param current_time_ms Timestamp actual en ms (usar xTaskGetTickCount() * portTICK_PERIOD_MS)
 * @return true si se detectó un latido, false en caso contrario
 */
bool xd58c_heartrate_process(xd58c_heartrate_t *hr, uint32_t voltage_mv, uint32_t current_time_ms);

/**
 * @brief Obtiene el BPM calculado (promedio de ventana de 5 segundos)
 * @param hr Puntero a la estructura xd58c_heartrate_t
 * @param current_time_ms Timestamp actual en ms
 * @return BPM promedio (0 si no hay suficientes muestras)
 */
uint32_t xd58c_heartrate_get_bpm(xd58c_heartrate_t *hr, uint32_t current_time_ms);

#endif // XD58C_DRIVER_H
