idf_component_register(
    SRCS 
        "main.c"
        "xd58c_driver.c"
        "adxl345_driver.c"
        "mqtt_publisher.c"
        # "micropython_bindings.c"  # Comentado - MicroPython no instalado
    INCLUDE_DIRS "."
    REQUIRES 
        driver
        esp_adc
        nvs_flash
        spiffs
        esp_wifi
        esp_netif
        esp_event
        mqtt
)
