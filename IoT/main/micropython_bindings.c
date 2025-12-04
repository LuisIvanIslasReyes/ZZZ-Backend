#include "micropython_bindings.h"
#include "xd58c_driver.h"
#include "adxl345_driver.h"
#include "esp_log.h"
#include "py/compile.h"
#include "py/runtime.h"
#include "py/repl.h"
#include "py/gc.h"
#include "py/mperrno.h"
#include "py/stackctrl.h"

static const char *TAG = "MP_BINDINGS";

// =============================================================================
// FUNCIONES EXPUESTAS A PYTHON - Sensor XD58C
// =============================================================================

// sensors.xd58c_init()
STATIC mp_obj_t mp_xd58c_init(void) {
    esp_err_t err = xd58c_init();
    if (err != ESP_OK) {
        mp_raise_msg(&mp_type_OSError, "Error inicializando XD58C");
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mp_xd58c_init_obj, mp_xd58c_init);

// sensors.xd58c_read() -> int (valor ADC 0-4095)
STATIC mp_obj_t mp_xd58c_read(void) {
    uint32_t value;
    esp_err_t err = xd58c_read_analog(&value);
    
    if (err != ESP_OK) {
        mp_raise_msg(&mp_type_OSError, "Error leyendo XD58C");
    }
    
    return mp_obj_new_int(value);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mp_xd58c_read_obj, mp_xd58c_read);

// sensors.xd58c_voltage() -> int (voltaje en mV)
STATIC mp_obj_t mp_xd58c_voltage(void) {
    uint32_t voltage_mv;
    esp_err_t err = xd58c_read_voltage(&voltage_mv);
    
    if (err != ESP_OK) {
        mp_raise_msg(&mp_type_OSError, "Error leyendo voltaje");
    }
    
    return mp_obj_new_int(voltage_mv);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mp_xd58c_voltage_obj, mp_xd58c_voltage);

// =============================================================================
// FUNCIONES EXPUESTAS A PYTHON - Sensor ADXL345
// =============================================================================

// sensors.adxl345_init()
STATIC mp_obj_t mp_adxl345_init(void) {
    esp_err_t err = adxl345_init();
    if (err != ESP_OK) {
        mp_raise_msg(&mp_type_OSError, "Error inicializando ADXL345");
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mp_adxl345_init_obj, mp_adxl345_init);

// sensors.adxl345_read() -> (x, y, z)
STATIC mp_obj_t mp_adxl345_read(void) {
    adxl345_accel_t accel;
    esp_err_t err = adxl345_read_accel(&accel);
    
    if (err != ESP_OK) {
        mp_raise_msg(&mp_type_OSError, "Error leyendo ADXL345");
    }
    
    mp_obj_t tuple[3] = {
        mp_obj_new_float(accel.x),
        mp_obj_new_float(accel.y),
        mp_obj_new_float(accel.z)
    };
    
    return mp_obj_new_tuple(3, tuple);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mp_adxl345_read_obj, mp_adxl345_read);

// sensors.adxl345_calibrate()
STATIC mp_obj_t mp_adxl345_calibrate(void) {
    esp_err_t err = adxl345_calibrate();
    if (err != ESP_OK) {
        mp_raise_msg(&mp_type_OSError, "Error calibrando ADXL345");
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mp_adxl345_calibrate_obj, mp_adxl345_calibrate);

// =============================================================================
// FUNCIÓN PARA SER LLAMADA DESDE PYTHON - Ejemplo C callable desde Python
// =============================================================================

// sensors.log_message(msg)
STATIC mp_obj_t mp_log_message(mp_obj_t msg_obj) {
    const char *msg = mp_obj_str_get_str(msg_obj);
    ESP_LOGI("PYTHON", "%s", msg);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(mp_log_message_obj, mp_log_message);

// =============================================================================
// DEFINICIÓN DEL MÓDULO 'sensors'
// =============================================================================

STATIC const mp_rom_map_elem_t sensors_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_sensors) },
    
    // XD58C
    { MP_ROM_QSTR(MP_QSTR_xd58c_init), MP_ROM_PTR(&mp_xd58c_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_xd58c_read), MP_ROM_PTR(&mp_xd58c_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_xd58c_voltage), MP_ROM_PTR(&mp_xd58c_voltage_obj) },
    
    // ADXL345
    { MP_ROM_QSTR(MP_QSTR_adxl345_init), MP_ROM_PTR(&mp_adxl345_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_adxl345_read), MP_ROM_PTR(&mp_adxl345_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_adxl345_calibrate), MP_ROM_PTR(&mp_adxl345_calibrate_obj) },
    
    // Utilidades
    { MP_ROM_QSTR(MP_QSTR_log_message), MP_ROM_PTR(&mp_log_message_obj) },
};
STATIC MP_DEFINE_CONST_DICT(sensors_module_globals, sensors_module_globals_table);

const mp_obj_module_t sensors_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&sensors_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_sensors, sensors_module);

// =============================================================================
// INICIALIZACIÓN DE MICROPYTHON
// =============================================================================

void micropython_init(void) {
    ESP_LOGI(TAG, "Inicializando MicroPython...");
    
    // Inicializar el stack de MicroPython
    mp_stack_ctrl_init();
    mp_stack_set_limit(10240);
    
    // Inicializar el heap de MicroPython
    static uint8_t heap[128 * 1024];
    gc_init(heap, heap + sizeof(heap));
    
    // Inicializar el runtime de MicroPython
    mp_init();
    
    ESP_LOGI(TAG, "MicroPython inicializado correctamente");
}

void micropython_exec_string(const char *code) {
    nlr_buf_t nlr;
    
    if (nlr_push(&nlr) == 0) {
        // Compilar y ejecutar el código
        mp_lexer_t *lex = mp_lexer_new_from_str_len(
            MP_QSTR__lt_stdin_gt_, code, strlen(code), 0
        );
        
        qstr source_name = lex->source_name;
        mp_parse_tree_t parse_tree = mp_parse(lex, MP_PARSE_FILE_INPUT);
        mp_obj_t module_fun = mp_compile(&parse_tree, source_name, true);
        mp_call_function_0(module_fun);
        
        nlr_pop();
        ESP_LOGI(TAG, "Código Python ejecutado exitosamente");
    } else {
        // Ocurrió un error
        mp_obj_print_exception(&mp_plat_print, (mp_obj_t)nlr.ret_val);
        ESP_LOGE(TAG, "Error ejecutando código Python");
    }
}

void micropython_run_script(const char *filepath) {
    ESP_LOGI(TAG, "Ejecutando script: %s", filepath);
    
    // Aquí se implementaría la lectura del archivo desde SPIFFS
    // Por ahora, mostramos un mensaje
    ESP_LOGW(TAG, "Función micropython_run_script no implementada aún");
    ESP_LOGI(TAG, "Se debe leer el archivo '%s' desde SPIFFS y ejecutarlo", filepath);
}
