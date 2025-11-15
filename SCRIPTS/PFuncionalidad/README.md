# 🔧 Pruebas de Funcionalidad del Backend

## 📋 Descripción

Este directorio contiene las **pruebas de funcionalidad** del backend del Sistema de Detección de Fatiga. Estas pruebas verifican que cada endpoint de la API REST funcione correctamente y devuelva las respuestas esperadas.

---

## 🎯 ¿Qué son las Pruebas de Funcionalidad?

Las pruebas de funcionalidad verifican que cada componente del sistema funcione según lo especificado:

- ✅ **Endpoints responden correctamente** con códigos de estado apropiados
- ✅ **Autenticación funciona** (login, tokens JWT)
- ✅ **CRUD operations** en dispositivos, sensores, métricas, etc.
- ✅ **Filtros y ordenamiento** funcionan correctamente
- ✅ **Paginación** opera como se espera
- ✅ **Validaciones** rechazan datos incorrectos
- ✅ **Manejo de errores** es apropiado (404, 401, 405, etc.)
- ✅ **Documentación** de API está accesible

---

## 📁 Archivos

### `generar_evidencia_pdf.py` ⭐ (RECOMENDADO)
Script que genera un **documento PDF profesional** con todas las evidencias.

**Características:**
- 18 pruebas funcionales automatizadas
- Documento PDF listo para entregar
- Formato profesional con tablas y resumen
- Incluye respuestas del servidor en cada prueba
- Organizado por categorías
- **Ideal para entregar al docente**

### `test_funcionalidad_backend.py`
Script alternativo que genera reportes HTML y JSON.

**Características:**
- 20 pruebas funcionales automatizadas
- Generación de reportes HTML interactivos
- Reportes JSON para procesamiento
- Evidencias detalladas de cada prueba

---

## 🚀 Cómo Ejecutar las Pruebas

### Prerrequisitos

1. **Backend activo en `http://localhost:8000`**
   ```powershell
   cd C:\Users\misam\OneDrive\Documentos\GitHub\ZZZ-Backend
   .\.venv\Scripts\Activate.ps1
   python manage.py runserver
   ```

2. **Base de datos configurada y migrada**
   ```powershell
   python manage.py migrate
   ```

3. **Usuario de prueba creado**
   - Email: `admin@example.com`
   - Password: `admin123`
   
   Si no existe, créalo:
   ```powershell
   python manage.py createsuperuser
   ```

### Ejecutar las Pruebas

#### Opción 1: Generar PDF (RECOMENDADO) ⭐

```powershell
# Desde el directorio raíz del proyecto
cd C:\Users\misam\OneDrive\Documentos\GitHub\ZZZ-Backend

# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Generar evidencia en PDF
python SCRIPTS\PFuncionalidad\generar_evidencia_pdf.py
```

**Ventajas:**
- Documento PDF profesional listo para entregar
- Más fácil de abrir y compartir
- Incluye todas las evidencias en un solo archivo
- Formato ideal para impresión

#### Opción 2: Generar HTML/JSON

```powershell
# Ejecutar las pruebas con reporte HTML
python SCRIPTS\PFuncionalidad\test_funcionalidad_backend.py
```

**Ventajas:**
- Reporte HTML interactivo
- Archivo JSON para procesamiento automático
- Más detalles visuales

### Salida Esperada

```
🚀 Iniciando Pruebas de Funcionalidad del Backend
   Sistema de Detección de Fatiga

======================================================================
PRUEBAS DE FUNCIONALIDAD DEL BACKEND
Sistema de Detección de Fatiga
======================================================================

🔐 Autenticando usuario de prueba...
✅ Autenticación exitosa

📋 CATEGORÍA: AUTENTICACIÓN
----------------------------------------------------------------------
✅ PASS [1] Login Exitoso
   Verifica que un usuario puede autenticarse con credenciales válidas
   Status: 200

✅ PASS [2] Login con Credenciales Inválidas
   Verifica que se rechacen credenciales incorrectas (esperado: 400 o 401)
   Status: 400

...

======================================================================
RESUMEN DE PRUEBAS DE FUNCIONALIDAD
======================================================================
Total de pruebas ejecutadas: 20
Pruebas exitosas: 18 ✅
Pruebas fallidas: 2 ❌
Tasa de éxito: 90.0%
======================================================================

✅ Reporte JSON generado: [RUTA]/evidencia_funcionalidad_[TIMESTAMP].json
✅ Reporte HTML generado: [RUTA]/evidencia_funcionalidad_[TIMESTAMP].html
```

---

## 📊 Pruebas Incluidas

### 🔐 Autenticación (3 pruebas)
- **PF-001:** Login exitoso con credenciales válidas
- **PF-002:** Login con credenciales inválidas debe fallar
- **PF-003:** Login sin campos requeridos debe fallar

### 📱 Dispositivos (3 pruebas)
- **PF-004:** Listar todos los dispositivos
- **PF-005:** Filtrar dispositivos activos
- **PF-006:** Acceso sin autenticación debe fallar

### 📊 Datos de Sensores (3 pruebas)
- **PF-007:** Listar datos de sensores
- **PF-008:** Ordenar datos por fecha descendente
- **PF-009:** Paginación de datos

### 📈 Métricas Procesadas (2 pruebas)
- **PF-010:** Listar métricas procesadas
- **PF-011:** Filtrar métricas por nivel de actividad

### 🚨 Alertas (2 pruebas)
- **PF-012:** Listar alertas de fatiga
- **PF-013:** Filtrar alertas activas

### 💡 Recomendaciones (2 pruebas)
- **PF-014:** Listar recomendaciones
- **PF-015:** Filtrar recomendaciones por tipo

### 📚 Documentación (3 pruebas)
- **PF-016:** Schema OpenAPI disponible
- **PF-017:** Swagger UI disponible
- **PF-018:** ReDoc disponible

### ⚠️ Manejo de Errores (2 pruebas)
- **PF-019:** Endpoint no existente retorna 404
- **PF-020:** Método HTTP no permitido retorna 405

---

## 📄 Reportes Generados

### Documento PDF ⭐ (Opción recomendada)
`EVIDENCIA_FUNCIONALIDAD_YYYYMMDD_HHMMSS.pdf`

**Incluye:**
- 📄 **Portada profesional** con título y fecha
- 📊 **Tabla resumen** con estadísticas generales:
  - Total de pruebas
  - Pruebas exitosas/fallidas
  - Tasa de éxito
  - URL del backend
- 📋 **Pruebas organizadas por categorías**:
  - 🔐 Autenticación
  - 📱 Dispositivos
  - 📊 Datos de Sensores
  - 📈 Métricas Procesadas
  - 🚨 Alertas
  - 💡 Recomendaciones
  - 📚 Documentación
  - ⚠️ Manejo de Errores
- ✅ **Cada prueba incluye**:
  - ID de prueba (PF-XXX)
  - Nombre y descripción
  - Resultado (✅ exitoso / ❌ fallido)
  - Endpoint probado
  - Método HTTP
  - Status code
  - Timestamp
  - Respuesta del servidor
- 🖨️ **Listo para imprimir o entregar digitalmente**

### Reporte HTML (Alternativo)
`evidencia_funcionalidad_YYYYMMDD_HHMMSS.html`

**Incluye:**
- 📊 Resumen visual con estadísticas
- 🎨 Diseño profesional y responsive
- ✅ Indicadores de éxito/fallo por prueba
- 📝 Detalles completos de cada prueba
- 🏷️ Organización por categorías
- 🖨️ Se puede convertir a PDF desde el navegador

### Reporte JSON (Alternativo)
`evidencia_funcionalidad_YYYYMMDD_HHMMSS.json`

**Contiene:**
- Metadata de ejecución
- Resultados estructurados de todas las pruebas
- Estadísticas completas
- Ideal para procesamiento automático

---

## 💾 Cómo Guardar las Evidencias

### Opción 1: Usar el PDF Generado ⭐ (RECOMENDADO)
El documento PDF ya está listo para entregar directamente.

```powershell
# Abrir el PDF más reciente
$latest = Get-ChildItem -Path "SCRIPTS\PFuncionalidad\EVIDENCIA_FUNCIONALIDAD_*.pdf" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Invoke-Item $latest.FullName
```

**Ventajas:**
- ✅ Ya está en formato PDF
- ✅ Listo para subir a la plataforma
- ✅ Se puede imprimir directamente
- ✅ Formato profesional

### Opción 2: Convertir HTML a PDF
Si usaste el generador HTML:

1. Abre el archivo HTML en el navegador
2. Presiona `Ctrl+P` (Imprimir)
3. Selecciona "Guardar como PDF"
4. Guarda el archivo

### Opción 3: Copiar a Carpeta de Entrega
```powershell
# Crear carpeta de evidencias
New-Item -Path "Evidencias_Entrega" -ItemType Directory -Force

# Copiar el PDF más reciente
$latestPDF = Get-ChildItem -Path "SCRIPTS\PFuncionalidad\EVIDENCIA_FUNCIONALIDAD_*.pdf" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Copy-Item $latestPDF.FullName -Destination "Evidencias_Entrega\"

# También copiar README como documentación
Copy-Item "SCRIPTS\PFuncionalidad\README.md" -Destination "Evidencias_Entrega\"
```

---

## 🔧 Personalización

### Cambiar Credenciales de Prueba

Edita las líneas 11-14 en `test_funcionalidad_backend.py`:

```python
TEST_USER = {
    "email": "tu_email@example.com",
    "password": "tu_contraseña"
}
```

### Cambiar URL del Backend

Edita la línea 8:

```python
BASE_URL = "http://localhost:8000"  # Cambia aquí
```

### Agregar Nuevas Pruebas

```python
def test_mi_nueva_funcionalidad(self):
    """PF-XXX: Descripción de la prueba"""
    try:
        response = requests.get(
            f"{API_URL}/mi-endpoint/",
            headers=self.headers,
            timeout=10
        )
        
        self.log_result(
            "Categoría",
            "Nombre de la Prueba",
            "Descripción detallada de qué se está probando",
            response.status_code == 200,
            response.status_code,
            request_info={"endpoint": "/api/mi-endpoint/", "method": "GET"}
        )
    except Exception as e:
        self.log_result("Categoría", "Nombre", "Descripción", False, error=e)
```

---

## 📈 Interpretación de Resultados

### Códigos de Estado HTTP
- **200 OK:** Solicitud exitosa
- **201 Created:** Recurso creado exitosamente
- **400 Bad Request:** Datos de entrada inválidos
- **401 Unauthorized:** No autenticado (falta token)
- **403 Forbidden:** No autorizado (sin permisos)
- **404 Not Found:** Recurso no encontrado
- **405 Method Not Allowed:** Método HTTP no soportado
- **500 Internal Server Error:** Error del servidor

### Tasa de Éxito
- 🟢 **90-100%:** Excelente - Backend funcionando correctamente
- 🟡 **70-89%:** Bueno - Algunos problemas menores
- 🔴 **<70%:** Requiere atención - Revisar errores

---

## 🐛 Troubleshooting

### Error: "Connection refused"
**Causa:** El backend no está corriendo  
**Solución:** Inicia el servidor Django con `python manage.py runserver`

### Error: "Authentication failed"
**Causa:** Credenciales incorrectas o usuario no existe  
**Solución:** Verifica las credenciales en el script o crea el usuario

### Algunas pruebas fallan con 401
**Causa:** Token de autenticación no válido  
**Solución:** Verifica que el login inicial sea exitoso

### Error: "Port 8000 already in use"
**Causa:** Ya hay un servidor corriendo en ese puerto  
**Solución:** Detén el servidor anterior o usa otro puerto

---

## 📞 Soporte

Para más información sobre el proyecto:
- **Documentación:** `MD/PROJECT_CONTEXT.md`
- **Guías de pruebas:** `MD/GUIAS_PRUEBAS/`
- **Troubleshooting:** `MD/ERRORS/TROUBLESHOOTING.md`

---

## 📝 Para la Entrega

### Entrega Recomendada ⭐
Sube el documento PDF generado:
- ✅ **`EVIDENCIA_FUNCIONALIDAD_[TIMESTAMP].pdf`** - Documento principal

Este archivo contiene:
- Todas las pruebas ejecutadas
- Resultados detallados
- Respuestas del servidor
- Formato profesional listo para entregar

### Entrega Alternativa
Si prefieres otros formatos:
1. ✅ Reporte HTML (`evidencia_funcionalidad_*.html`)
2. ✅ Reporte JSON (`evidencia_funcionalidad_*.json`)
3. ✅ Este README como documentación

### Entrega Completa (Opcional)
Para una entrega más completa:
1. ✅ PDF de evidencias (principal)
2. ✅ README.md (documentación del proceso)
3. ✅ Screenshots adicionales (opcional)

---

**¡Éxito con tus pruebas! 🎉**
