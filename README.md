# 🩺 Stress Monitor - Backend API

Sistema de monitoreo de estrés en empleados mediante sensores de wearables. Backend construido con Django REST Framework.

## 📋 Descripción

Sistema que calcula el nivel de estrés en los empleados de una empresa a través de los sensores del wearable (referencia: Redmi Watch 5 Active) con la finalidad de encontrar patrones que ayuden a tomar decisiones a los supervisores para que sus empleados sean más productivos.

### Componentes del Ecosistema

- **Backend (este repo)**: API REST en Django + DRF
- **Web**: Panel para supervisores (React)
- **Móvil**: App para empleados (React Native)
- **Wearable**: Lectura de sensores (Android/Kotlin)

## 🏗️ Arquitectura

```
┌─────────────┐      BLE      ┌──────────────┐     HTTPS     ┌─────────────┐
│  Wearable   │ ──────────────▶│ Mobile App   │ ─────────────▶│  Backend    │
│  (Android)  │                │ (React       │               │  (Django)   │
│             │                │  Native)     │               │             │
└─────────────┘                └──────────────┘               └──────┬──────┘
                                                                     │
                                     ┌───────────────────────────────┤
                                     │                               │
                              ┌──────▼──────┐                 ┌──────▼──────┐
                              │  PostgreSQL │                 │   Celery    │
                              │             │                 │  (Worker)   │
                              └─────────────┘                 └──────┬──────┘
                                                                     │
                                                              ┌──────▼──────┐
                                                              │    Redis    │
                                                              └─────────────┘
```

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- Git

### Configuración con Docker (Recomendado)

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd ZZZ-Backend
```

2. **Copiar variables de entorno**
```bash
cp .env.example .env
```

3. **Construir y levantar contenedores**
```bash
docker-compose up --build
```

4. **Ejecutar migraciones y crear datos demo**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py create_demo_data
```

5. **Acceder a la aplicación**
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- Docs: http://localhost:8000/api/docs/

### Configuración Local (Sin Docker)

1. **Crear entorno virtual**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos**
Asegúrate de tener PostgreSQL y Redis corriendo localmente, luego edita `.env` con tus credenciales.

4. **Ejecutar migraciones**
```bash
python manage.py migrate
python manage.py create_demo_data
```

5. **Iniciar servidor**
```bash
python manage.py runserver
```

6. **Iniciar Celery (en otra terminal)**
```bash
celery -A config worker -l info
```

## 📡 API Endpoints

### Autenticación

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register/` | Registrar nuevo usuario | No |
| POST | `/api/auth/login/` | Login (obtener JWT) | No |
| POST | `/api/auth/refresh/` | Refrescar token | No |
| GET | `/api/auth/profile/` | Obtener perfil | Sí |
| PUT | `/api/auth/profile/` | Actualizar perfil | Sí |
| POST | `/api/auth/change-password/` | Cambiar contraseña | Sí |
| POST | `/api/auth/fcm-token/` | Registrar token FCM | Sí |
| GET | `/api/auth/employees/` | Listar empleados | Sí |
| GET | `/api/auth/employees/{id}/` | Detalle de empleado | Sí |

### Dispositivos

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/devices/` | Listar dispositivos | Sí |
| POST | `/api/devices/` | Registrar dispositivo | Sí |
| GET | `/api/devices/{id}/` | Detalle de dispositivo | Sí |
| PUT | `/api/devices/{id}/` | Actualizar dispositivo | Sí |
| DELETE | `/api/devices/{id}/` | Eliminar dispositivo | Sí |

### Datos de Sensores

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| POST | `/api/sensor-data/` | Ingestión batch de datos | Sí |
| GET | `/api/employees/{id}/stress/` | Obtener datos de estrés | Sí |
| GET | `/api/employees/{id}/stress/summary/` | Resumen de estrés | Sí |

### Supervisores

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/supervisor/reports/` | Reportes agregados | Supervisor+ |

## 🔐 Autenticación

El sistema usa JWT (JSON Web Tokens) para autenticación.

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan.perez@stressmonitor.com",
    "password": "employee123"
  }'
```

**Respuesta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Usar token en peticiones
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

## 📊 Ingestión de Datos

### Formato de Batch

```json
{
  "device_id": "WATCH-EMP-001",
  "firmware_version": "1.0.0",
  "samples": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "hr": 75,
      "spo2": 98.5,
      "accel_x": 0.1,
      "accel_y": 0.2,
      "accel_z": 9.8,
      "steps": 1500,
      "battery": 85
    }
  ]
}
```

### Generar Datos de Prueba

Usa el script incluido para generar datos mock:

```bash
python scripts/generate_mock_data.py
```

Este script:
- Se autentica con la API
- Genera muestras realistas de sensores
- Envía batches cada 60 segundos
- Simula patrones de estrés durante el día

## 👥 Roles y Permisos

### Admin
- Acceso completo a todos los recursos
- Gestión de usuarios
- Acceso al panel de Django Admin

### Supervisor
- Ver empleados supervisados
- Acceder a reportes agregados
- Ver datos de estrés de su equipo

### Employee (Empleado)
- Registrar dispositivos propios
- Enviar datos de sensores
- Ver su propio historial de estrés

## 🧪 Tests

### Ejecutar todos los tests
```bash
# Con Docker
docker-compose exec web pytest

# Local
pytest
```

### Ejecutar con cobertura
```bash
pytest --cov=apps --cov-report=html
```

### Ver reporte de cobertura
```bash
# Se genera en htmlcov/index.html
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
```

## 🔧 Comandos Útiles

### Management Commands

```bash
# Crear datos de demostración
python manage.py create_demo_data

# Crear superusuario
python manage.py createsuperuser

# Limpiar datos antiguos
python manage.py shell
>>> from apps.devices.tasks import cleanup_old_data
>>> cleanup_old_data()
```

### Celery

```bash
# Iniciar worker
celery -A config worker -l info

# Iniciar beat (tareas programadas)
celery -A config beat -l info

# Monitorear tareas
celery -A config events
```

## 📁 Estructura del Proyecto

```
ZZZ-Backend/
├── apps/
│   ├── authentication/      # App de usuarios y autenticación
│   │   ├── models.py        # User, Employee
│   │   ├── views.py         # Endpoints de auth
│   │   ├── serializers.py
│   │   ├── permissions.py   # Permisos por rol
│   │   └── management/
│   │       └── commands/
│   │           └── create_demo_data.py
│   └── devices/             # App de dispositivos y sensores
│       ├── models.py        # Device, SensorPacket, SensorSample, StressAggregate
│       ├── views.py         # Endpoints de ingestión y reportes
│       ├── serializers.py
│       ├── tasks.py         # Celery tasks
│       └── admin.py
├── config/
│   ├── settings/
│   │   ├── base.py          # Settings compartidos
│   │   ├── development.py   # Settings de desarrollo
│   │   └── production.py    # Settings de producción
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py            # Configuración de Celery
├── docs/                    # Documentación de contexto
├── scripts/                 # Scripts de utilidad
│   ├── entrypoint.sh        # Docker entrypoint
│   └── generate_mock_data.py
├── tests/                   # Tests
│   ├── conftest.py
│   ├── factories.py
│   ├── test_authentication.py
│   └── test_devices.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pytest.ini
├── requirements.txt
└── README.md
```

## 🗄️ Modelos de Datos

### User
- Sistema de autenticación personalizado
- Roles: Admin, Supervisor, Employee
- Email como username

### Employee
- Perfil extendido del usuario
- Relación con supervisor
- Token FCM para notificaciones

### Device
- Wearables registrados por empleado
- Hardware ID único
- Estado activo/inactivo

### SensorPacket
- Paquete crudo de datos recibidos
- Payload JSON
- Estado de procesamiento

### SensorSample
- Muestras individuales extraídas
- HR, SpO2, Acelerómetro, Pasos, Batería

### StressAggregate
- Score de estrés calculado
- Ventana de tiempo
- Features agregadas (avg HR, HRV, movement)

## 🤖 Procesamiento de Estrés

### Algoritmo v1.0 (Heurístico)

El cálculo actual es un modelo heurístico simple:

```python
stress_score = (hr_component * 0.4) + (hrv_component * 0.3) + (movement_component * 0.3)
```

**Componentes:**
- **Heart Rate (40%)**: HR elevado indica posible estrés
- **HRV (30%)**: Baja variabilidad indica estrés
- **Movement (30%)**: Contexto de actividad física

### Futuro: Machine Learning

Para producción, se debe entrenar un modelo supervisado:

1. **Recolectar datos etiquetados**
   - Encuestas de auto-reporte
   - Eventos de estrés conocidos
   
2. **Feature Engineering**
   - HR, HRV, RMSSD
   - Frecuencia de movimiento
   - Contexto temporal (hora, día)
   
3. **Entrenar modelo**
   - XGBoost, LightGBM o Red Neuronal
   - Validación cruzada
   - Métricas: Accuracy, F1-Score
   
4. **Deploy**
   - TorchServe o TensorFlow Serving
   - Endpoint de inferencia
   - Versionado de modelos

## 🔔 Notificaciones

### FCM (Firebase Cloud Messaging)

1. **Registrar token en la app móvil**
```bash
POST /api/auth/fcm-token/
{
  "fcm_token": "firebase-token-here"
}
```

2. **El sistema enviará notificaciones cuando:**
   - Score de estrés > 75 (alto)
   - Al empleado afectado
   - Al supervisor del empleado

## 🛡️ Seguridad

- JWT con rotación de tokens
- HTTPS en producción
- CORS configurado
- Rate limiting (pendiente implementar)
- Validación de datos de entrada
- Permisos por rol

## 📈 Monitoreo y Logs

Los logs están configurados en formato JSON estructurado.

### Ver logs en Docker
```bash
docker-compose logs -f web
docker-compose logs -f celery
```

### Niveles de log
- INFO: Operaciones normales
- WARNING: Situaciones anormales pero manejables
- ERROR: Errores que requieren atención

## 🚀 Despliegue en Producción

### Checklist

- [ ] Cambiar `SECRET_KEY` en `.env`
- [ ] Configurar `ALLOWED_HOSTS`
- [ ] Usar base de datos gestionada (RDS, Cloud SQL)
- [ ] Configurar Redis gestionado
- [ ] Habilitar HTTPS
- [ ] Configurar backups automáticos
- [ ] Configurar monitoreo (Sentry, New Relic)
- [ ] Configurar rate limiting
- [ ] Revisar políticas de retención de datos

### Proveedores Recomendados

- **Render**: Fácil, deployment automático desde Git
- **Railway**: Similar a Render, buen free tier
- **DigitalOcean App Platform**: Escalable, buen precio
- **Heroku**: Clásico, fácil pero más caro
- **AWS/GCP/Azure**: Máximo control, más complejo

## 📞 Credenciales de Demo

Después de ejecutar `create_demo_data`:

| Rol | Email | Password |
|-----|-------|----------|
| Admin | admin@stressmonitor.com | admin123 |
| Supervisor | supervisor@stressmonitor.com | supervisor123 |
| Employee | juan.perez@stressmonitor.com | employee123 |

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este es un proyecto académico.

## 📧 Contacto

Para preguntas sobre el proyecto, contacta al equipo de desarrollo.

---

**Proyecto desarrollado como parte de un trabajo escolar de monitoreo de estrés en empleados.**
