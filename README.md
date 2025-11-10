# Sistema de Detección de Fatiga en Empleados

Sistema web para detección y análisis de fatiga en empleados mediante sensores IoT (ESP32), con Machine Learning para predicción y optimización de rutinas laborales.

## 🎯 Descripción del Proyecto

Aplicación web escolar que permite:
- Monitoreo en tiempo real de signos vitales (ritmo cardíaco, SpO2, movimiento)
- Detección automática de fatiga mediante Machine Learning
- Dashboards interactivos para Empleados y Supervisores
- Sistema de alertas y recomendaciones
- Optimización de rutinas laborales basada en datos

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** Django 4.2.7 + Django REST Framework 3.14.0
- **Base de Datos:** PostgreSQL
- **Autenticación:** JWT (djangorestframework-simplejwt)
- **IoT:** MQTT (paho-mqtt)
- **Machine Learning:** scikit-learn, pandas, numpy

### Frontend
- **Framework:** React + TypeScript
- **Build Tool:** Vite
- **UI:** DaisyUI + TailwindCSS
- **Gráficas:** Chart.js / Recharts

### Hardware
- **Dispositivo:** ESP32
- **Sensores:** Ritmo cardíaco, Acelerómetro, SpO2

## 📋 Requisitos Previos

- Python 3.11+
- PostgreSQL 14+
- Broker MQTT (Mosquitto recomendado)
- Node.js 18+ (para frontend)
- Git

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/LuisIvanIslasReyes/ZZZ-Backend.git
cd ZZZ-Backend
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv
```

**Activar el entorno virtual:**
- Windows (PowerShell):
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- Windows (CMD):
  ```cmd
  venv\Scripts\activate.bat
  ```
- Linux/Mac:
  ```bash
  source venv/bin/activate
  ```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copiar el archivo de ejemplo y editar con tus configuraciones:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
# Django Settings
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=fatigue_detection_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# MQTT Settings
MQTT_BROKER=localhost
MQTT_PORT=1883
```

### 5. Configurar PostgreSQL

Crear la base de datos:

```sql
CREATE DATABASE fatigue_detection_db;
CREATE USER postgres WITH PASSWORD 'tu_password';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'America/Mexico_City';
GRANT ALL PRIVILEGES ON DATABASE fatigue_detection_db TO postgres;
```

### 6. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 8. Ejecutar el Servidor

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://localhost:8000`

## 📁 Estructura del Proyecto

```
ZZZ-Backend/
├── apps/
│   ├── users/              # Gestión de usuarios y autenticación
│   ├── devices/            # Gestión de dispositivos ESP32
│   ├── sensors/            # Datos de sensores y métricas
│   ├── analytics/          # Alertas y recomendaciones
│   └── mqtt_client/        # Cliente MQTT
├── config/                 # Configuración de Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── ml_models/              # Modelos de Machine Learning
├── notebooks/              # Jupyter Notebooks para ML
├── .env                    # Variables de entorno (no incluir en git)
├── .env.example            # Plantilla de variables de entorno
├── .gitignore
├── requirements.txt        # Dependencias de Python
├── manage.py
└── README.md
```

## 👥 Roles de Usuario

### 1. Administrador
- Gestionar Supervisores
- Ver estadísticas globales
- Configuración del sistema

### 2. Supervisor
- Gestionar Empleados
- Gestionar Dispositivos
- Ver dashboards de su equipo
- Gestionar alertas
- Recibir recomendaciones

### 3. Empleado
- Ver sus propias métricas
- Ver su historial de fatiga
- Recibir alertas personales

## 📊 Características Principales

### Métricas Monitoreadas
- **Ritmo Cardíaco:** BPM, HRV (RMSSD, SDNN)
- **Oxigenación:** SpO2 promedio, mínimo, desaturaciones
- **Movimiento:** Nivel de actividad, varianza, entropía
- **Índice de Fatiga:** 0-100 (calculado por ML)

### Sistema de Alertas
- Fatiga alta (>70%)
- SpO2 bajo (<90%)
- Ritmo cardíaco elevado sostenido
- Inactividad sospechosa

### Machine Learning
- Clustering automático para detección de patrones
- Predicción de niveles de fatiga
- Recomendaciones personalizadas

## 🔧 Comandos Útiles

```bash
# Ejecutar servidor de desarrollo
python manage.py runserver

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Shell interactivo de Django
python manage.py shell

# Ejecutar tests
python manage.py test

# Colectar archivos estáticos
python manage.py collectstatic
```

## 📝 Estado del Proyecto

**Fase Actual:** Fase 1 - Configuración del Proyecto Base

- ✅ Entorno virtual creado
- ✅ Dependencias instaladas
- ✅ Proyecto Django inicializado
- ✅ Apps creadas (users, devices, sensors, analytics, mqtt_client)
- ✅ Configuración de settings.py
- ✅ Configuración de variables de entorno
- ⏳ Modelos de base de datos (Pendiente)
- ⏳ Autenticación JWT (Pendiente)
- ⏳ APIs REST (Pendiente)

## 📚 Próximos Pasos

1. Crear modelos de base de datos
2. Implementar autenticación JWT
3. Desarrollar APIs REST
4. Integrar cliente MQTT
5. Desarrollar modelo de Machine Learning
6. Crear frontend en React

## 👨‍💻 Autor

Luis Iván Islas Reyes - [GitHub](https://github.com/LuisIvanIslasReyes)

## 📄 Licencia

Este es un proyecto escolar.

---

**Nota:** Este proyecto simula un wearable mediante sensores IoT en ESP32 debido a limitaciones de hardware físico.
