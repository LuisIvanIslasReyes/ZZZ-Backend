Preguntas y supuestos
1. ¿El hardware objetivo (Redmi 5 Watch Active) permite extracción de HR/HRV y accesibilidad de acelerómetro por terceros?
2. ¿Se debe soportar actualización OTA de firmware o telemetría de salud del propio wearable?
3. ¿Conexión directa al backend desde wearable es necesaria o siempre pasa por móvil?

Notas y siguientes pasos
- Crear prototipo en Android que capture datos y envíe paquetes simulados al móvil.

Actualizaciones según tus respuestas
- Conectividad: BLE; el móvil hará de gateway.
- Sensores: HR (y SpO2 si disponible) y acelerómetro son los requeridos.
- Tiempo real: no necesario; el wearable debe batchear y enviar al móvil.

Recomendación de hardware económico
- Si buscas alternativas económicas con mejor soporte de sensores y comunidad, considera:
	- Amazfit Bip U / Bip U Pro: económico, HR + SpO2 y buena comunidad para hacks.
	- Xiaomi Mi Band 6/7: muy barato, HR y SpO2; la extracción de datos puede requerir usar la API de la app o técnicas no oficiales.
	- Realme Watch / Redmi Watch (variedades): similares al original; verifica acceso a sensores en SDK.

Nota práctica
- Para el prototipo escolar, usar un wearable que puedas controlar desde Android (o simular datos) es suficiente. Recomiendo comprar un Amazfit Bip U o una Mi Band si el precio es crítico; para facilidad de desarrollo, un dispositivo con SDK oficial (más caro) ahorra tiempo.

# Contexto técnico — Wearable (Android)

Resumen rápido
- Stack recomendado: Android Studio, Kotlin, Android SDK targeting API 26+; usar WorkManager para tareas background y BLE APIs para conexión con mobile. Considerar uso de Wear OS si se pretende compatibilidad amplia.
- Propósito: Lectura de sensores (HR, acelerómetro, pasos, batería), preprocesamiento ligero, empuje de paquetes al móvil y UI mínima para el empleado.

Requisitos funcionales clave
- Leer HR, acelerómetro, pasos, batería
- Buffer local y envío por BLE (o BLE/GATT) al móvil
- UI: indicador de conexión, estado de batería, feedback de estrés en tiempo real
- Gestión de permisos y consumo de energía

Formato de paquete sugerido
- JSON comprimido (ejemplo): { device_id, ts_start, ts_end, samples: [{t, hr, ax, ay, az, steps}], firmware_version }

Consideraciones de energía
- Muestreo adaptativo: aumentar frecuencia en actividad y reducir en reposo
- Usar batching para reducir consumo y reconexiones frecuentes

Preguntas y supuestos
1. ¿El hardware objetivo (Redmi 5 Watch Active) permite extracción de HR/HRV y accesibilidad de acelerómetro por terceros?
2. ¿Se debe soportar actualización OTA de firmware o telemetría de salud del propio wearable?
3. ¿Conexión directa al backend desde wearable es necesaria o siempre pasa por móvil?

Notas y siguientes pasos
- Crear prototipo en Android que capture datos y envíe paquetes simulados al móvil.
