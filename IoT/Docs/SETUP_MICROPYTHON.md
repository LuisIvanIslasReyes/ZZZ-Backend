# 🔧 Configuración Rápida - MicroPython en ESP-IDF

## ⚡ Inicio Rápido (3 pasos)

### 1️⃣ Preparar Entorno

```powershell
# Abrir terminal en VSCode y configurar ESP-IDF
cd C:\Utt\ZZZ\ZZZ-Backend\IoT

# Configurar target
idf.py set-target esp32
```

### 2️⃣ Agregar MicroPython

**IMPORTANTE**: Antes de compilar, debes agregar MicroPython como componente.

#### Opción Simple (Sin submódulo git):

```powershell
# Crear carpeta components
New-Item -ItemType Directory -Force -Path components

# Descargar MicroPython
cd components
git clone --depth 1 --recursive https://github.com/micropython/micropython.git

# Volver a raíz
cd ..
```

#### Configuración del componente MicroPython:

Crear archivo `components/micropython/CMakeLists.txt`:

```cmake
idf_component_register(
    SRCS 
        "py/runtime.c"
        "py/gc.c"
        "py/parse.c"
        "py/compile.c"
        # ... agregar más archivos según necesites
    INCLUDE_DIRS 
        "."
        "py"
    REQUIRES 
        driver
)
```

**Alternativa más simple**: Usar solo las cabeceras de MicroPython y enlazar con una biblioteca precompilada.

### 3️⃣ Compilar y Flashear

```powershell
# Compilar
idf.py build

# Flashear (ajustar puerto COM)
idf.py -p COM3 flash monitor
```

---

## 🚨 Problema: MicroPython es muy grande

**Realidad**: Integrar MicroPython completo requiere:
- ~1MB de código adicional
- Configuración compleja de makefiles
- Tiempo de compilación largo

### ✅ Solución Práctica: Enfoque Híbrido

En lugar de compilar MicroPython completo, usa un **enfoque simplificado**:

#### Arquitectura Recomendada:

```
┌─────────────────────────────────────┐
│   Firmware Principal (C/C++)        │
│   - Drivers de sensores             │
│   - FreeRTOS                        │
│   - Control de hardware             │
└─────────┬───────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│   Intérprete Ligero                 │
│   Opciones:                         │
│   1. MicroPython (runtime mínimo)   │
│   2. Lua (más ligero)               │
│   3. Python scripts precompilados   │
└─────────────────────────────────────┘
```

---

## 🎯 Alternativa 1: MicroPython Runtime Mínimo

Usa solo el parser y runtime de MicroPython:

```c
// Incluir solo headers necesarios
#include "py/compile.h"
#include "py/runtime.h"
#include "py/gc.h"

// Compilar solo con archivos esenciales:
// py/runtime.c, py/gc.c, py/compile.c, py/parse.c, py/lexer.c
```

**CMakeLists.txt del componente**:

```cmake
set(MICROPYTHON_DIR ${CMAKE_CURRENT_LIST_DIR}/micropython)

idf_component_register(
    SRCS
        "${MICROPYTHON_DIR}/py/runtime.c"
        "${MICROPYTHON_DIR}/py/gc.c"
        "${MICROPYTHON_DIR}/py/compile.c"
        "${MICROPYTHON_DIR}/py/parse.c"
        "${MICROPYTHON_DIR}/py/lexer.c"
        "${MICROPYTHON_DIR}/py/obj.c"
        "${MICROPYTHON_DIR}/py/objstr.c"
        "${MICROPYTHON_DIR}/py/objlist.c"
        "${MICROPYTHON_DIR}/py/objdict.c"
        "${MICROPYTHON_DIR}/py/objtuple.c"
        "${MICROPYTHON_DIR}/py/builtinimport.c"
        "${MICROPYTHON_DIR}/py/vm.c"
        "${MICROPYTHON_DIR}/py/showbc.c"
        "${MICROPYTHON_DIR}/py/repl.c"
        "${MICROPYTHON_DIR}/py/smallint.c"
        "${MICROPYTHON_DIR}/py/frozenmod.c"
    INCLUDE_DIRS
        "${MICROPYTHON_DIR}"
        "${MICROPYTHON_DIR}/py"
    REQUIRES
        driver
        nvs_flash
)
```

---

## 🎯 Alternativa 2: Usar Lua (Más ligero)

Lua es mucho más fácil de integrar y más pequeño (~200KB):

```powershell
# Descargar Lua
cd components
git clone https://github.com/lua/lua.git
```

**Ejemplo de uso en C**:

```c
#include "lua.h"
#include "lualib.h"
#include "lauxlib.h"

void run_lua_script(const char *script) {
    lua_State *L = luaL_newstate();
    luaL_openlibs(L);
    
    luaL_dostring(L, script);
    
    lua_close(L);
}
```

---

## 🎯 Alternativa 3: Scripts Python Precompilados (.mpy)

Usa `mpy-cross` para precompilar scripts y cargarlos más rápido:

```powershell
# Instalar mpy-cross
pip install mpy-cross

# Compilar script
mpy-cross scripts/sensor_monitor.py

# Resultado: sensor_monitor.mpy (más pequeño y rápido)
```

---

## 📋 Decisión: ¿Qué usar?

| Opción | Tamaño | Complejidad | Compatibilidad Python | Recomendación |
|--------|--------|-------------|----------------------|---------------|
| **MicroPython Completo** | ~1MB | Alta | 100% | Solo si necesitas Python puro |
| **MicroPython Mínimo** | ~300KB | Media | 80% | ✅ Mejor balance |
| **Lua** | ~200KB | Baja | 0% (sintaxis diferente) | Si no te importa cambiar sintaxis |
| **Solo C** | 0KB | Ninguna | 0% | ✅ Máximo rendimiento |

---

## ✨ Recomendación Final para tu Proyecto

**Usa MicroPython Mínimo** con este setup:

### Estructura Simplificada:

```
IoT/
├── CMakeLists.txt
├── main/
│   ├── main.c                    # ✅ Ya creado
│   ├── max30102_driver.c         # ✅ Ya creado
│   ├── adxl345_driver.c          # ✅ Ya creado
│   └── CMakeLists.txt
├── components/
│   └── micropython_minimal/      # ← Crear esto
│       ├── CMakeLists.txt
│       ├── mpy_bindings.c
│       └── micropython/          # Clonar repo
└── scripts/
    └── sensor_monitor.py         # ✅ Ya creado
```

### Pasos para implementar:

1. **Clonar MicroPython**:
```powershell
cd C:\Utt\ZZZ\ZZZ-Backend\IoT
New-Item -ItemType Directory -Force -Path components\micropython_minimal
cd components\micropython_minimal
git clone --depth 1 https://github.com/micropython/micropython.git
```

2. **Crear componente mínimo** (archivo `components/micropython_minimal/CMakeLists.txt`):

```cmake
set(MPY_DIR ${CMAKE_CURRENT_LIST_DIR}/micropython)

idf_component_register(
    SRCS
        "mpy_bindings.c"
    INCLUDE_DIRS
        "."
        "${MPY_DIR}"
        "${MPY_DIR}/py"
    REQUIRES
        driver
)

# Agregar definiciones necesarias
target_compile_definitions(${COMPONENT_LIB} PRIVATE
    MICROPY_ENABLE_GC=1
    MICROPY_HELPER_REPL=1
)
```

3. **Actualizar** `main/CMakeLists.txt` para requerir el componente:

```cmake
idf_component_register(
    SRCS 
        "main.c"
        "max30102_driver.c"
        "adxl345_driver.c"
        "micropython_bindings.c"
    INCLUDE_DIRS "."
    REQUIRES 
        driver
        nvs_flash
        spiffs
        micropython_minimal  # ← Agregar esto
)
```

---

## ⚠️ Nota Importante

Por simplicidad, **el código ya creado funciona sin MicroPython** si comentas las partes de Python.

Para empezar a probar **solo con C**:

1. Comenta estas líneas en `main.c`:
```c
// micropython_init();  // ← Comentar
// xTaskCreate(test_sensors_task_python, ...);  // ← Comentar
```

2. Compila y prueba:
```powershell
idf.py build flash monitor
```

3. Verás los sensores funcionando en C puro.

4. Luego, cuando quieras agregar Python, sigue los pasos anteriores.

---

**¿Quieres que genere el setup completo de MicroPython mínimo, o prefieres empezar solo con C?**
