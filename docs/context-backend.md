# Contexto técnico — Backend (Django REST Framework)

Resumen rápido
- Stack recomendado: Python 3.11+, Django 4.x, Django REST Framework (DRF), PostgreSQL (PostGIS opcional si se usa geolocalización), Redis (cache y celery broker), Celery para tareas asíncronas.
- Propósito: Exponer API REST/GraphQL para el ecosistema (web, móvil, wearable). Ingesta, procesamiento y almacenamiento de datos de sensores, cálculo de métricas de estrés, endpoints para autenticación, y paneles de supervisión.

Contrato mínimo inicial (endpoints clave)
- POST /api/auth/login/ — credenciales -> token (JWT)
- POST /api/auth/register/ — registro de empleado
- GET /api/employees/{id}/ — perfil
- POST /api/devices/ — registrar wearable vinculado al empleado
- POST /api/sensor-data/ — ingestión masiva de paquetes de sensores (tachy, accel, pasos, etc.)
- GET /api/employees/{id}/stress/ — resumen y serie temporal del nivel de estrés
- GET /api/supervisor/reports/ — endpoints agregados para el panel de supervisores

Modelos iniciales (esquema simplificado)
- Employee
  - id, nombre, correo, puesto, equipo_id, timezone
- Device
  - id, empleado (FK), device_type, hardware_id, last_seen
- SensorPacket
  - id, device(FK), timestamp, raw_payload (JSONB), processed (bool)
- SensorSample
  - id, packet(FK), sample_time, hr, acc_x, acc_y, acc_z, steps, battery_level
- StressAggregate
  - id, employee(FK), window_start, window_end, stress_score, method_version

Procesamiento y ML
- Pipeline: ingestion -> validation -> feature extraction -> scoring ML -> persist
- ML: modelo inicial puede ser un modelo off-line (scikit-learn/xgboost) que se ejecuta en batch o via Celery. Posteriormente mover a TorchServe o endpoints de inferencia separados.
- Telemetría: guardar versiones de modelo y metadatos de entrenamiento para trazabilidad.

Autenticación y seguridad
- JWT (SimpleJWT) para APIs públicas; tokens de rotación opcionales.
- Scopes/roles: empleado, supervisor, admin. Policy basada en DRF permissions.
- Validación de payloads grandes: usar streaming uploads y limitar tamaño por petición.

Escalabilidad y rendimiento
- Base de datos: particionado por tiempo o employee si crece mucho.
- Redis para caching y rate limiting.
- Celery + Redis/RabbitMQ para procesamientos pesados.
- Endpoints de ingestión optimizados: aceptar batches, compresión gzip.

Observabilidad
- Logging JSON, métricas (Prometheus), traces (OpenTelemetry)

Requisitos de privacidad
- PII: cifrado en reposo, políticas de retención, consentimiento explícito.

Preguntas y supuestos
1. ¿Habrá autenticación centralizada (SSO) o solo local (email/password)?
2. ¿Con qué frecuencia y volumen envía datos el wearable? (ej. 1 muestra/segundo)
3. ¿Necesitan datos en tiempo real (<5s) para alertas o es suficiente procesamiento en batch?
4. ¿Qué sensores exactamente estarán disponibles (HR, HRV, acelerómetro, SPO2, etc.)?
5. ¿Deseas almacenar raw payloads completos o solo features procesadas?
6. ¿Cómo será la relación empleado-supervisor (jerarquía, equipos, anonimizacion)?

Notas y siguientes pasos
- Implementar endpoints de ingestión y modelos de test con Celery.
- Configurar infra mínima (Postgres, Redis) y un pipeline CI con migraciones y pruebas.

Actualizaciones según tus respuestas
- Autenticación: usar autenticación local (email/contraseña) con JWT (SimpleJWT) y roles Admin>Supervisor>Empleado.
- Conectividad: el móvil actúa como gateway BLE; el backend recibirá datos en batches desde la app móvil.
- Volumen: aunque el diseño debe ser escalable, el proyecto escolar trabajará con 1 wearable a la vez. Diseña ingestión por batches y almacenamiento eficiente (aceptar batches comprimidos).
- Sensores: HR (con posible SpO2) y acelerómetro. Guardar raw payloads por un periodo corto (ej. 30 días) y features agregadas por más tiempo (ej. 1 año).

Retención y privacidad (explicación breve)
- Retención: es la política que define cuánto tiempo guardas cada tipo de dato. Recomendación para proyecto escolar:
  - Raw sensor payloads: 30 días (reduce coste y riesgo)
  - Features/aggregates: 365 días
  - Logs y metadatos: 90 días
- Anonimización: para análisis históricos, considera anonimizar o pseudonimizar datos (hash del id) si vas a compartir resultados.

Notificaciones
- Para push notifications (empleado y supervisor) recomendamos Firebase Cloud Messaging (FCM). El backend tendrá un servicio encargado de enviar notificaciones cuando un batch produca una alerta.

Infra mínima sugerida para un proyecto escolar
- Dockerizar la app y usar un proveedor simple (Render, Railway, DigitalOcean App Platform) o desplegar en un droplet si ya usas DigitalOcean. Recomendación: empezar con una instancia gestionada de Postgres + Redis pequeño.

