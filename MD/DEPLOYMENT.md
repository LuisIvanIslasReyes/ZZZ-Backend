# Guía de Despliegue - Sistema de Detección de Fatiga

## 📋 Contenido

1. [Despliegue con Docker](#despliegue-con-docker)
2. [Despliegue Manual](#despliegue-manual)
3. [Configuración de Producción](#configuración-de-producción)
4. [Monitoreo y Logs](#monitoreo-y-logs)
5. [Backup y Restauración](#backup-y-restauración)

---

## 🐳 Despliegue con Docker

### Prerequisitos

- Docker >= 20.10
- Docker Compose >= 2.0
- 4GB RAM mínimo
- 20GB espacio en disco

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/your-org/ZZZ-Backend.git
cd ZZZ-Backend
```

### Paso 2: Configurar Variables de Entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

**Variables críticas:**
- `SECRET_KEY`: Generar nueva clave para producción
- `DEBUG=False`
- `ALLOWED_HOSTS`: Dominios de producción
- `DB_PASSWORD`: Contraseña segura

### Paso 3: Construir y Ejecutar

```bash
# Construcción
docker-compose build

# Ejecutar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Paso 4: Migraciones e Inicialización

```bash
# Ejecutar migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Colectar archivos estáticos
docker-compose exec backend python manage.py collectstatic --noinput
```

### Paso 5: Entrenar Modelo ML

```bash
docker-compose exec backend python train_ml_model.py
```

### Verificación

```bash
# Verificar servicios
docker-compose ps

# Acceder a:
# - API: http://localhost:8000/api/docs/
# - Admin: http://localhost:8000/admin/
# - MQTT: mqtt://localhost:1883
```

---

## 🔧 Despliegue Manual

### Prerequisitos

- Python 3.11+
- PostgreSQL 15+
- MQTT Broker (Mosquitto)
- Nginx (opcional)

### Paso 1: Instalar PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Crear base de datos
sudo -u postgres createdb fatigue_detection_db
sudo -u postgres createuser --password postgres
```

### Paso 2: Instalar Mosquitto

```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### Paso 3: Configurar Python

```bash
# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 4: Configurar Aplicación

```bash
# Copiar variables de entorno
cp .env.example .env
# Editar .env

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Colectar estáticos
python manage.py collectstatic
```

### Paso 5: Ejecutar Servicios

```bash
# Terminal 1: Django
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Terminal 2: MQTT Client
python -c "from apps.mqtt_client.apps import MqttClientConfig; MqttClientConfig.start_mqtt_client()"
```

---

## 🚀 Configuración de Producción

### Security Settings

Actualizar `config/settings.py`:

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### Nginx como Reverse Proxy

```bash
sudo cp nginx/nginx.conf /etc/nginx/sites-available/fatigue-detection
sudo ln -s /etc/nginx/sites-available/fatigue-detection /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL con Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Systemd Services

**Django Service (`/etc/systemd/system/fatigue-backend.service`):**

```ini
[Unit]
Description=Fatigue Detection Backend
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/ZZZ-Backend
Environment="PATH=/var/www/ZZZ-Backend/venv/bin"
ExecStart=/var/www/ZZZ-Backend/venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start fatigue-backend
sudo systemctl enable fatigue-backend
```

---

## 📊 Monitoreo y Logs

### Docker Logs

```bash
# Ver logs en tiempo real
docker-compose logs -f backend

# Últimas 100 líneas
docker-compose logs --tail=100 backend

# Logs de MQTT
docker-compose logs -f mqtt_client
```

### Logs del Sistema

```bash
# Django logs
tail -f /var/log/fatigue-detection/django.log

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# PostgreSQL logs
tail -f /var/log/postgresql/postgresql-15-main.log
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/docs/

# Database
docker-compose exec db pg_isready

# MQTT
mosquitto_sub -h localhost -t '$SYS/#' -C 1
```

---

## 💾 Backup y Restauración

### Backup de Base de Datos

```bash
# Manual
docker-compose exec db pg_dump -U postgres fatigue_detection_db > backup_$(date +%Y%m%d).sql

# Automatizado (cron)
0 2 * * * /path/to/backup.sh
```

**Script `backup.sh`:**

```bash
#!/bin/bash
BACKUP_DIR=/backups
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U postgres fatigue_detection_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

### Restauración

```bash
# Desde backup
docker-compose exec -T db psql -U postgres fatigue_detection_db < backup.sql

# Desde gzip
gunzip < backup.sql.gz | docker-compose exec -T db psql -U postgres fatigue_detection_db
```

### Backup de Modelos ML

```bash
tar -czf ml_models_backup_$(date +%Y%m%d).tar.gz ml_models/
```

---

## 🔄 Actualización del Sistema

```bash
# Detener servicios
docker-compose down

# Pull nuevo código
git pull origin main

# Rebuild
docker-compose build

# Migrar base de datos
docker-compose run backend python manage.py migrate

# Iniciar servicios
docker-compose up -d
```

---

## ⚡ Optimización de Performance

### PostgreSQL Tuning

```bash
# /etc/postgresql/15/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
max_connections = 100
```

### Gunicorn Workers

```bash
# Fórmula: (2 x CPU cores) + 1
gunicorn config.wsgi --workers 9 --threads 2 --worker-class gthread
```

---

## 🐛 Troubleshooting

### Backend no inicia

```bash
# Verificar logs
docker-compose logs backend

# Verificar configuración
docker-compose exec backend python manage.py check

# Verificar migraciones
docker-compose exec backend python manage.py showmigrations
```

### Base de datos no conecta

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps db

# Probar conexión
docker-compose exec backend python manage.py dbshell
```

### MQTT no funciona

```bash
# Verificar broker
mosquitto_sub -h localhost -t 'test' -v

# Publicar mensaje de prueba
mosquitto_pub -h localhost -t 'test' -m 'hello'
```

---

## 📚 Referencias

- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

**Última actualización:** 11 de Noviembre, 2025
