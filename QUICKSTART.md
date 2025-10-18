# 🚀 Guía de Inicio Rápido

Esta guía te llevará desde cero hasta tener el backend funcionando en menos de 5 minutos.

## Opción 1: Docker (Más Fácil) ⭐

### 1. Instalar Docker Desktop
- Windows/Mac: https://www.docker.com/products/docker-desktop
- Verifica: `docker --version`

### 2. Clonar y Configurar
```powershell
# Clonar repo
git clone <url>
cd ZZZ-Backend

# Copiar variables de entorno
copy .env.example .env

# Levantar todo
docker-compose up --build
```

### 3. Crear Datos de Demo
En otra terminal:
```powershell
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py create_demo_data
```

### 4. ¡Listo! 🎉
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- Docs: http://localhost:8000/api/docs/

**Login:**
- Email: `juan.perez@stressmonitor.com`
- Password: `employee123`

## Opción 2: Local (Sin Docker)

### 1. Instalar Python 3.11+
- Windows: https://www.python.org/downloads/

### 2. Instalar PostgreSQL y Redis
- PostgreSQL: https://www.postgresql.org/download/
- Redis: https://redis.io/download (o usar Redis en Docker)

### 3. Setup del Proyecto
```powershell
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar .env y editar con tus credenciales de DB
copy .env.example .env
notepad .env

# Migraciones
python manage.py migrate
python manage.py create_demo_data

# Iniciar servidor
python manage.py runserver
```

### 4. Iniciar Celery (en otra terminal)
```powershell
venv\Scripts\activate
celery -A config worker -l info
```

## 🧪 Probar la API

### Con cURL (PowerShell)
```powershell
# Login
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login/" -Method POST -Body (@{email="juan.perez@stressmonitor.com"; password="employee123"} | ConvertTo-Json) -ContentType "application/json"
$token = $response.access

# Ver perfil
Invoke-RestMethod -Uri "http://localhost:8000/api/auth/profile/" -Headers @{Authorization="Bearer $token"}
```

### Con Postman
1. Importa la colección desde `/docs/postman_collection.json` (crear)
2. O usa Swagger UI en http://localhost:8000/api/docs/

### Generar Datos de Prueba
```powershell
python scripts/generate_mock_data.py
```

## 📱 Siguiente Paso: Conectar con Frontend

Una vez que el backend esté corriendo, puedes conectar:

1. **Web App** (React): Configurar `API_BASE_URL=http://localhost:8000`
2. **Mobile App** (React Native): Usar tu IP local `http://192.168.x.x:8000`
3. **Wearable**: Conectar vía Bluetooth al móvil

## ❓ Problemas Comunes

### Error: "No module named 'django'"
```powershell
pip install -r requirements.txt
```

### Error: "Connection refused" (PostgreSQL)
Verifica que PostgreSQL esté corriendo:
```powershell
# Windows
Get-Service postgresql*
```

### Error: Celery no procesa tasks
Asegúrate de que Redis esté corriendo y Celery worker esté activo.

### Puerto 8000 ocupado
Cambia el puerto:
```powershell
python manage.py runserver 8001
```

## 📚 Recursos Adicionales

- [README completo](README.md)
- [Arquitectura de ML](docs/ml-architecture.md)
- [API Endpoints](README.md#-api-endpoints)
- Swagger Docs: http://localhost:8000/api/docs/

## 🆘 Ayuda

Si algo no funciona, revisa:
1. Los logs: `docker-compose logs -f web`
2. Variables de entorno en `.env`
3. Que todos los servicios estén corriendo

---

**¡Feliz desarrollo! 🚀**
