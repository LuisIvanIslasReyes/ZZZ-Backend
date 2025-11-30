# 📢 Endpoint: Enviar Notificación al Equipo

## 🎯 Funcionalidad

Permite al **supervisor** enviar una notificación broadcast (mensaje general) a **todos sus empleados activos** simultáneamente.

**Casos de uso:**
- 📢 Recordatorios de reuniones
- ⚠️ Avisos importantes de seguridad
- 📋 Instrucciones generales para el equipo
- 🎉 Anuncios o felicitaciones

**Nota:** Crea una alerta individual para cada empleado, así cada uno puede marcarla como leída independientemente.

---

## 📋 Especificación del Endpoint

### Request

```http
POST /api/alerts/send-team-notification/
Authorization: Bearer {token_supervisor}
Content-Type: application/json
```

### Body

```json
{
  "title": "Reunión Importante",
  "message": "Recordatorio: Reunión de equipo mañana a las 10:00 AM en la sala de juntas.",
  "priority": "medium"
}
```

### Parámetros

| Campo | Tipo | Requerido | Descripción | Valores |
|-------|------|-----------|-------------|---------|
| `title` | string | ✅ Sí | Título de la notificación | Texto libre |
| `message` | string | ✅ Sí | Mensaje completo | Texto libre |
| `priority` | string | ❌ No | Nivel de prioridad | `low`, `medium` (default), `high` |

---

## ✅ Respuesta Exitosa (201 Created)

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
    },
    {
      "employee_id": 11,
      "employee_name": "María López",
      "alert_id": 124
    }
  ]
}
```

---

## ❌ Respuestas de Error

### 400 Bad Request - Título Faltante

```json
{
  "error": "El título es obligatorio"
}
```

### 400 Bad Request - Mensaje Faltante

```json
{
  "error": "El mensaje es obligatorio"
}
```

### 400 Bad Request - Prioridad Inválida

```json
{
  "error": "Prioridad inválida. Debe ser: low, medium o high"
}
```

### 400 Bad Request - Sin Empleados

```json
{
  "error": "No tienes empleados asignados"
}
```

### 403 Forbidden - No es Supervisor

```json
{
  "error": "Solo supervisores pueden enviar notificaciones al equipo"
}
```

---

## 🔧 Implementación Frontend

### Service API

```typescript
// services/notificationService.ts

export const notificationService = {
  /**
   * Enviar notificación al equipo completo
   */
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

### Componente React

```typescript
// components/SendTeamNotificationModal.tsx

import React, { useState } from 'react';
import { notificationService } from '../services/notificationService';

interface SendTeamNotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const SendTeamNotificationModal: React.FC<SendTeamNotificationModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState({
    title: '',
    message: '',
    priority: 'medium' as 'low' | 'medium' | 'high'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await notificationService.sendTeamNotification(formData);
      
      toast.success(`✅ ${result.message}`);
      
      onSuccess();
      onClose();
      
      // Reset form
      setFormData({ title: '', message: '', priority: 'medium' });
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Error al enviar la notificación';
      setError(errorMsg);
      toast.error(`❌ ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>📢 Enviar Notificación al Equipo</h2>
        
        <form onSubmit={handleSubmit}>
          {/* Título */}
          <div className="form-group">
            <label htmlFor="title">
              Título <span className="required">*</span>
            </label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Ej: Recordatorio de descanso"
              required
              maxLength={200}
            />
          </div>

          {/* Mensaje */}
          <div className="form-group">
            <label htmlFor="message">
              Mensaje <span className="required">*</span>
            </label>
            <textarea
              id="message"
              value={formData.message}
              onChange={(e) => setFormData({ ...formData, message: e.target.value })}
              placeholder="Escribe tu mensaje aquí..."
              required
              rows={5}
              maxLength={1000}
            />
            <small>{formData.message.length}/1000 caracteres</small>
          </div>

          {/* Prioridad */}
          <div className="form-group">
            <label htmlFor="priority">Prioridad</label>
            <select
              id="priority"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
            >
              <option value="low">🟢 Baja - Información</option>
              <option value="medium">🟡 Media - Recordatorio</option>
              <option value="high">🔴 Alta - Urgente</option>
            </select>
          </div>

          {/* Vista previa */}
          <div className="preview-box">
            <h4>Vista previa:</h4>
            <div className="notification-preview">
              <strong>📢 {formData.title || 'Título de la notificación'}</strong>
              <p>{formData.message || 'Tu mensaje aparecerá aquí...'}</p>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div className="alert alert-error">
              ⚠️ {error}
            </div>
          )}

          {/* Botones */}
          <div className="modal-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !formData.title || !formData.message}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Enviando...
                </>
              ) : (
                <>
                  ⚡ Enviar Notificación
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

---

### CSS

```css
/* SendTeamNotificationModal.css */

.preview-box {
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.notification-preview {
  background: white;
  border-left: 4px solid #4CAF50;
  padding: 12px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.notification-preview strong {
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
  color: #333;
}

.notification-preview p {
  margin: 0;
  color: #666;
  line-height: 1.5;
  white-space: pre-wrap;
}

.required {
  color: #f44336;
}

.alert-error {
  background: #ffebee;
  border-left: 4px solid #f44336;
  padding: 12px;
  margin: 16px 0;
  border-radius: 4px;
}
```

---

### Uso en Dashboard

```typescript
// pages/SupervisorDashboard.tsx

const [showNotificationModal, setShowNotificationModal] = useState(false);

return (
  <div className="dashboard">
    <header>
      <h1>Dashboard del Supervisor</h1>
      <button
        className="btn btn-primary"
        onClick={() => setShowNotificationModal(true)}
      >
        📢 Enviar Notificación al Equipo
      </button>
    </header>

    <SendTeamNotificationModal
      isOpen={showNotificationModal}
      onClose={() => setShowNotificationModal(false)}
      onSuccess={() => {
        // Opcional: recargar alertas o mostrar confirmación adicional
        console.log('Notificación enviada exitosamente');
      }}
    />

    {/* Resto del dashboard */}
  </div>
);
```

---

## 🔄 Flujo Completo

```
1. Supervisor abre modal "Enviar Notificación"
       ↓
2. Llena formulario:
   - Título: "Reunión Importante"
   - Mensaje: "Mañana a las 10 AM"
   - Prioridad: "medium"
       ↓
3. Click en "Enviar Notificación"
       ↓
4. POST /api/alerts/send-team-notification/
       ↓
5. Backend crea una FatigueAlert para cada empleado
       ↓
6. Respuesta: "Notificación enviada a 5 empleados"
       ↓
7. Frontend muestra toast de éxito
       ↓
8. Empleados ven la alerta en su dashboard
```

---

## 📊 Cómo se Muestra en el Dashboard del Empleado

Cuando un empleado recibe la notificación, verá:

```
┌─────────────────────────────────────────┐
│ 🔔 Nueva Alerta - Prioridad: Media     │
├─────────────────────────────────────────┤
│ 📢 Reunión Importante                   │
│                                         │
│ Recordatorio: Reunión de equipo        │
│ mañana a las 10:00 AM en la sala       │
│ de juntas.                              │
│                                         │
│ ✉️ De: Supervisor López                 │
│ 📅 30/11/2025 - 15:30                   │
│                                         │
│ [✓ Marcar como Leída]                  │
└─────────────────────────────────────────┘
```

---

## ✅ Características

✅ **Solo supervisores** pueden enviar notificaciones  
✅ **Validación** de campos requeridos  
✅ **Vista previa** antes de enviar  
✅ **Prioridades** visuales (low/medium/high)  
✅ **Contador** de empleados notificados  
✅ **Toast** de confirmación  
✅ **Historial** en tabla de alertas  

---

## 🧪 Testing

### Prueba Manual

1. Login como supervisor
2. Abrir modal "Enviar Notificación al Equipo"
3. Llenar formulario con datos de prueba
4. Enviar
5. Verificar respuesta 201 con lista de empleados
6. Login como empleado
7. Verificar que aparece la alerta en el dashboard

---

## 📝 Notas Técnicas

- Las notificaciones se crean como `FatigueAlert` con el mensaje formateado
- El formato del mensaje es: `📢 {title}\n\n{message}`
- Solo se envía a empleados **activos** (`is_active=True`)
- El supervisor debe tener empleados asignados
- Las alertas se pueden resolver individualmente desde el dashboard del empleado

---

**Fecha:** 30/11/2025  
**Endpoint:** `/api/alerts/send-team-notification/`  
**Método:** POST  
**Permisos:** Supervisor, Admin  
**Status:** ✅ Implementado
