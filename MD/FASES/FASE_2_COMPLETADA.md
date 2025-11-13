# FASE 2 COMPLETADA ✅

## Sistema de Autenticación y Roles

### Resumen de lo Implementado

La Fase 2 ha sido completada exitosamente. Se implementó un sistema completo de autenticación con JWT y gestión de usuarios con tres roles jerárquicos.

---

## 📋 Componentes Creados

### 1. Modelo CustomUser (`apps/users/models.py`)

**Características:**
- Extiende `AbstractBaseUser` y `PermissionsMixin`
- Autenticación por email (no username)
- Tres roles: Admin, Supervisor, Empleado
- Relaciones jerárquicas:
  - `Admin (1) → Supervisores (N)`
  - `Supervisor (1) → Empleados (N)`
- Validación automática de jerarquía en el método `save()`
- Manager personalizado (`CustomUserManager`)

**Campos principales:**
- `email` (EmailField, unique)
- `first_name`, `last_name`
- `role` (choices: admin, supervisor, employee)
- `supervisor` (FK a User, para empleados)
- `admin` (FK a User, para supervisores)
- `is_active`, `is_staff`
- `created_at`, `updated_at`, `last_login`

**Métodos útiles:**
- `get_full_name()`, `get_short_name()`
- `is_admin()`, `is_supervisor()`, `is_employee()`
- `get_supervised_employees()`
- `get_supervisor_count()`

### 2. Serializers (`apps/users/serializers.py`)

**Serializers creados:**

1. **UserSerializer** - Lectura de usuarios
2. **UserCreateSerializer** - Creación de usuarios con validación de jerarquía
3. **UserUpdateSerializer** - Actualización de usuarios
4. **ChangePasswordSerializer** - Cambio de contraseña
5. **LoginSerializer** - Login con validación de credenciales
6. **EmployeeListSerializer** - Lista simplificada de empleados
7. **SupervisorListSerializer** - Lista de supervisores con contador de empleados

### 3. Permisos Personalizados (`apps/users/permissions.py`)

**Clases de permisos:**

1. **IsAdmin** - Solo administradores
2. **IsSupervisor** - Solo supervisores
3. **IsEmployee** - Solo empleados
4. **IsAdminOrSupervisor** - Admins y supervisores
5. **IsOwnerOrSupervisor** - Dueño, su supervisor o admin
6. **CanManageEmployees** - Gestión de empleados (supervisor/admin)
7. **CanManageSupervisors** - Gestión de supervisores (solo admin)

### 4. Vistas (Views) (`apps/users/views.py`)

**Endpoints de Autenticación:**
- `LoginView` - Login con JWT
- `LogoutView` - Logout (blacklist de token)
- `ChangePasswordView` - Cambio de contraseña
- `CurrentUserView` - Perfil del usuario actual

**Endpoints para Admin:**
- `SupervisorListCreateView` - Listar y crear supervisores
- `SupervisorDetailView` - Ver/editar/eliminar supervisor
- `AdminStatsView` - Estadísticas del sistema

**Endpoints para Supervisor:**
- `EmployeeListCreateView` - Listar y crear empleados
- `EmployeeDetailView` - Ver/editar/eliminar empleado

**Endpoints para Empleado:**
- `EmployeeProfileView` - Ver perfil propio

### 5. URLs (`apps/users/urls.py`)

**Rutas configuradas:**

```
/api/auth/login/              - POST - Login
/api/auth/logout/             - POST - Logout
/api/auth/refresh/            - POST - Refresh token JWT
/api/auth/change-password/    - POST - Cambiar contraseña
/api/auth/me/                 - GET/PUT - Perfil actual

/api/admin/supervisors/       - GET/POST - Lista y crea supervisores
/api/admin/supervisors/{id}/  - GET/PUT/DELETE - Detalle supervisor
/api/admin/stats/             - GET - Estadísticas

/api/supervisor/employees/    - GET/POST - Lista y crea empleados
/api/supervisor/employees/{id}/ - GET/PUT/DELETE - Detalle empleado

/api/employee/me/             - GET - Perfil del empleado
```

### 6. Admin Panel (`apps/users/admin.py`)

**Configuración del panel de administración:**
- Registro del modelo `CustomUser`
- Campos personalizados en el admin
- Filtros por rol, estado, fecha
- Búsqueda por email y nombre
- Optimización de queries con `select_related`

---

## 🔐 Sistema de Autenticación JWT

**Configuración en `settings.py`:**

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # Configurable vía .env
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=1440),  # 24 horas
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

**Flujo de autenticación:**

1. Usuario hace POST a `/api/auth/login/` con `{email, password}`
2. Backend valida credenciales
3. Si válido, retorna:
   ```json
   {
     "access": "token_jwt_access",
     "refresh": "token_jwt_refresh",
     "user": { datos_del_usuario }
   }
   ```
4. Cliente guarda tokens
5. Cliente usa `access` token en header: `Authorization: Bearer {token}`
6. Cuando `access` expira, usar `refresh` en `/api/auth/refresh/`

---

## 👥 Jerarquía de Roles

### Administrador
- **Puede:**
  - Crear, editar, eliminar supervisores
  - Ver todas las estadísticas del sistema
  - Acceder a todos los datos
- **No puede:**
  - Tener supervisor o admin asignado

### Supervisor
- **Puede:**
  - Crear, editar, eliminar empleados bajo su supervisión
  - Ver métricas de sus empleados
  - Gestionar dispositivos de sus empleados
  - Gestionar alertas de sus empleados
- **Debe:**
  - Tener un administrador asignado
- **No puede:**
  - Tener supervisor asignado

### Empleado
- **Puede:**
  - Ver sus propias métricas y estadísticas
  - Ver sus alertas
  - Cambiar su contraseña
- **Debe:**
  - Tener un supervisor asignado
- **No puede:**
  - Tener admin asignado

---

## 🗄️ Migraciones

**Migración creada:**
- `apps/users/migrations/0001_initial.py`

**Para aplicar (cuando PostgreSQL esté configurado):**
```bash
python manage.py migrate
```

---

## 📝 Próximos Pasos (Fase 3)

1. Configurar PostgreSQL
2. Aplicar migraciones
3. Crear superusuario
4. Crear modelos de: Device, SensorData, ProcessedMetrics
5. Crear modelos de: FatigueAlert, RoutineRecommendation

---

## ⚠️ Notas Importantes

1. **PostgreSQL no configurado**: Las migraciones se crearon pero no se aplicaron. Necesitas:
   - Instalar PostgreSQL
   - Crear la base de datos `fatigue_detection_db`
   - Configurar credenciales en `.env`

2. **Soft Delete**: Los métodos `perform_destroy` en las vistas hacen soft delete (marcan `is_active=False`) en lugar de eliminar permanentemente.

3. **Validación de jerarquía**: El modelo `CustomUser` valida automáticamente en el método `save()` que la jerarquía sea correcta.

4. **Optimización**: Las queries usan `select_related` para evitar el problema N+1.

---

## 🧪 Testing de la API (Cuando esté la BD)

### 1. Crear superusuario
```bash
python manage.py createsuperuser
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "tu_password"}'
```

### 3. Crear Supervisor (como Admin)
```bash
curl -X POST http://localhost:8000/api/admin/supervisors/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {tu_token_access}" \
  -d '{
    "email": "supervisor@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "supervisor"
  }'
```

### 4. Crear Empleado (como Supervisor)
```bash
curl -X POST http://localhost:8000/api/supervisor/employees/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {tu_token_access}" \
  -d '{
    "email": "empleado@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "María",
    "last_name": "García",
    "role": "employee"
  }'
```

---

**Estado:** ✅ FASE 2 COMPLETADA
**Siguiente:** Fase 3 - Base de Datos y Modelos
