#ifndef MQTT_PUBLISHER_H
#define MQTT_PUBLISHER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

// Configuración del servidor MQTT (ajusta según tu backend)
#define MQTT_BROKER_URI     "mqtt://172.18.5.137:1883"  // Cambiar a IP de tu servidor
#define MQTT_USERNAME       ""                        // Usuario MQTT (si aplica)
#define MQTT_PASSWORD       ""                        // Contraseña MQTT (si aplica)

// Identificador único del dispositivo ESP32
#define DEVICE_ID           "ESP32-001"               // Cambiar según tu sistema

// Topic MQTT (debe coincidir con el backend: devices/+/sensors)
#define MQTT_TOPIC_TEMPLATE "devices/%s/sensors"

/**
 * @brief Estructura para datos de sensores a publicar
 */
typedef struct {
    char device_id[32];      // Identificador del dispositivo
    uint32_t heart_rate_bpm; // Pulso cardíaco en BPM
    float spo2;              // SpO2 (oxigenación) - actualmente no disponible
    float accel_x;           // Aceleración X en g
    float accel_y;           // Aceleración Y en g
    float accel_z;           // Aceleración Z en g
} sensor_payload_t;

/**
 * @brief Estructura para alertas de salud
 */
typedef struct {
    char device_id[32];      // Identificador del dispositivo
    char alert_type[32];     // Tipo de alerta ("HIGH_HEART_RATE", "LOW_SPO2", etc.)
    char severity[16];       // Severidad ("WARNING", "CRITICAL")
    char message[128];       // Mensaje descriptivo
    uint32_t heart_rate_bpm; // BPM actual
    float spo2;              // SpO2 actual
} alert_payload_t;

/**
 * @brief Inicializa la conexión MQTT y WiFi
 * @param wifi_ssid Nombre de la red WiFi
 * @param wifi_password Contraseña WiFi
 * @return ESP_OK si la inicialización fue exitosa
 */
esp_err_t mqtt_publisher_init(const char *wifi_ssid, const char *wifi_password);

/**
 * @brief Publica datos de sensores al broker MQTT
 * @param payload Estructura con los datos a enviar
 * @return ESP_OK si la publicación fue exitosa
 */
esp_err_t mqtt_publish_sensor_data(const sensor_payload_t *payload);

/**
 * @brief Publica una alerta de salud al broker MQTT
 * @param payload Estructura con los datos de la alerta
 * @return ESP_OK si la publicación fue exitosa
 */
esp_err_t mqtt_publish_alert(const alert_payload_t *payload);

/**
 * @brief Verifica si el cliente MQTT está conectado
 * @return true si está conectado, false en caso contrario
 */
bool mqtt_is_connected(void);

/**
 * @brief Detiene el cliente MQTT
 */
void mqtt_publisher_stop(void);

#endif // MQTT_PUBLISHER_H
