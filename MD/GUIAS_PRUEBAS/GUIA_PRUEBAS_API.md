# 🧪 GUÍA DE PRUEBA DE LA API

## ✅ CONFIGURACIÓN COMPLETADA

- **Base de datos:** PostgreSQL conectada y migrada ✅
- **Superusuario creado:** admin@example.com / admin123 ✅
- **Servidor:** http://localhost:8000 ✅

## 📋 INSTRUCCIONES PARA PROBAR LA API

### Opción 1: Ejecución Automática del Script

1. **Abrir DOS terminales PowerShell** en el directorio del proyecto

2. **Terminal 1 - Servidor:**
   ```powershell
   cd C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
   .\venv\Scripts\Activate.ps1
   python manage.py runserver
   ```
   
3. **Terminal 2 - Pruebas:**
   ```powershell
   cd C:\Users\bauti\Downloads\respaldos\ZZZ-Backend
   .\venv\Scripts\Activate.ps1
   python test_api.py
   ```

### Opción 2: Prueba Manual con cURL o Postman

#### 1. Login (Admin)
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin123\"}"
```

**Respuesta esperada:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### 2. Obtener información del usuario autenticado
```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

**Respuesta esperada:**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "Principal",
  "role": "admin",
  "is_active": true
}
```

#### 3. Crear un Supervisor
```bash
curl -X POST http://localhost:8000/api/admin/supervisors/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"supervisor@example.com\",\"password\":\"super123\",\"password2\":\"super123\",\"first_name\":\"Juan\",\"last_name\":\"Supervisor\",\"role\":\"supervisor\"}"
```

#### 4. Listar Supervisores
```bash
curl -X GET http://localhost:8000/api/admin/supervisors/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

#### 5. Login como Supervisor
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"supervisor@example.com\",\"password\":\"super123\"}"
```

#### 6. Crear un Empleado (como Supervisor)
```bash
curl -X POST http://localhost:8000/api/supervisor/employees/ \
  -H "Authorization: Bearer {SUPERVISOR_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"employee@example.com\",\"password\":\"emp123\",\"password2\":\"emp123\",\"first_name\":\"Pedro\",\"last_name\":\"Empleado\",\"role\":\"employee\"}"
```

#### 7. Listar Empleados (como Supervisor)
```bash
curl -X GET http://localhost:8000/api/supervisor/employees/ \
  -H "Authorization: Bearer {SUPERVISOR_ACCESS_TOKEN}"
```

#### 8. Login como Empleado
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"employee@example.com\",\"password\":\"emp123\"}"
```

#### 9. Ver información del Empleado
```bash
curl -X GET http://localhost:8000/api/employee/me/ \
  -H "Authorization: Bearer {EMPLOYEE_ACCESS_TOKEN}"
```

#### 10. Cambiar Contraseña
```bash
curl -X POST http://localhost:8000/api/auth/change-password/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"old_password\":\"emp123\",\"new_password\":\"newpass123\",\"new_password2\":\"newpass123\"}"
```

#### 11. Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"{REFRESH_TOKEN}\"}"
```

#### 12. Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"{REFRESH_TOKEN}\"}"
```

## 📊 ENDPOINTS DISPONIBLES

### Autenticación (`/api/auth/`)
- ✅ `POST /api/auth/register/` - Registro
- ✅ `POST /api/auth/login/` - Login (retorna JWT)
- ✅ `POST /api/auth/refresh/` - Refresh token
- ✅ `POST /api/auth/logout/` - Logout
- ✅ `GET /api/auth/me/` - Info del usuario actual
- ✅ `PUT /api/auth/me/` - Actualizar perfil
- ✅ `POST /api/auth/change-password/` - Cambiar contraseña

### Admin (`/api/admin/`)
- ✅ `GET /api/admin/supervisors/` - Listar supervisores
- ✅ `POST /api/admin/supervisors/` - Crear supervisor
- ✅ `GET /api/admin/supervisors/{id}/` - Detalle de supervisor
- ✅ `PUT /api/admin/supervisors/{id}/` - Actualizar supervisor
- ✅ `DELETE /api/admin/supervisors/{id}/` - Eliminar supervisor (soft delete)

### Supervisor (`/api/supervisor/`)
- ✅ `GET /api/supervisor/employees/` - Listar empleados
- ✅ `POST /api/supervisor/employees/` - Crear empleado
- ✅ `GET /api/supervisor/employees/{id}/` - Detalle de empleado
- ✅ `PUT /api/supervisor/employees/{id}/` - Actualizar empleado
- ✅ `DELETE /api/supervisor/employees/{id}/` - Eliminar empleado (soft delete)

### Empleado (`/api/employee/`)
- ✅ `GET /api/employee/me/` - Mi información

## 🔐 CREDENCIALES DE PRUEBA

| Rol         | Email                    | Password    |
|-------------|--------------------------|-------------|
| Admin       | admin@example.com        | admin123    |

## 🎯 PRÓXIMOS PASOS

Una vez probada la API de autenticación, puedes continuar con:

1. **Fase 3:** Crear modelos de Device, SensorData, ProcessedMetrics, etc.
2. **Fase 4:** Integración MQTT
3. **Fase 5:** Modelo de Machine Learning
4. **Frontend:** Crear la aplicación React con TypeScript

## ⚙️ TROUBLESHOOTING

### El servidor no inicia
- Verifica que PostgreSQL esté corriendo
- Verifica las credenciales en `.env`
- Ejecuta: `python manage.py check`

### Error de conexión a la base de datos
- Verifica PostgreSQL: `psql --version`
- Verifica credenciales en `.env`
- Prueba conexión: `psql -U postgres -d fatigue_detection_db`

### Errores de migración
- Borra migraciones: elimina archivos en `apps/users/migrations/` (excepto `__init__.py`)
- Recrea: `python manage.py makemigrations`
- Aplica: `python manage.py migrate`

---

**✅ FASE 2 COMPLETADA Y PROBADA**

La API de autenticación con JWT está funcionando correctamente.
