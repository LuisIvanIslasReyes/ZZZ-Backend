Preguntas y supuestos
1. ¿El wearable se conecta por Bluetooth o el wearable sube datos a un gateway móvil propietario?
2. ¿Se requiere soporte iOS además de Android?
3. ¿Frecuencia de muestreo esperada y tolerancia a pérdida de paquetes?

Notas y siguientes pasos
- Probar emparejamiento con un dispositivo de referencia y crear un mock de payloads de sensor.

Actualizaciones según tus respuestas
- Autenticación: local con usuario y contraseña; la app móvil gestionará el login y almacenamiento seguro del JWT (keystore/secure storage).
- Conectividad: BLE; el móvil actúa como gateway. La app debe recolectar muestras y enviar batches comprimidos al backend a intervalos (ej. cada 1-5 minutos) o al finalizar la jornada.
- Volumen: diseño para 1 wearable en la práctica, pero acepta batches y estructura escalable para múltiples dispositivos en el futuro.
- Sensores: HR (y SpO2 si está disponible) y acelerómetro. Recomendación para prototipo: muestreo HR cada 1s y acelerómetro a 10Hz durante ventanas de interés, pero puedes reducir para ahorro de batería.
- Retención: raw 30 días, agregados 365 días (consistente con backend).

Recomendaciones técnicas
- Uso de SQLite (o Realm) para cache local y cola de subida; usar expo-notifications o FCM para push.
- Manejo de permisos Android: location background si BLE lo requiere, permisos de actividad física, y manejo de energía.

# Contexto técnico — Móvil (React Native)

Resumen rápido
- Stack recomendado: React Native (Expo para prototipado rápido o React Native CLI para control nativo), TypeScript, React Navigation, Redux or Zustand, React Native BLE library para conexión con wearables (si corresponde), and SQLite/AsyncStorage for local caching.
- Propósito: App para empleados que se conecta al wearable, muestra datos de jornada, sincroniza con backend y permite configurar privacidad y consentimiento.

Requisitos funcionales clave
- Login de empleado (JWT)
- Emparejar wearable (Bluetooth LE) o registrar device id
- Mostrar timeline de la jornada: HR, pasos, descansos, score de estrés
- Sincronización en background y subida por batches
- Notificaciones y alertas (locales)

Contrato con Backend
- Endpoints: /api/auth/, /api/devices/, /api/sensor-data/ (batch upload), /api/employees/{id}/stress
- Mecanismo de sync: enqueue samples localmente y subir cada X minutos o cuando haya buena conectividad

Arquitectura local
- Capa de persistencia: SQLite para series temporales, usar WatermelonDB o Realm para datos offline de alta frecuencia
- Background tasks: Headless JS (Android) y Background Fetch (iOS)

Consideraciones hardware
- BLE pairing reliability; reconexión automática; manejo de permisos de Android (foreground, background location si necesario para BLE)

Preguntas y supuestos
1. ¿El wearable se conecta por Bluetooth o el wearable sube datos a un gateway móvil propietario?
2. ¿Se requiere soporte iOS además de Android?
3. ¿Frecuencia de muestreo esperada y tolerancia a pérdida de paquetes?

Notas y siguientes pasos
- Probar emparejamiento con un dispositivo de referencia y crear un mock de payloads de sensor.
