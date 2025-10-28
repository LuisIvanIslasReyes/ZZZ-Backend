# 🚀 Endpoints Básicos - ZZZ Backend (VERSIÓN SIMPLE)

## ✅ **SOLO LO ESENCIAL PARA QUE FUNCIONE**

### 🔐 **Autenticación** 
```
POST /api/auth/login/          # Login
POST /api/auth/register/       # Registro  
GET  /api/auth/profile/        # Ver perfil
PUT  /api/auth/profile/        # Actualizar perfil
```

### 📱 **Dispositivos y Sensores**
```
GET  /api/devices/             # Listar dispositivos
POST /api/devices/             # Crear dispositivo
POST /api/sensor-data/         # Enviar datos del sensor
GET  /api/employees/<id>/stress/ # Ver estrés del empleado
```

---

## 🎯 **SOLO 8 ENDPOINTS BÁSICOS**

1. `POST /api/auth/login/` - Para entrar al sistema
2. `POST /api/auth/register/` - Registrar usuarios
3. `GET /api/auth/profile/` - Ver perfil del usuario
4. `PUT /api/auth/profile/` - Actualizar perfil
5. `GET /api/devices/` - Ver dispositivos
6. `POST /api/devices/` - Crear dispositivo
7. `POST /api/sensor-data/` - Recibir datos del wearable
8. `GET /api/employees/<id>/stress/` - Ver estrés en tiempo real

---

## 🔥 **QUICK START**

```bash
# 1. Registrar usuario
POST /api/auth/register/
{"username": "admin", "password": "password123", "email": "admin@example.com"}

# 2. Login
POST /api/auth/login/
{"username": "admin", "password": "password123"}

# 3. Crear dispositivo
POST /api/devices/
{"name": "Smartwatch-001", "device_type": "wearable", "employee": 1}

# 4. Enviar datos del sensor
POST /api/sensor-data/
{"device_id": 1, "heart_rate": 85, "activity_level": 0.7}

# 5. Ver estrés del empleado
GET /api/employees/1/stress/
```

---

## 📝 **RESUMEN PELADO**

**Apps activas:** 2 (authentication, devices)
**Endpoints totales:** 8
**Apps eliminadas:** alerts, recommendations, analytics, departments, configuration, notifications

✅ **Simple**
✅ **Funcional** 
✅ **Sin complicaciones**

¡Solo lo básico compa! 🎯