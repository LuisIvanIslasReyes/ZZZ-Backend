# 🚀 Endpoints Esenciales - ZZZ Backend

## ✅ **LO BÁSICO PARA QUE FUNCIONE**

### 🔐 **Autenticación** 
```
POST /api/auth/login/          # Login
POST /api/auth/register/       # Registro
GET  /api/auth/profile/        # Ver perfil
PUT  /api/auth/profile/        # Actualizar perfil
```

### 📱 **Dispositivos**
```
GET  /api/devices/             # Listar dispositivos
POST /api/devices/             # Crear dispositivo
POST /api/sensor-data/         # Enviar datos del sensor
GET  /api/employees/<id>/stress/ # Ver estrés del empleado
```

### 🚨 **Alertas**
```
GET  /api/alerts/              # Ver alertas
POST /api/alerts/              # Crear alerta
PUT  /api/alerts/<id>/acknowledge/ # Reconocer alerta
GET  /api/alerts/active/       # Alertas activas
```

### 💡 **Recomendaciones**
```
GET  /api/recommendations/     # Ver recomendaciones
POST /api/recommendations/     # Crear recomendación
PUT  /api/recommendations/<id>/apply/ # Aplicar recomendación
```

### 🏢 **Departamentos**
```
GET  /api/departments/         # Listar departamentos
POST /api/departments/         # Crear departamento
GET  /api/departments/<id>/employees/ # Empleados del depto
```

---

## 🎯 **ENDPOINTS POR PRIORIDAD**

### **PRIORIDAD 1 - BÁSICO** (Lo mínimo para funcionar)
1. `POST /api/auth/login/` - Para entrar al sistema
2. `POST /api/sensor-data/` - Para recibir datos del wearable
3. `GET /api/employees/<id>/stress/` - Para ver el estrés
4. `GET /api/alerts/active/` - Para ver alertas importantes

### **PRIORIDAD 2 - GESTIÓN** (Para administrar)
5. `POST /api/auth/register/` - Registrar usuarios
6. `GET/POST /api/devices/` - Gestionar dispositivos
7. `GET/POST /api/alerts/` - Gestionar alertas
8. `GET/POST /api/departments/` - Gestionar departamentos

### **PRIORIDAD 3 - EXTRAS** (Funcionalidades avanzadas)
9. `GET/POST /api/recommendations/` - Sistema de recomendaciones
10. `GET /api/analytics/dashboard/` - Dashboard con stats
11. `GET/POST /api/configuration/` - Configuraciones del sistema

---

## 📝 **RESUMEN EJECUTIVO**

**Total de endpoints implementados:** 68+
**Apps creadas:** 8 (authentication, devices, alerts, recommendations, analytics, departments, configuration, notifications)
**Endpoints esenciales:** 15
**Endpoints de gestión:** 20
**Endpoints avanzados:** 33+

**Para empezar rápido:** Usa solo los 4 endpoints de PRIORIDAD 1
**Para funcionalidad completa:** Implementa hasta PRIORIDAD 2
**Para sistema completo:** Todos los endpoints disponibles

---

## 🔥 **QUICK START**

```bash
# 1. Login
POST /api/auth/login/
{"username": "admin", "password": "password"}

# 2. Enviar datos
POST /api/sensor-data/
{"device_id": 1, "heart_rate": 85, "activity_level": 0.7}

# 3. Ver estrés
GET /api/employees/1/stress/

# 4. Ver alertas
GET /api/alerts/active/