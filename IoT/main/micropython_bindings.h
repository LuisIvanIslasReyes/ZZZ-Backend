#ifndef MICROPYTHON_BINDINGS_H
#define MICROPYTHON_BINDINGS_H

#include "py/runtime.h"

/**
 * @brief Inicializa el intérprete de MicroPython
 */
void micropython_init(void);

/**
 * @brief Ejecuta un script de Python desde el sistema de archivos
 * @param filepath Ruta al archivo .py
 */
void micropython_run_script(const char *filepath);

/**
 * @brief Ejecuta código Python desde una cadena
 * @param code Código Python a ejecutar
 */
void micropython_exec_string(const char *code);

/**
 * @brief Registra el módulo personalizado 'sensors' en MicroPython
 */
void register_sensors_module(void);

#endif // MICROPYTHON_BINDINGS_H
