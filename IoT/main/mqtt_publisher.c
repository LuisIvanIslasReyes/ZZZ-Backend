#include "mqtt_publisher.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "mqtt_client.h"
#include <string.h>
#include <time.h>
#include <sys/time.h>

static const char *TAG = "MQTT_PUB";

static esp_mqtt_client_handle_t mqtt_client = NULL;
static bool mqtt_connected = false;
static char mqtt_topic[64];

// Callbacks WiFi
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                                int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGW(TAG, "WiFi desconectado, reconectando...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "✅ WiFi conectado - IP: " IPSTR, IP2STR(&event->ip_info.ip));
    }
}

// Callbacks MQTT
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, 
                               int32_t event_id, void *event_data) {
    (void)handler_args;  // Marcar como intencionalmente no usado
    (void)base;          // Marcar como intencionalmente no usado
    (void)event_data;    // Marcar como intencionalmente no usado
    
    switch ((esp_mqtt_event_id_t)event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "✅ MQTT conectado al broker");
            mqtt_connected = true;
            break;
            
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGW(TAG, "⚠️  MQTT desconectado");
            mqtt_connected = false;
            break;
            
        case MQTT_EVENT_ERROR:
            ESP_LOGE(TAG, "❌ Error MQTT");
            mqtt_connected = false;
            break;
            
        default:
            break;
    }
}

esp_err_t mqtt_publisher_init(const char *wifi_ssid, const char *wifi_password) {
    esp_err_t ret;
    
    // ========== CONFIGURAR WIFI ==========
    ESP_LOGI(TAG, "Inicializando WiFi...");
    
    ret = esp_netif_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Error en esp_netif_init: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ret = esp_event_loop_create_default();
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "Error creando event loop: %s", esp_err_to_name(ret));
        return ret;
    }
    
    esp_netif_create_default_wifi_sta();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ret = esp_wifi_init(&cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Error en esp_wifi_init: %s", esp_err_to_name(ret));
        return ret;
    }
    
    // Registrar eventos WiFi
    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        &instance_got_ip));
    
    // Configurar credenciales WiFi
    wifi_config_t wifi_config = {
        .sta = {
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };
    
    strncpy((char *)wifi_config.sta.ssid, wifi_ssid, sizeof(wifi_config.sta.ssid) - 1);
    strncpy((char *)wifi_config.sta.password, wifi_password, sizeof(wifi_config.sta.password) - 1);
    
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
    
    ESP_LOGI(TAG, "🔌 Conectando a WiFi: %s", wifi_ssid);
    
    // Esperar conexión WiFi (máximo 60 segundos)
    int retry = 0;
    while (retry < 120) {
        esp_netif_t *netif = esp_netif_get_handle_from_ifkey("WIFI_STA_DEF");
        esp_netif_ip_info_t ip_info;
        if (esp_netif_get_ip_info(netif, &ip_info) == ESP_OK && ip_info.ip.addr != 0) {
            break;
        }
        vTaskDelay(pdMS_TO_TICKS(500));
        retry++;
    }
    
    if (retry >= 120) {
        ESP_LOGE(TAG, "❌ Timeout conectando a WiFi (60 segundos)");
        ESP_LOGW(TAG, "⚠️  Continuando sin WiFi - reintentará en background");
        // No retornar ESP_FAIL - permitir que continúe y se conecte después
    }
    
    // ========== CONFIGURAR MQTT ==========
    ESP_LOGI(TAG, "Inicializando cliente MQTT...");
    
    // Generar topic con el device_id
    snprintf(mqtt_topic, sizeof(mqtt_topic), MQTT_TOPIC_TEMPLATE, DEVICE_ID);
    
    esp_mqtt_client_config_t mqtt_cfg = {
        .broker.address.uri = MQTT_BROKER_URI,
    };
    
    // Credenciales MQTT (si aplica)
    if (strlen(MQTT_USERNAME) > 0) {
        mqtt_cfg.credentials.username = MQTT_USERNAME;
    }
    if (strlen(MQTT_PASSWORD) > 0) {
        mqtt_cfg.credentials.authentication.password = MQTT_PASSWORD;
    }
    
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);
    if (mqtt_client == NULL) {
        ESP_LOGE(TAG, "❌ Error inicializando cliente MQTT");
        return ESP_FAIL;
    }
    
    esp_mqtt_client_register_event(mqtt_client, ESP_EVENT_ANY_ID, mqtt_event_handler, NULL);
    esp_mqtt_client_start(mqtt_client);
    
    ESP_LOGI(TAG, "📡 Cliente MQTT iniciado");
    ESP_LOGI(TAG, "   Topic: %s", mqtt_topic);
    ESP_LOGI(TAG, "   Device ID: %s", DEVICE_ID);
    
    return ESP_OK;
}

esp_err_t mqtt_publish_sensor_data(const sensor_payload_t *payload) {
    if (payload == NULL) {
        ESP_LOGE(TAG, "Payload nulo");
        return ESP_ERR_INVALID_ARG;
    }
    
    if (!mqtt_connected) {
        ESP_LOGW(TAG, "MQTT no conectado, reintentando...");
        return ESP_ERR_INVALID_STATE;
    }
    
    // Obtener timestamp ISO 8601
    time_t now;
    struct tm timeinfo;
    char timestamp[32];
    
    time(&now);
    gmtime_r(&now, &timeinfo);
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    
    // Construir JSON (formato esperado por Django)
    char json_payload[512];
    snprintf(json_payload, sizeof(json_payload),
             "{"
             "\"device_id\":\"%s\","
             "\"timestamp\":\"%s\","
             "\"heart_rate\":%.1f,"
             "\"spo2\":%.1f,"
             "\"accel\":{"
             "\"x\":%.3f,"
             "\"y\":%.3f,"
             "\"z\":%.3f"
             "}"
             "}",
             payload->device_id,
             timestamp,
             (float)payload->heart_rate_bpm,
             payload->spo2,
             payload->accel_x,
             payload->accel_y,
             payload->accel_z);
    
    // Publicar mensaje
    int msg_id = esp_mqtt_client_publish(mqtt_client, mqtt_topic, json_payload, 0, 1, 0);
    
    if (msg_id >= 0) {
        ESP_LOGI(TAG, "📤 Datos publicados (msg_id=%d)", msg_id);
        ESP_LOGD(TAG, "   Payload: %s", json_payload);
        return ESP_OK;
    } else {
        ESP_LOGE(TAG, "❌ Error publicando datos");
        return ESP_FAIL;
    }
}

esp_err_t mqtt_publish_alert(const alert_payload_t *payload) {
    if (payload == NULL) {
        ESP_LOGE(TAG, "Alert payload nulo");
        return ESP_ERR_INVALID_ARG;
    }
    
    if (!mqtt_connected) {
        ESP_LOGW(TAG, "MQTT no conectado, no se puede enviar alerta");
        return ESP_ERR_INVALID_STATE;
    }
    
    // Obtener timestamp ISO 8601
    time_t now;
    struct tm timeinfo;
    char timestamp[32];
    
    time(&now);
    gmtime_r(&now, &timeinfo);
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    
    // Construir JSON para alerta
    char json_payload[512];
    snprintf(json_payload, sizeof(json_payload),
             "{"
             "\"device_id\":\"%s\","
             "\"timestamp\":\"%s\","
             "\"alert_type\":\"%s\","
             "\"severity\":\"%s\","
             "\"message\":\"%s\","
             "\"heart_rate\":%.1f,"
             "\"spo2\":%.1f"
             "}",
             payload->device_id,
             timestamp,
             payload->alert_type,
             payload->severity,
             payload->message,
             (float)payload->heart_rate_bpm,
             payload->spo2);
    
    // Topic para alertas: devices/{device_id}/alerts
    char alert_topic[128];
    snprintf(alert_topic, sizeof(alert_topic), "devices/%s/alerts", payload->device_id);
    
    // Publicar mensaje
    int msg_id = esp_mqtt_client_publish(mqtt_client, alert_topic, json_payload, 0, 1, 0);
    
    if (msg_id >= 0) {
        ESP_LOGW(TAG, "🚨 ALERTA publicada: %s (msg_id=%d)", payload->alert_type, msg_id);
        ESP_LOGW(TAG, "   Mensaje: %s", payload->message);
        ESP_LOGD(TAG, "   Payload: %s", json_payload);
        return ESP_OK;
    } else {
        ESP_LOGE(TAG, "❌ Error publicando alerta");
        return ESP_FAIL;
    }
}

bool mqtt_is_connected(void) {
    return mqtt_connected;
}

void mqtt_publisher_stop(void) {
    if (mqtt_client != NULL) {
        esp_mqtt_client_stop(mqtt_client);
        esp_mqtt_client_destroy(mqtt_client);
        mqtt_client = NULL;
        mqtt_connected = false;
        ESP_LOGI(TAG, "Cliente MQTT detenido");
    }
}
