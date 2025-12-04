#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_spiffs.h"
#include "nvs_flash.h"

#include "xd58c_driver.h"
#include "adxl345_driver.h"
#include "mqtt_publisher.h"
// #include "micropython_bindings.h"  // Comentado temporalmente - MicroPython no instalado

static const char *TAG = "MAIN";

// ========== CONFIGURACIÓN WIFI (CAMBIAR CON TUS DATOS) ==========
#define WIFI_SSID     "HUAWEI-106V4H"        // ⚠️ CAMBIAR
#define WIFI_PASSWORD "Natalia1926281" // ⚠️ CAMBIAR

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
    
    uint32_t last_mqtt_publish = 0;
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
                // Calcular umbral dinámico actual
                int range = heartrate.max_signal - heartrate.baseline;
                int dynamic_thr = (range > 10) ? (range * 3 / 10) : 5;
                
                ESP_LOGI(TAG, "━━━ DIAGNÓSTICO XD58C ━━━");
                ESP_LOGI(TAG, "  Señal actual:     %lu mV", voltage_mv);
                ESP_LOGI(TAG, "  Baseline:         %d mV", heartrate.baseline);
                ESP_LOGI(TAG, "  Rango [min-max]:  [%d - %d] = %d mV", 
                         heartrate.min_signal, heartrate.max_signal, range);
                ESP_LOGI(TAG, "  Umbral dinámico:  %d mV", dynamic_thr);
                ESP_LOGI(TAG, "  Presión:          %s (señal %s, rango %s)", 
                         heartrate.finger_detected ? "✓ BUENA" : "✗ INSUFICIENTE",
                         voltage_mv > 2200 ? "alta" : "baja",
                         range > 100 ? "OK" : "bajo");
                ESP_LOGI(TAG, "  Pulsos en ventana: %d pulsos", heartrate.intervals_count);
                ESP_LOGI(TAG, "  BPM actual:       %lu", heartrate.bpm);
                
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
        
        // ========== PUBLICAR A MQTT (cada 5 segundos, como en el backend) ==========
        if (current_time_ms - last_mqtt_publish >= 5000) {
            uint32_t bpm = xd58c_heartrate_get_bpm(&heartrate, current_time_ms);
            
            // Preparar payload
            sensor_payload_t payload = {
                .heart_rate_bpm = bpm,
                .spo2 = 98.0,  // ⚠️ SpO2 no disponible, valor fijo por ahora
                .accel_x = accel.x,
                .accel_y = accel.y,
                .accel_z = accel.z
            };
            strncpy(payload.device_id, DEVICE_ID, sizeof(payload.device_id) - 1);
            
            // Publicar siempre (aunque BPM sea 0)
            if (mqtt_is_connected()) {
                esp_err_t pub_err = mqtt_publish_sensor_data(&payload);
                if (pub_err == ESP_OK) {
                    if (bpm > 0) {
                        ESP_LOGI(TAG, "✅ BPM: %lu | Latidos: %d | Accel: (%.2f, %.2f, %.2f)", 
                                 bpm, heartrate.peaks_count, accel.x, accel.y, accel.z);
                    } else {
                        ESP_LOGI(TAG, "⏳ Detectando... (Señal: %lu mV, Latidos: %d)", 
                                 heartrate.baseline, heartrate.peaks_count);
                    }
                } else {
                    ESP_LOGE(TAG, "❌ Error MQTT");
                }
            }
            
            last_mqtt_publish = current_time_ms;
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
        ESP_LOGE(TAG, "❌ Error inicializando MQTT. Verifica credenciales WiFi.");
        ESP_LOGE(TAG, "   SSID: %s", WIFI_SSID);
        return;
    }
    
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "✅ Sistema listo para transmitir datos");
    ESP_LOGI(TAG, "===========================================");
    
    // ========== INICIAR TAREA DE CAPTURA Y TRANSMISIÓN ==========
    xTaskCreate(sensors_mqtt_task, "mqtt_sensors", 8192, NULL, 5, NULL);
    
    ESP_LOGI(TAG, "📡 Tarea MQTT iniciada - Enviando datos cada 5 segundos");
}
