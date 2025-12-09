#include "xd58c_driver.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

static const char *TAG = "XD58C";
static adc_oneshot_unit_handle_t adc1_handle = NULL;
static adc_cali_handle_t adc1_cali_handle = NULL;

esp_err_t xd58c_init(void) {
    esp_err_t err;
    
    // Configurar ADC1 oneshot
    adc_oneshot_unit_init_cfg_t init_config1 = {
        .unit_id = XD58C_ADC_UNIT,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    
    err = adc_oneshot_new_unit(&init_config1, &adc1_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error creando unidad ADC: %s", esp_err_to_name(err));
        return err;
    }
    
    // Configurar canal
    adc_oneshot_chan_cfg_t config = {
        .bitwidth = XD58C_ADC_BITWIDTH,
        .atten = XD58C_ADC_ATTEN,
    };
    
    err = adc_oneshot_config_channel(adc1_handle, XD58C_ADC_CHANNEL, &config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error configurando canal ADC: %s", esp_err_to_name(err));
        return err;
    }
    
    // Calibración ADC
    adc_cali_line_fitting_config_t cali_config = {
        .unit_id = XD58C_ADC_UNIT,
        .atten = XD58C_ADC_ATTEN,
        .bitwidth = XD58C_ADC_BITWIDTH,
    };
    
    err = adc_cali_create_scheme_line_fitting(&cali_config, &adc1_cali_handle);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "ADC calibrado correctamente");
    } else {
        ESP_LOGW(TAG, "Calibración no disponible, usando valores raw");
        adc1_cali_handle = NULL;
    }
    
    ESP_LOGI(TAG, "XD58C inicializado en GPIO34 (ADC1_CH6)");
    return ESP_OK;
}

esp_err_t xd58c_read_analog(uint32_t *value) {
    if (value == NULL) {
        ESP_LOGE(TAG, "Puntero nulo");
        return ESP_ERR_INVALID_ARG;
    }
    
    if (adc1_handle == NULL) {
        ESP_LOGE(TAG, "ADC no inicializado");
        return ESP_ERR_INVALID_STATE;
    }
    
    // Tomar múltiples muestras y promediar
    uint32_t sum = 0;
    int adc_raw;
    
    for (int i = 0; i < XD58C_ADC_SAMPLES; i++) {
        esp_err_t err = adc_oneshot_read(adc1_handle, XD58C_ADC_CHANNEL, &adc_raw);
        if (err == ESP_OK) {
            sum += adc_raw;
        }
        vTaskDelay(pdMS_TO_TICKS(1));
    }
    
    *value = sum / XD58C_ADC_SAMPLES;
    return ESP_OK;
}

esp_err_t xd58c_read_voltage(uint32_t *voltage_mv) {
    if (voltage_mv == NULL) {
        ESP_LOGE(TAG, "Puntero nulo");
        return ESP_ERR_INVALID_ARG;
    }
    
    // Leer valor ADC
    uint32_t adc_reading = 0;
    esp_err_t err = xd58c_read_analog(&adc_reading);
    if (err != ESP_OK) {
        return err;
    }
    
    // Convertir a voltaje usando calibración
    if (adc1_cali_handle != NULL) {
        int voltage;
        err = adc_cali_raw_to_voltage(adc1_cali_handle, adc_reading, &voltage);
        if (err == ESP_OK) {
            *voltage_mv = (uint32_t)voltage;
        } else {
            // Fallback: conversión manual aproximada
            *voltage_mv = (adc_reading * 3300) / 4095;
        }
    } else {
        // Cálculo manual si no hay calibración
        *voltage_mv = (adc_reading * 3300) / 4095;
    }
    
    return ESP_OK;
}

void xd58c_heartrate_init(xd58c_heartrate_t *hr) {
    if (hr == NULL) return;
    
    memset(hr, 0, sizeof(xd58c_heartrate_t));
    
    // Baseline inicial = 0 (se calibrará automáticamente)
    hr->baseline = 0;
    hr->baseline_index = 0;
    hr->baseline_sum = 0;
    
    // Llenar buffer de baseline vacío
    for (int i = 0; i < XD58C_BASELINE_SAMPLES; i++) {
        hr->baseline_buffer[i] = 0;
    }
    
    hr->finger_detected = false;
    hr->last_peak_state = false;
    hr->last_peak_time = 0;
    hr->intervals_sum = 0;
    hr->intervals_count = 0;
    hr->window_start = 0;
    hr->peaks_count = 0;
    hr->min_signal = 4000;
    hr->max_signal = 0;
    
    // AUTO-CALIBRACIÓN
    hr->calibration_done = false;
    hr->calibration_start = 0;
    hr->calibration_samples = 0;
    hr->ambient_baseline = 0;
    hr->signal_with_finger = 0;
    hr->auto_threshold = false;
    
    ESP_LOGI(TAG, "🔧 Algoritmo con AUTO-CALIBRACIÓN inicializado");
    ESP_LOGI(TAG, "   ⏱️  Se calibrará automáticamente en los primeros 10 segundos");
}

bool xd58c_heartrate_process(xd58c_heartrate_t *hr, uint32_t voltage_mv, uint32_t current_time_ms) {
    if (hr == NULL) return false;
    
    // === 1. AUTO-CALIBRACIÓN INICIAL (primeros 5 segundos) ===
    if (!hr->calibration_done) {
        if (hr->calibration_start == 0) {
            hr->calibration_start = current_time_ms;
            hr->ambient_baseline = (int)voltage_mv;
            hr->signal_with_finger = (int)voltage_mv;
            ESP_LOGI("XD58C", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            ESP_LOGI("XD58C", "🔧 INICIANDO AUTO-CALIBRACIÓN (10 segundos)");
            ESP_LOGI("XD58C", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            ESP_LOGI("XD58C", "📍 PASO 1: Coloca tu dedo en el sensor");
            ESP_LOGI("XD58C", "📍 PASO 2: Presiona SUAVEMENTE");
            ESP_LOGI("XD58C", "📍 PASO 3: NO MUEVAS el dedo durante 10 segundos");
            ESP_LOGI("XD58C", "");
        }
        
        // Recolectar muestras durante calibración
        hr->calibration_samples++;
        if ((int)voltage_mv < hr->ambient_baseline) hr->ambient_baseline = (int)voltage_mv;
        if ((int)voltage_mv > hr->signal_with_finger) hr->signal_with_finger = (int)voltage_mv;
        
        // Mensajes de progreso cada 2 segundos
        static uint32_t last_progress_msg = 0;
        uint32_t elapsed = current_time_ms - hr->calibration_start;
        if (elapsed - last_progress_msg >= 2000) {
            int seconds_left = (XD58C_CALIBRATION_TIME_MS - elapsed) / 1000;
            ESP_LOGI("XD58C", "⏳ Calibrando... %d segundos restantes (Señal: %lu mV)", 
                     seconds_left, voltage_mv);
            last_progress_msg = elapsed;
        }
        
        // Completar calibración después de 5 segundos
        if (current_time_ms - hr->calibration_start >= XD58C_CALIBRATION_TIME_MS) {
            hr->calibration_done = true;
            int calibrated_range = hr->signal_with_finger - hr->ambient_baseline;
            
            // RESETEAR min/max para empezar limpio
            hr->min_signal = (int)voltage_mv;
            hr->max_signal = (int)voltage_mv;
            hr->baseline = (int)voltage_mv;
            
            // Llenar buffer de baseline con valor actual
            for (int i = 0; i < XD58C_BASELINE_SAMPLES; i++) {
                hr->baseline_buffer[i] = (int)voltage_mv;
            }
            hr->baseline_sum = (int)voltage_mv * XD58C_BASELINE_SAMPLES;
            
            ESP_LOGI("XD58C", "");
            ESP_LOGI("XD58C", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            ESP_LOGI("XD58C", "✅ CALIBRACIÓN COMPLETA!");
            ESP_LOGI("XD58C", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            ESP_LOGI("XD58C", "📊 Resultados:");
            ESP_LOGI("XD58C", "   Baseline ambiente: %d mV", hr->ambient_baseline);
            ESP_LOGI("XD58C", "   Señal con dedo: %d mV", hr->signal_with_finger);
            ESP_LOGI("XD58C", "   Rango detectado: %d mV", calibrated_range);
            ESP_LOGI("XD58C", "   Muestras analizadas: %d", hr->calibration_samples);
            
            if (calibrated_range < XD58C_MIN_RANGE_MV) {
                ESP_LOGW("XD58C", "⚠️  Rango muy bajo (%d mV). Posibles causas:", calibrated_range);
                ESP_LOGW("XD58C", "   - Dedo no está presionado correctamente");
                ESP_LOGW("XD58C", "   - Luz ambiente demasiado brillante");
                ESP_LOGW("XD58C", "   - Sensor mal conectado (verificar GPIO34)");
                ESP_LOGW("XD58C", "   - Voltaje insuficiente (verificar 3.3V)");
            } else {
                ESP_LOGI("XD58C", "✅ Rango aceptable - Iniciando detección de pulsos");
            }
            hr->auto_threshold = true;
        }
        return false;  // No detectar pulsos durante calibración
    }
    
    // === 2. DETECTAR SI HAY PRESIÓN ADECUADA DEL DEDO (post-calibración) ===
    int signal_deviation = abs((int)voltage_mv - hr->ambient_baseline);
    if (signal_deviation < XD58C_MIN_SIGNAL_CHANGE) {
        hr->finger_detected = false;
        hr->bpm = 0;
        return false;  // Sin cambio significativo = sin dedo
    }
    hr->finger_detected = true;  // Cambio detectado = dedo presente
    
    // Inicializar ventana si es primera vez
    if (hr->window_start == 0) {
        hr->window_start = current_time_ms;
    }
    
    // === 3. ACTUALIZAR BASELINE ADAPTATIVO (promedio móvil de 50 muestras) ===
    hr->baseline_sum -= hr->baseline_buffer[hr->baseline_index];
    hr->baseline_buffer[hr->baseline_index] = (int)voltage_mv;
    hr->baseline_sum += (int)voltage_mv;
    hr->baseline_index = (hr->baseline_index + 1) % XD58C_BASELINE_SAMPLES;
    hr->baseline = hr->baseline_sum / XD58C_BASELINE_SAMPLES;
    
    // === 3. ACTUALIZAR ESTADÍSTICAS DE SEÑAL ===
    if ((int)voltage_mv < hr->min_signal) hr->min_signal = (int)voltage_mv;
    if ((int)voltage_mv > hr->max_signal) hr->max_signal = (int)voltage_mv;
    
    // === 4. VALIDAR RANGO DE SEÑAL Y CALCULAR UMBRAL ADAPTATIVO ===
    int signal_range = hr->max_signal - hr->min_signal;
    
    // Validar que hay suficiente variación de señal (REDUCIDO para sensores sensibles)
    if (signal_range < XD58C_MIN_RANGE_MV) {
        // Rango muy bajo, pero no descartar inmediatamente
        // Puede ser inicio de lectura
        static uint8_t low_range_count = 0;
        low_range_count++;
        if (low_range_count > 20) {  // Después de 20 muestras malas
            hr->finger_detected = false;
            low_range_count = 0;
            return false;
        }
    }
    
    // Umbral adaptativo: 25% del rango (más sensible)
    // Si el rango es muy pequeño, usar umbral mínimo
    int dynamic_threshold = (signal_range > 40) ? (signal_range / 4) : 10;
    
    // === 5. DETECTAR PICO CON UMBRAL DINÁMICO ===
    bool current_peak = ((int)voltage_mv > (hr->baseline + dynamic_threshold));
    
    // === 6. DETECTAR FLANCO ASCENDENTE (transición low->high) ===
    if (current_peak && !hr->last_peak_state) {
        // Solo contar si hay pulso anterior válido
        if (hr->last_peak_time > 0) {
            uint32_t interval = current_time_ms - hr->last_peak_time;
            
            // Validar intervalo: debe estar entre límites fisiológicos (40-180 BPM)
            uint32_t min_interval = 60000 / XD58C_MAX_BPM;  // ~333 ms
            uint32_t max_interval = 60000 / XD58C_MIN_BPM;  // ~1500 ms
            
            if (interval >= min_interval && interval <= max_interval) {
                // Intervalo válido - acumular para promedio
                hr->intervals_sum += interval;
                hr->intervals_count++;
                hr->peaks_count++;
                
                ESP_LOGD(TAG, "💓 Latido #%d: intervalo %lu ms", hr->peaks_count, interval);
            }
        }
        
        // Actualizar timestamp del último pico
        hr->last_peak_time = current_time_ms;
    }
    
    // Actualizar estado del pico
    hr->last_peak_state = current_peak;
    
    // === 7. CALCULAR BPM CADA 5 SEGUNDOS ===
    if (current_time_ms - hr->window_start >= XD58C_SAMPLE_WINDOW) {
        // Calcular BPM promedio si hay suficientes muestras (mínimo 4 pulsos)
        if (hr->intervals_count >= 4) {
            uint32_t avg_interval = hr->intervals_sum / hr->intervals_count;
            uint32_t calculated_bpm = 60000 / avg_interval;
            
            // Validar BPM dentro de rangos fisiológicos
            if (calculated_bpm >= XD58C_MIN_BPM && calculated_bpm <= XD58C_MAX_BPM) {
                hr->bpm = calculated_bpm;
                ESP_LOGI(TAG, "❤️  BPM: %lu (de %d latidos, promedio %lu ms/latido)", 
                         hr->bpm, hr->intervals_count, avg_interval);
            } else {
                hr->bpm = 0;
                ESP_LOGW(TAG, "⚠️  BPM fuera de rango: %lu (esperado 40-180)", calculated_bpm);
            }
        } else {
            hr->bpm = 0;
            ESP_LOGW(TAG, "⚠️  Pocos latidos (%d/4 mínimo), aumenta presión del dedo", hr->intervals_count);
        }
        
        // Resetear contadores para nueva ventana
        hr->intervals_sum = 0;
        hr->intervals_count = 0;
        hr->window_start = current_time_ms;
        
        // Resetear estadísticas de señal
        hr->min_signal = 4000;
        hr->max_signal = 0;
    }
    
    return false;
}

uint32_t xd58c_heartrate_get_bpm(xd58c_heartrate_t *hr, uint32_t current_time_ms) {
    if (hr == NULL) return 0;
    
    // Verificar si la ventana actual tiene datos recientes
    if (current_time_ms - hr->window_start < XD58C_SAMPLE_WINDOW) {
        // Ventana en curso, retornar último BPM calculado si existe
        return hr->bpm;
    }
    
    // Si pasó mucho tiempo sin calcular, retornar 0
    if (current_time_ms - hr->window_start > XD58C_SAMPLE_WINDOW * 2) {
        return 0;
    }
    
    return hr->bpm;
}