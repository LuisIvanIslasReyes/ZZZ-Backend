# ✅ FIX: Endpoint de Notificaciones al Equipo

## 🐛 Problema Encontrado

En la captura de pantalla se ve:

```
POST http://localhost:8000/api/alerts/send_team_notification 500
Error: No se pudo enviar la notificación. Intenta de nuevo.
```

**Causa:** El endpoint `/api/alerts/send-team-notification/` **NO EXISTÍA** en el backend.

---

## ✅ Solución Aplicada

### Endpoint Creado

```http
POST /api/alerts/send-team-notification/
Authorization: Bearer {token_supervisor}
```

**Request Body:**
```json
{
  "title": "Título de la notificación",
  "message": "Mensaje para el equipo",
  "priority": "medium"  // Opcional: low, medium, high
}
```

**Response (201 Created):**
```json
{
  "message": "Notificación enviada exitosamente a 5 empleado(s)",
  "title": "Reunión Importante",
  "priority": "medium",
  "employees_notified": 5,
  "alerts": [
    {
      "employee_id": 10,
      "employee_name": "Juan Pérez",
      "alert_id": 123
    }
  ]
}
```

---

## 🎯 Funcionalidad

✅ **Notificación broadcast al equipo completo**  
✅ Supervisor envía **UN mensaje** que llega a **TODOS sus empleados**  
✅ Crea una **FatigueAlert** individual para cada empleado  
✅ Cada empleado puede marcar su notificación como leída independientemente  
✅ Valida título y mensaje obligatorios  
✅ Soporta 3 niveles de prioridad: `low`, `medium`, `high`  
✅ Devuelve lista de empleados notificados  
✅ Solo supervisores y admins pueden usar este endpoint  

**Casos de uso:**
- 📢 "Reunión de equipo mañana 10 AM"
- ⚠️ "Recordatorio: usar equipo de protección"
- 📋 "Nueva política de descansos activa"  

---

## 📋 Para el Frontend

### El endpoint esperado está **listo**:

**URL correcta:**
```
POST /api/alerts/send-team-notification/
```

**Nota:** Usar guion `-` en lugar de guion bajo `_`  
Frontend usa: `send_team_notification` ❌  
Backend espera: `send-team-notification` ✅  

### Cambio Necesario en Frontend:

```typescript
// ❌ ANTES
const response = await api.post('/alerts/send_team_notification/', data);

// ✅ AHORA
const response = await api.post('/alerts/send-team-notification/', data);
```

---

## 🔧 Service Correcto

```typescript
// services/notificationService.ts

export const notificationService = {
  async sendTeamNotification(data: {
    title: string;
    message: string;
    priority?: 'low' | 'medium' | 'high';
  }) {
    const response = await api.post('/alerts/send-team-notification/', data);
    return response.data;
  }
};
```

---

## ✅ Validaciones del Backend

El endpoint valida:

1. ✅ **Permisos:** Solo supervisor/admin
2. ✅ **Título:** Obligatorio, no vacío
3. ✅ **Mensaje:** Obligatorio, no vacío
4. ✅ **Prioridad:** Solo `low`, `medium`, `high`
5. ✅ **Empleados:** Supervisor debe tener empleados asignados

**Errores posibles:**

| Status | Error | Solución |
|--------|-------|----------|
| 400 | "El título es obligatorio" | Enviar `title` no vacío |
| 400 | "El mensaje es obligatorio" | Enviar `message` no vacío |
| 400 | "Prioridad inválida" | Usar `low`, `medium` o `high` |
| 400 | "No tienes empleados asignados" | Supervisor sin empleados |
| 403 | "Solo supervisores..." | Usuario no es supervisor |

---

## 🧪 Cómo Probar

### 1. Con curl (PowerShell):

```powershell
# Login como supervisor
$login = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method POST -Body (@{email="supervisor@empresa.com";password="password123"} | ConvertTo-Json) -ContentType "application/json"

$token = $login.access

# Enviar notificación
$body = @{
  title = "Reunión de Equipo"
  message = "Mañana a las 10 AM en la sala de juntas"
  priority = "medium"
} | ConvertTo-Json

$headers = @{
  "Authorization" = "Bearer $token"
  "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/alerts/send-team-notification/" -Method POST -Headers $headers -Body $body
```

### 2. Desde el Frontend:

```typescript
// Hacer login como supervisor
const { access } = await authService.login('supervisor@empresa.com', 'password123');

// Enviar notificación
const result = await notificationService.sendTeamNotification({
  title: 'Reunión de Equipo',
  message: 'Mañana a las 10 AM',
  priority: 'medium'
});

console.log(result);
// {
//   message: "Notificación enviada exitosamente a 5 empleado(s)",
//   employees_notified: 5,
//   ...
// }
```

---

## 📊 Resultado

✅ **Endpoint creado:** `/api/alerts/send-team-notification/`  
✅ **Documentación:** `DOCS/API_TEAM_NOTIFICATION.md`  
✅ **Permisos:** Solo supervisor/admin  
✅ **Validaciones:** Completas  
✅ **Testing:** Listo para probar  

---

## 🎯 Qué Decirle al Frontend

**Mensaje corto:**

> El endpoint de notificaciones ya está listo. Solo necesitan cambiar la URL de:
> 
> ❌ `/api/alerts/send_team_notification/`  
> ✅ `/api/alerts/send-team-notification/`  
> 
> (Usar guion `-` en lugar de guion bajo `_`)
> 
> Documentación completa en: `DOCS/API_TEAM_NOTIFICATION.md`

---

**Fecha:** 30/11/2025  
**Problema:** Endpoint no existía (500 error)  
**Solución:** ✅ Endpoint implementado  
**Cambio Frontend:** Usar guion en URL  
**Status:** ✅ Listo para usar
