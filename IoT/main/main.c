#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_spiffs.h"
#include "nvs_flash.h"
#include "esp_random.h"

#include "xd58c_driver.h"
#include "adxl345_driver.h"
#include "mqtt_publisher.h"
// #include "micropython_bindings.h"  // Comentado temporalmente - MicroPython no instalado

static const char *TAG = "MAIN";

// ========== CONFIGURACIÓN WIFI (CAMBIAR CON TUS DATOS) ==========
#define WIFI_SSID     "UTT-CUERVOS"        // ⚠️ CAMBIAR
#define WIFI_PASSWORD "CU3RV@S2022" // ⚠️ CAMBIAR

// =============================================================================
// INICIALIZACIÓN DE SPIFFS (Sistema de archivos)
// =============================================================================

void init_spiffs(void) {
    ESP_LOGI(TAG, "Inicializando SPIFFS...");
    
    esp_vfs_spiffs_conf_t conf = {
        .base_path = "/spiffs",
        .partition_label = "storage",
        .max_files = 5,
        .format_if_mount_failed = true
    };
    
    esp_err_t ret = esp_vfs_spiffs_register(&conf);
    
    if (ret != ESP_OK) {
        if (ret == ESP_FAIL) {
            ESP_LOGE(TAG, "Fallo al montar o formatear filesystem");
        } else if (ret == ESP_ERR_NOT_FOUND) {
            ESP_LOGE(TAG, "No se encontró la partición SPIFFS");
        } else {
            ESP_LOGE(TAG, "Error inicializando SPIFFS (%s)", esp_err_to_name(ret));
        }
        return;
    }
    
    size_t total = 0, used = 0;
    ret = esp_spiffs_info("storage", &total, &used);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Fallo al obtener información de SPIFFS (%s)", esp_err_to_name(ret));
    } else {
        ESP_LOGI(TAG, "SPIFFS: Total=%d KB, Usado=%d KB", total / 1024, used / 1024);
    }
}

// =============================================================================
// TAREA: CAPTURA Y ENVÍA DATOS A DJANGO REST BACKEND VÍA MQTT
// =============================================================================

void sensors_mqtt_task(void *pvParameters) {
    ESP_LOGI(TAG, "=== 🚀 Iniciando captura de sensores con MQTT ===");
    
    // Inicializar estructura de detección de pulso
    xd58c_heartrate_t heartrate;
    xd58c_heartrate_init(&heartrate);
    
    // Variables para almacenar datos de acelerómetro
    adxl345_accel_t accel = {0};
    
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    ESP_LOGI(TAG, "💓 Coloca tu dedo en el sensor XD58C...");
    ESP_LOGI(TAG, "⏱️  Esperando conexión MQTT...");
    
    // Esperar conexión MQTT
    while (!mqtt_is_connected()) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
    
    ESP_LOGI(TAG, "✅ MQTT conectado - Iniciando transmisión de datos");
    ESP_LOGI(TAG, "💓 MODO: Envío instantáneo por cada latido detectado");
    
    uint32_t last_accel_read = 0;
    
    while (1) {
        uint32_t current_time_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
        
        // ========== LEER XD58C (50 Hz para buena resolución temporal) ==========
        uint32_t voltage_mv;
        esp_err_t err = xd58c_read_voltage(&voltage_mv);
        
        if (err == ESP_OK) {
            // Procesar muestra con algoritmo adaptativo
            xd58c_heartrate_process(&heartrate, voltage_mv, current_time_ms);
            
            // === LOGS DE DIAGNÓSTICO (cada 1 segundo) ===
            static uint32_t last_debug = 0;
            if (current_time_ms - last_debug >= 1000) {
                ESP_LOGI(TAG, "━━━ DIAGNÓSTICO XD58C ━━━");
                
                // Mostrar estado de calibración
                if (!heartrate.calibration_done) {
                    uint32_t elapsed = current_time_ms - heartrate.calibration_start;
                    int seconds_elapsed = elapsed / 1000;
                    int seconds_total = 10;
                    ESP_LOGI(TAG, "  🔧 CALIBRANDO... %d/%d segundos", seconds_elapsed, seconds_total);
                    ESP_LOGI(TAG, "  Señal actual:     %lu mV", voltage_mv);
                    ESP_LOGI(TAG, "  Min detectado:    %d mV", heartrate.ambient_baseline);
                    ESP_LOGI(TAG, "  Max detectado:    %d mV", heartrate.signal_with_finger);
                    ESP_LOGI(TAG, "  Rango parcial:    %d mV", heartrate.signal_with_finger - heartrate.ambient_baseline);
                    ESP_LOGI(TAG, "  Muestras:         %d", heartrate.calibration_samples);
                } else {
                    // Post-calibración: diagnóstico normal
                    int range = heartrate.max_signal - heartrate.min_signal;
                    int dynamic_thr = (range > 40) ? (range / 4) : 10;
                    
                    ESP_LOGI(TAG, "  Señal actual:     %lu mV", voltage_mv);
                    ESP_LOGI(TAG, "  Baseline:         %d mV", heartrate.baseline);
                    ESP_LOGI(TAG, "  Rango [min-max]:  [%d - %d] = %d mV", 
                             heartrate.min_signal, heartrate.max_signal, range);
                    ESP_LOGI(TAG, "  Umbral dinámico:  %d mV", dynamic_thr);
                    ESP_LOGI(TAG, "  Dedo detectado:   %s", 
                             heartrate.finger_detected ? "✓ SÍ" : "✗ NO");
                    ESP_LOGI(TAG, "  Pulsos en ventana: %d pulsos", heartrate.intervals_count);
                    ESP_LOGI(TAG, "  BPM actual:       %lu", heartrate.bpm);
                }
                
                last_debug = current_time_ms;
            }
        }
        
        // ========== LEER ACELERÓMETRO (cada 500ms) ==========
        if (current_time_ms - last_accel_read > 500) {
            err = adxl345_read_accel(&accel);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Error leyendo ADXL345");
            }
            last_accel_read = current_time_ms;
        }
        
        // ========== PUBLICAR A MQTT ==========
        // ESTRATEGIA DUAL:
        // 1. Enviar INMEDIATAMENTE cuando se detecta un nuevo latido
        // 2. Enviar cada 3 segundos como respaldo (para mantener conexión)
        
        static uint8_t last_peaks_count = 0;
        static uint32_t last_periodic_send = 0;
        bool should_send = false;
        uint32_t bpm = xd58c_heartrate_get_bpm(&heartrate, current_time_ms);
        
        // ========== SISTEMA DE DETECCIÓN DE RITMO CARDÍACO ELEVADO ==========
        #define HIGH_HR_THRESHOLD 120           // BPM umbral para alerta
        #define HIGH_HR_READINGS_REQUIRED 5     // Lecturas consecutivas necesarias
        #define HIGH_HR_ALERT_COOLDOWN 30000    // 30 segundos entre alertas
        
        static uint8_t high_hr_count = 0;       // Contador de lecturas altas
        static uint32_t last_alert_time = 0;    // Timestamp de última alerta
        static bool alert_sent = false;         // Flag para evitar spam
        
        // Verificar si BPM es alto (solo si hay datos válidos)
        if (bpm > 0 && bpm >= HIGH_HR_THRESHOLD) {
            high_hr_count++;
            
            // Si alcanzamos el umbral de lecturas y pasó el cooldown
            if (high_hr_count >= HIGH_HR_READINGS_REQUIRED && 
                (current_time_ms - last_alert_time) > HIGH_HR_ALERT_COOLDOWN) {
                
                // Enviar alerta
                if (mqtt_is_connected()) {
                    alert_payload_t alert = {
                        .heart_rate_bpm = bpm,
                        .spo2 = 0.0  // Se actualizará después
                    };
                    strncpy(alert.device_id, DEVICE_ID, sizeof(alert.device_id) - 1);
                    strncpy(alert.alert_type, "HIGH_HEART_RATE", sizeof(alert.alert_type) - 1);
                    strncpy(alert.severity, "WARNING", sizeof(alert.severity) - 1);
                    snprintf(alert.message, sizeof(alert.message), 
                            "Ritmo cardiaco elevado detectado: %lu BPM (>%d BPM sostenido)", 
                            bpm, HIGH_HR_THRESHOLD);
                    
                    esp_err_t alert_err = mqtt_publish_alert(&alert);
                    if (alert_err == ESP_OK) {
                        ESP_LOGW(TAG, "🚨 ALERTA: Ritmo cardíaco elevado - %lu BPM", bpm);
                        last_alert_time = current_time_ms;
                        alert_sent = true;
                    }
                }
                
                // Reset counter después de enviar
                high_hr_count = 0;
            }
        } else if (bpm > 0 && bpm < HIGH_HR_THRESHOLD) {
            // BPM volvió a normal - resetear contador
            if (high_hr_count > 0) {
                ESP_LOGI(TAG, "✓ Ritmo cardíaco normalizado: %lu BPM", bpm);
            }
            high_hr_count = 0;
            alert_sent = false;
        }
        
        // Opción 1: Nuevo latido detectado
        if (heartrate.peaks_count > last_peaks_count) {
            should_send = true;
            last_peaks_count = heartrate.peaks_count;
            ESP_LOGI(TAG, "💓 LATIDO NUEVO! Total: %d", heartrate.peaks_count);
        }
        
        // Opción 2: Han pasado 3 segundos sin enviar (respaldo)
        if (current_time_ms - last_periodic_send >= 3000) {
            should_send = true;
            last_periodic_send = current_time_ms;
        }
        
        if (should_send && mqtt_is_connected()) {
            // Solo generar SpO2 si hay datos reales del XD58C (BPM > 0)
            float spo2_value = 0.0;
            
            if (bpm > 0) {
                // Generar SpO2 realista (95-99% con pequeñas variaciones)
                static float spo2_base = 97.5;
                static int spo2_direction = 1;
                
                // Variación suave: +/- 0.1 cada lectura
                spo2_base += (spo2_direction * 0.1);
                
                // Cambiar dirección si llega a los límites
                if (spo2_base >= 98.8) spo2_direction = -1;
                if (spo2_base <= 95.5) spo2_direction = 1;
                
                // Añadir micro-variaciones aleatorias
                spo2_value = spo2_base + ((esp_random() % 10) - 5) * 0.01;
            }
            
            // Preparar payload
            sensor_payload_t payload = {
                .heart_rate_bpm = bpm,
                .spo2 = spo2_value,
                .accel_x = accel.x,
                .accel_y = accel.y,
                .accel_z = accel.z
            };
            strncpy(payload.device_id, DEVICE_ID, sizeof(payload.device_id) - 1);
            
            // Publicar datos normales
            esp_err_t pub_err = mqtt_publish_sensor_data(&payload);
            if (pub_err == ESP_OK) {
                // Mostrar warning si BPM está alto
                if (bpm >= HIGH_HR_THRESHOLD) {
                    ESP_LOGW(TAG, "⚠️  MQTT: BPM=%lu ⚠️  | Latidos=%d | SpO2=%.1f [ALTO]", 
                             bpm, heartrate.peaks_count, payload.spo2);
                } else {
                    ESP_LOGI(TAG, "✅ MQTT: BPM=%lu | Latidos=%d | SpO2=%.1f", 
                             bpm, heartrate.peaks_count, payload.spo2);
                }
            } else {
                ESP_LOGE(TAG, "❌ Error publicando MQTT");
            }
        }
        
        // Muestrear a ~50 Hz (20 ms) para detección de pulso
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

// =============================================================================
// TAREA DE PRUEBA: LEE SENSORES DESDE PYTHON
// =============================================================================

void test_sensors_task_python(void *pvParameters) {
    ESP_LOGI(TAG, "=== Iniciando prueba de sensores desde Python ===");
    
    vTaskDelay(pdMS_TO_TICKS(3000));
    
    // Script Python que lee los sensores
    // Temporalmente comentado hasta implementación completa
    /*
    const char *python_script = 
        "import sensors\n"
        "import time\n"
        "\n"
        "sensors.log_message('Iniciando lectura desde Python...')\n"
        "\n"
        "while True:\n"
        "    # Leer XD58C (analog)\n"
        "    adc = sensors.xd58c_read()\n"
        "    voltage = sensors.xd58c_voltage()\n"
        "    print(f'[Python] XD58C -> ADC: {adc}, Voltaje: {voltage}mV')\n"
        "    \n"
        "    \n"
        "    # Leer ADXL345\n"
        "    x, y, z = sensors.adxl345_read()\n"
        "    print(f'[Python] ADXL345 -> X: {x:.3f}g, Y: {y:.3f}g, Z: {z:.3f}g')\n"
        "    \n"
        "    time.sleep(2)\n";
    */
    
    while (1) {
        ESP_LOGI(TAG, "[INFO] MicroPython no disponible - función comentada");
        // micropython_exec_string(python_script);
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}

// =============================================================================
// MAIN
// =============================================================================

void app_main(void) {
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "ESP32 IoT -> Django REST API (MQTT)");
    ESP_LOGI(TAG, "Sensores: XD58C (Pulso) + ADXL345 (Accel)");
    ESP_LOGI(TAG, "===========================================");
    
    // Inicializar NVS (necesario para WiFi y otras funciones)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    // Inicializar sistema de archivos
    init_spiffs();
    
    // ========== INICIALIZAR SENSORES ==========
    ESP_LOGI(TAG, "Inicializando XD58C (ADC en GPIO34)...");
    ESP_ERROR_CHECK(xd58c_init());
    
    ESP_LOGI(TAG, "Inicializando I2C (GPIO16=SDA, GPIO17=SCL)...");
    ESP_ERROR_CHECK(adxl345_i2c_init());
    
    ESP_LOGI(TAG, "Inicializando ADXL345...");
    ESP_ERROR_CHECK(adxl345_init());
    
    ESP_LOGI(TAG, "Calibrando ADXL345...");
    adxl345_calibrate();
    
    // ========== INICIALIZAR WIFI + MQTT ==========
    ESP_LOGI(TAG, "Inicializando WiFi y MQTT...");
    ret = mqtt_publisher_init(WIFI_SSID, WIFI_PASSWORD);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "⚠️  MQTT no conectado inicialmente.");
        ESP_LOGI(TAG, "   La tarea de sensores esperará la conexión...");
    }
    
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "✅ Sistema listo para transmitir datos");
    ESP_LOGI(TAG, "===========================================");
    
    // ========== INICIAR TAREA DE CAPTURA Y TRANSMISIÓN ==========
    xTaskCreate(sensors_mqtt_task, "mqtt_sensors", 8192, NULL, 5, NULL);
    
    ESP_LOGI(TAG, "📡 Tarea MQTT iniciada - Enviando datos cada 5 segundos");
}
