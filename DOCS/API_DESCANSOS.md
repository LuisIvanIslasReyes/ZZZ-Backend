# 📋 API - Gestión de Descansos (Scheduled Breaks)

## 🎯 Endpoints Disponibles

### Para SUPERVISORES

**📌 IMPORTANTE:** Todos los endpoints de supervisor muestran datos de **TODOS los empleados** asignados al supervisor, no solo de uno.

#### 1️⃣ Ver Descansos Pendientes de Aprobación
**Muestra TODOS los descansos pendientes de TODOS los empleados del supervisor**
```http
GET /api/scheduled-breaks/pending/
Authorization: Bearer <token>
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "employee": {
      "id": 5,
      "full_name": "Juan Pérez",
      "email": "juan@example.com"
    },
    "break_type": "rest",
    "break_type_display": "Descanso",
    "scheduled_date": "2025-11-30",
    "scheduled_time": "14:00:00",
    "duration_minutes": 15,
    "reason": "Fatiga por alta carga de trabajo",
    "status": "pending",
    "reviewed_by": null,
    "review_date": null,
    "review_comment": null,
    "created_at": "2025-11-29T10:30:00Z"
  }
]
```

---

#### 2️⃣ Ver Historial de Descansos (Aprobados/Rechazados)
**📌 Historial completo del supervisor: Ve TODOS los descansos que ha revisado de TODOS sus empleados**

```http
GET /api/scheduled-breaks/?status=approved
GET /api/scheduled-breaks/?status=rejected
GET /api/scheduled-breaks/  # Todos
Authorization: Bearer <token>
```

**Respuesta:** (Array con TODOS los descansos de TODOS los empleados del supervisor)
```json
[
  {
    "id": 2,
    "employee": {
      "id": 5,
      "full_name": "Juan Pérez"
    },
    "break_type": "medical",
    "break_type_display": "Médico",
    "scheduled_date": "2025-11-28",
    "scheduled_time": "10:00:00",
    "duration_minutes": 30,
    "status": "approved",
    "reviewed_by": {
      "id": 2,
      "full_name": "Supervisor López"
    },
    "review_date": "2025-11-27T15:30:00Z",
    "review_comment": "Aprobado por razones médicas",
    "created_at": "2025-11-26T09:00:00Z"
  },
  {
    "id": 3,
    "employee": {
      "id": 8,
      "full_name": "María González"
    },
    "break_type": "rest",
    "break_type_display": "Descanso",
    "scheduled_date": "2025-11-27",
    "scheduled_time": "15:30:00",
    "duration_minutes": 15,
    "status": "rejected",
    "reviewed_by": {
      "id": 2,
      "full_name": "Supervisor López"
    },
    "review_date": "2025-11-26T14:20:00Z",
    "review_comment": "No es momento apropiado",
    "created_at": "2025-11-26T10:15:00Z"
  }
]
```

**💡 Nota:** El backend automáticamente filtra para que cada supervisor solo vea descansos de sus empleados asignados.

**Filtros disponibles:**
```javascript
// Por estado
?status=pending
?status=approved
?status=rejected
?status=completed
?status=cancelled

// Por tipo de descanso
?break_type=rest
?break_type=meal
?break_type=medical
?break_type=bathroom
?break_type=other

// Por fecha
?scheduled_date=2025-11-30

// Ordenar
?ordering=scheduled_date
?ordering=-scheduled_date  // Descendente
?ordering=created_at
```

---

#### 3️⃣ Aprobar/Rechazar Descanso
```http
POST /api/scheduled-breaks/{id}/review/
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "approved",  // o "rejected"
  "review_comment": "Aprobado por razones médicas"  // Opcional
}
```

**Respuesta (200):**
```json
{
  "message": "Descanso aprobado exitosamente",
  "break": {
    "id": 1,
    "employee": {...},
    "status": "approved",
    "reviewed_by": {
      "id": 2,
      "full_name": "Supervisor López"
    },
    "review_date": "2025-11-29T16:45:00Z",
    "review_comment": "Aprobado por razones médicas"
  }
}
```

---

#### 4️⃣ Ver Descansos de Hoy
```http
GET /api/scheduled-breaks/today/
Authorization: Bearer <token>
```

---

#### 5️⃣ Ver Descansos Próximos (7 días)
```http
GET /api/scheduled-breaks/upcoming/
Authorization: Bearer <token>
```

---

### Para EMPLEADOS

#### 6️⃣ Programar Nuevo Descanso
```http
POST /api/scheduled-breaks/
Authorization: Bearer <token>
Content-Type: application/json

{
  "break_type": "rest",
  "scheduled_date": "2025-11-30",
  "scheduled_time": "14:00:00",
  "duration_minutes": 15,
  "reason": "Fatiga acumulada"
}
```

**Tipos de descanso:**
- `rest` - Descanso
- `meal` - Comida
- `medical` - Médico
- `bathroom` - Baño
- `other` - Otro

---

#### 7️⃣ Ver Mis Descansos
```http
GET /api/scheduled-breaks/my-breaks/
Authorization: Bearer <token>
```

---

#### 8️⃣ Cancelar Descanso
```http
DELETE /api/scheduled-breaks/{id}/
Authorization: Bearer <token>
```

---

#### 9️⃣ Marcar Descanso como Completado
```http
POST /api/scheduled-breaks/{id}/update-status/
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "completed"
}
```

---

## 🎨 Componentes Frontend Sugeridos

### Para Supervisor - Vista de Descansos

```jsx
// components/ScheduledBreaksManagement.jsx
import React, { useState, useEffect } from 'react';
import { breaksApi } from '../services/breaksApi';

export const ScheduledBreaksManagement = () => {
  const [pendingBreaks, setPendingBreaks] = useState([]);
  const [historyBreaks, setHistoryBreaks] = useState([]);
  const [activeTab, setActiveTab] = useState('pending'); // 'pending' | 'history'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'pending') {
        const data = await breaksApi.getPending();
        setPendingBreaks(data);
      } else {
        // Historial: TODOS los descansos aprobados/rechazados de TODOS los empleados del supervisor
        const [approved, rejected] = await Promise.all([
          breaksApi.getAll({ status: 'approved' }),
          breaksApi.getAll({ status: 'rejected' })
        ]);
        // Combinar y ordenar por fecha de revisión (más recientes primero)
        setHistoryBreaks([...approved, ...rejected].sort((a, b) => 
          new Date(b.review_date) - new Date(a.review_date)
        ));
      }
    } catch (error) {
      console.error('Error loading breaks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (breakId, comment) => {
    try {
      await breaksApi.review(breakId, 'approved', comment);
      alert('✅ Descanso aprobado');
      loadData();
    } catch (error) {
      alert('❌ Error al aprobar');
    }
  };

  const handleReject = async (breakId, comment) => {
    try {
      await breaksApi.review(breakId, 'rejected', comment);
      alert('✅ Descanso rechazado');
      loadData();
    } catch (error) {
      alert('❌ Error al rechazar');
    }
  };

  return (
    <div className="breaks-management">
      <h1>Gestión de Descansos</h1>
      
      {/* Tabs */}
      <div className="tabs">
        <button 
          className={activeTab === 'pending' ? 'active' : ''}
          onClick={() => setActiveTab('pending')}
        >
          Pendientes ({pendingBreaks.length})
        </button>
        <button 
          className={activeTab === 'history' ? 'active' : ''}
          onClick={() => setActiveTab('history')}
        >
          Historial ({historyBreaks.length})
        </button>
      </div>

      {loading ? (
        <div>Cargando...</div>
      ) : activeTab === 'pending' ? (
        <PendingBreaksTable 
          breaks={pendingBreaks}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      ) : (
        <HistoryBreaksTable breaks={historyBreaks} />
      )}
    </div>
  );
};

// Tabla de pendientes
const PendingBreaksTable = ({ breaks, onApprove, onReject }) => (
  <table>
    <thead>
      <tr>
        <th>Empleado</th>
        <th>Tipo</th>
        <th>Fecha</th>
        <th>Hora</th>
        <th>Duración</th>
        <th>Razón</th>
        <th>Acciones</th>
      </tr>
    </thead>
    <tbody>
      {breaks.map(brk => (
        <tr key={brk.id}>
          <td>{brk.employee.full_name}</td>
          <td>{brk.break_type_display}</td>
          <td>{formatDate(brk.scheduled_date)}</td>
          <td>{brk.scheduled_time}</td>
          <td>{brk.duration_minutes} min</td>
          <td>{brk.reason}</td>
          <td>
            <button onClick={() => {
              const comment = prompt('Comentario (opcional):');
              onApprove(brk.id, comment);
            }}>
              ✅ Aprobar
            </button>
            <button onClick={() => {
              const comment = prompt('Razón del rechazo:');
              if (comment) onReject(brk.id, comment);
            }}>
              ❌ Rechazar
            </button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
);

// Tabla de historial
const HistoryBreaksTable = ({ breaks }) => (
  <table>
    <thead>
      <tr>
        <th>Empleado</th>
        <th>Tipo</th>
        <th>Fecha</th>
        <th>Estado</th>
        <th>Revisado por</th>
        <th>Fecha Revisión</th>
        <th>Comentario</th>
      </tr>
    </thead>
    <tbody>
      {breaks.map(brk => (
        <tr key={brk.id}>
          <td>{brk.employee.full_name}</td>
          <td>{brk.break_type_display}</td>
          <td>{formatDate(brk.scheduled_date)}</td>
          <td>
            <span className={`status ${brk.status}`}>
              {brk.status === 'approved' ? '✅ Aprobado' : '❌ Rechazado'}
            </span>
          </td>
          <td>{brk.reviewed_by?.full_name || '-'}</td>
          <td>{formatDateTime(brk.review_date)}</td>
          <td>{brk.review_comment || '-'}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('es-ES');
};

const formatDateTime = (dateStr) => {
  return new Date(dateStr).toLocaleString('es-ES');
};
```

---

## 📦 Servicio API

```javascript
// services/breaksApi.js
import axios from 'axios';

const API_URL = 'http://localhost:8000';
const getToken = () => localStorage.getItem('token');

export const breaksApi = {
  // Supervisor: Ver pendientes
  getPending: async () => {
    const { data } = await axios.get(`${API_URL}/api/scheduled-breaks/pending/`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return data;
  },

  // Supervisor: Ver historial con filtros
  getAll: async (filters = {}) => {
    const params = new URLSearchParams(filters).toString();
    const { data } = await axios.get(
      `${API_URL}/api/scheduled-breaks/?${params}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Supervisor: Aprobar/Rechazar
  review: async (breakId, status, comment = '') => {
    const { data } = await axios.post(
      `${API_URL}/api/scheduled-breaks/${breakId}/review/`,
      { status, review_comment: comment },
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Empleado: Crear descanso
  create: async (breakData) => {
    const { data } = await axios.post(
      `${API_URL}/api/scheduled-breaks/`,
      breakData,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Empleado: Mis descansos
  getMyBreaks: async () => {
    const { data } = await axios.get(
      `${API_URL}/api/scheduled-breaks/my-breaks/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Ver descansos de hoy
  getToday: async () => {
    const { data } = await axios.get(
      `${API_URL}/api/scheduled-breaks/today/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Cancelar descanso
  cancel: async (breakId) => {
    const { data } = await axios.delete(
      `${API_URL}/api/scheduled-breaks/${breakId}/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  }
};
```

---

## 🎨 Estados y Colores

```css
.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.status.pending {
  background: #fef3c7;
  color: #92400e;
}

.status.approved {
  background: #d1fae5;
  color: #065f46;
}

.status.rejected {
  background: #fee2e2;
  color: #991b1b;
}

.status.completed {
  background: #dbeafe;
  color: #1e40af;
}

.status.cancelled {
  background: #f3f4f6;
  color: #6b7280;
}
```

---

## ✅ Checklist Frontend

### Para Supervisor
- [ ] Vista "Pendientes" con tabla de descansos por aprobar
- [ ] Botones "Aprobar" y "Rechazar" con modal de comentario
- [ ] Vista "Historial" con filtros (aprobados/rechazados)
- [ ] Badge de estados con colores
- [ ] Contador de pendientes en tab

### Para Empleado
- [ ] Formulario para solicitar descanso
- [ ] Vista "Mis Descansos" con estados
- [ ] Botón para cancelar descansos pendientes
- [ ] Notificaciones cuando se aprueben/rechacen

---

**Fecha:** 29/11/2025  
**Backend:** ✅ Listo  
**Frontend:** 📋 Usar esta guía
