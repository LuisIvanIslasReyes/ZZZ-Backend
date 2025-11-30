# 🩺 API - Sistema de Síntomas

## � Funcionalidades Automáticas (Backend)

### ✅ Auto-Aprobación de Síntomas Severos
Cuando un empleado reporta un síntoma con severidad `severe`:
- ✅ Se **auto-aprueba automáticamente**
- ✅ Se marca como `is_reviewed=true`
- ✅ Se genera una **alerta crítica** (high priority)
- ✅ Se asigna al supervisor
- ✅ Nota automática: "⚠️ Síntoma severo - Auto-aprobado automáticamente"

**Razón:** Síntomas severos requieren atención inmediata, no pueden esperar aprobación manual.

### 🔔 Notificación al Empleado al Revisar
Cuando un supervisor revisa un síntoma:
- ✅ El empleado es **notificado** que su síntoma fue revisado
- ✅ Backend actualiza `reviewed_at` y `reviewed_by`
- ✅ Frontend puede mostrar badge amarillo con síntomas recientemente revisados
- ✅ Empleado puede ver las notas del supervisor

---

## �📋 Endpoints Disponibles

### Para SUPERVISORES

#### 1️⃣ Contar Síntomas Pendientes (Badge/Notificación)
**⚡ Endpoint optimizado para actualizar badges en tiempo real**

```http
GET /api/symptom-reports/pending-count/
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "count": 5,
  "by_severity": {
    "severe": 2,
    "moderate": 2,
    "mild": 1
  }
}
```

**Uso:** 
- Badge rojo en sidebar "Síntomas del Equipo"
- Polling cada 30 segundos
- Notificaciones push

---

#### 2️⃣ Listar Síntomas Pendientes (Tabla completa)
```http
GET /api/symptom-reports/pending/
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
    "symptom_type": "headache",
    "symptom_type_display": "Dolor de cabeza",
    "severity": "moderate",
    "severity_display": "Moderado",
    "description": "Dolor intenso desde hace 2 horas",
    "is_reviewed": false,
    "reviewed_by": null,
    "review_comment": null,
    "created_at": "2025-11-30T14:30:00Z",
    "reviewed_at": null
  }
]
```

---

#### 3️⃣ Ver Todos los Síntomas del Equipo
```http
GET /api/symptom-reports/
Authorization: Bearer <token>
```

**Filtros disponibles:**
```javascript
// Por estado de revisión
?is_reviewed=false  // Pendientes
?is_reviewed=true   // Revisados

// Por severidad
?severity=severe
?severity=moderate
?severity=mild

// Por tipo de síntoma
?symptom_type=fatigue
?symptom_type=headache
?symptom_type=dizziness

// Ordenar
?ordering=-created_at     // Más recientes primero
?ordering=severity        // Por severidad
```

---

#### 4️⃣ Revisar Síntoma
```http
POST /api/symptom-reports/{id}/review/
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_reviewed": true,
  "review_comment": "Revisado. Se recomienda descanso de 30 min"
}
```

**Respuesta (200):**
```json
{
  "message": "Reporte revisado exitosamente",
  "report": {
    "id": 1,
    "employee": {...},
    "is_reviewed": true,
    "reviewed_by": {
      "id": 2,
      "full_name": "Supervisor López"
    },
    "review_comment": "Revisado. Se recomienda descanso de 30 min",
    "reviewed_at": "2025-11-30T15:00:00Z"
  }
}
```

---

### Para EMPLEADOS

#### 5️⃣ Reportar Síntoma
```http
POST /api/symptom-reports/
Authorization: Bearer <token>
Content-Type: application/json

{
  "symptom_type": "headache",
  "severity": "moderate",
  "description": "Dolor intenso desde hace 2 horas"
}
```

**Tipos de síntoma disponibles:**
- `fatigue` - Fatiga/Cansancio
- `headache` - Dolor de cabeza
- `dizziness` - Mareo
- `nausea` - Náuseas
- `muscle_pain` - Dolor muscular
- `eye_strain` - Fatiga visual
- `stress` - Estrés
- `difficulty_concentrating` - Dificultad para concentrarse
- `shortness_of_breath` - Dificultad para respirar
- `other` - Otro

**Severidades:**
- `mild` - Leve
- `moderate` - Moderado
- `severe` - Severo (⚠️ Auto-genera alerta)

---

#### 6️⃣ Ver Mis Síntomas
```http
GET /api/symptom-reports/my-reports/
Authorization: Bearer <token>
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "symptom_type": "headache",
    "symptom_type_display": "Dolor de cabeza",
    "severity": "moderate",
    "is_reviewed": true,
    "reviewed_by": {
      "id": 2,
      "full_name": "Supervisor López"
    },
    "notes": "Revisado. Toma un descanso",
    "created_at": "2025-11-30T14:30:00Z",
    "reviewed_at": "2025-11-30T15:00:00Z"
  }
]
```

---

#### 7️⃣ Ver Síntomas Recientemente Revisados (Badge Amarillo)
**⚡ Endpoint para badge amarillo de notificaciones del empleado**

```http
GET /api/symptom-reports/recently-reviewed/
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "count": 2,
  "reports": [
    {
      "id": 1,
      "symptom_type": "headache",
      "symptom_type_display": "Dolor de cabeza",
      "severity": "moderate",
      "is_reviewed": true,
      "reviewed_by": {
        "id": 2,
        "full_name": "Supervisor López"
      },
      "notes": "Revisado. Descansa 15 minutos",
      "created_at": "2025-11-30T14:30:00Z",
      "reviewed_at": "2025-11-30T15:00:00Z"
    }
  ]
}
```

**Uso:** Badge amarillo en "Mis Síntomas" para empleados (últimas 24h)

---

## 🎨 Implementación Frontend

### 1️⃣ MainLayout.tsx - Badge Dinámico en Sidebar

```typescript
// MainLayout.tsx
import { useEffect, useState } from 'react';
import { symptomService } from '@/services/symptomService';

export const MainLayout = () => {
  const [pendingSymptomsCount, setPendingSymptomsCount] = useState(0);
  const [severityBreakdown, setSeverityBreakdown] = useState({
    severe: 0,
    moderate: 0,
    mild: 0
  });

  // Cargar conteo inicial
  useEffect(() => {
    loadPendingSymptomsCount();
    
    // Polling cada 30 segundos
    const interval = setInterval(loadPendingSymptomsCount, 30000);
    
    // Escuchar evento cuando se revise un síntoma
    window.addEventListener('symptoms-updated', loadPendingSymptomsCount);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('symptoms-updated', loadPendingSymptomsCount);
    };
  }, []);

  const loadPendingSymptomsCount = async () => {
    try {
      const data = await symptomService.getPendingCount();
      setPendingSymptomsCount(data.count);
      setSeverityBreakdown(data.by_severity);
    } catch (error) {
      console.error('Error loading symptoms count:', error);
    }
  };

  // Configurar items de navegación
  const navigationItems = [
    // ... otros items
    {
      label: 'Síntomas del Equipo',
      icon: <HeartIcon />,
      path: '/supervisor/team-symptoms',
      badge: pendingSymptomsCount > 0 ? {
        color: 'red',
        count: pendingSymptomsCount,
        // Tooltip opcional con breakdown
        tooltip: `${severityBreakdown.severe} severos, ${severityBreakdown.moderate} moderados`
      } : undefined
    }
  ];

  return (
    <div className="layout">
      <Sidebar items={navigationItems} />
      {/* ... resto del layout */}
    </div>
  );
};
```

---

### 2️⃣ TeamSymptomsPage.tsx - Emitir Evento Después de Revisar

```typescript
// TeamSymptomsPage.tsx
const handleReviewSymptom = async (symptomId: number, comment: string) => {
  try {
    await symptomService.reviewSymptom(symptomId, comment);
    
    // ✅ Emitir evento para actualizar badge
    window.dispatchEvent(new CustomEvent('symptoms-updated'));
    
    // Mostrar mensaje de éxito
    toast.success('Síntoma revisado exitosamente');
    
    // Recargar lista
    loadSymptoms();
  } catch (error) {
    toast.error('Error al revisar síntoma');
  }
};
```

---

### 3️⃣ symptomService.ts - Servicio API

```typescript
// services/symptomService.ts
import axios from 'axios';

const API_URL = 'http://localhost:8000';
const getToken = () => localStorage.getItem('token');

export const symptomService = {
  // 📊 Contar síntomas pendientes (para badge)
  getPendingCount: async () => {
    const { data } = await axios.get(
      `${API_URL}/api/symptom-reports/pending-count/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // 📋 Listar síntomas pendientes
  getPendingSymptoms: async () => {
    const { data } = await axios.get(
      `${API_URL}/api/symptom-reports/pending/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // 📋 Listar todos los síntomas del equipo
  getTeamSymptoms: async (filters = {}) => {
    const params = new URLSearchParams(filters).toString();
    const { data } = await axios.get(
      `${API_URL}/api/symptom-reports/?${params}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // ✅ Revisar síntoma
  reviewSymptom: async (symptomId: number, comment: string) => {
    const { data } = await axios.post(
      `${API_URL}/api/symptom-reports/${symptomId}/review/`,
      {
        is_reviewed: true,
        review_comment: comment
      },
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // 📝 Reportar síntoma (empleado)
  createSymptom: async (symptomData: {
    symptom_type: string;
    severity: string;
    description?: string;
  }) => {
    const { data } = await axios.post(
      `${API_URL}/api/symptom-reports/`,
      symptomData,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // 👤 Mis síntomas (empleado)
  getMySymptoms: async () => {
    const { data } = await axios.get(
      `${API_URL}/api/symptom-reports/my-reports/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // 🔔 Síntomas recientemente revisados (empleado - badge amarillo)
  getRecentlyReviewed: async () => {
    const { data } = await axios.get(
      `${API_URL}/api/symptom-reports/recently-reviewed/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  }
};
```

---

### 4️⃣ Sidebar Component - Badge Rojo

```typescript
// components/Sidebar.tsx
interface NavigationItem {
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: {
    color: 'red' | 'yellow' | 'blue';
    count: number;
    tooltip?: string;
  };
}

const Sidebar = ({ items }: { items: NavigationItem[] }) => {
  return (
    <nav>
      {items.map((item) => (
        <Link key={item.path} to={item.path} className="nav-item">
          {item.icon}
          <span>{item.label}</span>
          
          {/* Badge condicional */}
          {item.badge && item.badge.count > 0 && (
            <span
              className={`badge badge-${item.badge.color}`}
              title={item.badge.tooltip}
            >
              {item.badge.count}
            </span>
          )}
        </Link>
      ))}
    </nav>
  );
};
```

---

### 5️⃣ Badge CSS

```css
/* styles/sidebar.css */
.badge {
  position: absolute;
  top: 8px;
  right: 8px;
  min-width: 20px;
  height: 20px;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.badge-red {
  background-color: #ef4444;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
  animation: pulse 2s infinite;
}

.badge-yellow {
  background-color: #f59e0b;
}

.badge-blue {
  background-color: #3b82f6;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
```

---

## 🔔 Opcional: Badge Amarillo para Empleados

```typescript
// MainLayout.tsx (Para empleados)
const [recentlyReviewedCount, setRecentlyReviewedCount] = useState(0);

useEffect(() => {
  if (userRole === 'employee') {
    loadRecentlyReviewedCount();
  }
}, []);

const loadRecentlyReviewedCount = async () => {
  const symptoms = await symptomService.getMySymptoms();
  
  // Contar los revisados en las últimas 24h que no han sido "vistos"
  const lastView = localStorage.getItem('symptoms-last-view');
  const lastViewDate = lastView ? new Date(lastView) : new Date(0);
  
  const recentCount = symptoms.filter(s => 
    s.is_reviewed && 
    new Date(s.reviewed_at) > lastViewDate
  ).length;
  
  setRecentlyReviewedCount(recentCount);
};

// Al entrar a "Mis Síntomas"
const handleViewMySymptoms = () => {
  localStorage.setItem('symptoms-last-view', new Date().toISOString());
  setRecentlyReviewedCount(0);
};

// Item de navegación
{
  label: 'Mis Síntomas',
  icon: <UserIcon />,
  path: '/employee/my-symptoms',
  badge: recentlyReviewedCount > 0 ? {
    color: 'yellow',
    count: recentlyReviewedCount
  } : undefined
}
```

---

## 📊 Tabla de Síntomas del Equipo

```typescript
// TeamSymptomsPage.tsx
import { useState, useEffect } from 'react';
import { symptomService } from '@/services/symptomService';

export const TeamSymptomsPage = () => {
  const [symptoms, setSymptoms] = useState([]);
  const [filter, setFilter] = useState('pending'); // 'all', 'pending', 'reviewed'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSymptoms();
  }, [filter]);

  const loadSymptoms = async () => {
    setLoading(true);
    try {
      const filters = filter === 'pending' 
        ? { is_reviewed: 'false' }
        : filter === 'reviewed'
        ? { is_reviewed: 'true' }
        : {};
      
      const data = await symptomService.getTeamSymptoms(filters);
      setSymptoms(data);
    } catch (error) {
      console.error('Error loading symptoms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (symptomId: number, comment: string) => {
    try {
      await symptomService.reviewSymptom(symptomId, comment);
      
      // Emitir evento global
      window.dispatchEvent(new CustomEvent('symptoms-updated'));
      
      toast.success('Síntoma revisado');
      loadSymptoms();
    } catch (error) {
      toast.error('Error al revisar');
    }
  };

  return (
    <div className="symptoms-page">
      <h1>Síntomas del Equipo</h1>
      
      {/* Filtros */}
      <div className="filters">
        <button onClick={() => setFilter('pending')}>
          Pendientes ({symptoms.filter(s => !s.is_reviewed).length})
        </button>
        <button onClick={() => setFilter('reviewed')}>
          Revisados
        </button>
        <button onClick={() => setFilter('all')}>
          Todos
        </button>
      </div>

      {/* Tabla */}
      <table>
        <thead>
          <tr>
            <th>Empleado</th>
            <th>Síntoma</th>
            <th>Severidad</th>
            <th>Descripción</th>
            <th>Fecha</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {symptoms.map(symptom => (
            <tr key={symptom.id}>
              <td>{symptom.employee.full_name}</td>
              <td>{symptom.symptom_type_display}</td>
              <td>
                <span className={`severity ${symptom.severity}`}>
                  {symptom.severity_display}
                </span>
              </td>
              <td>{symptom.description || '-'}</td>
              <td>{formatDate(symptom.created_at)}</td>
              <td>
                {symptom.is_reviewed ? (
                  <span className="reviewed">✅ Revisado</span>
                ) : (
                  <span className="pending">⏳ Pendiente</span>
                )}
              </td>
              <td>
                {!symptom.is_reviewed && (
                  <button onClick={() => {
                    const comment = prompt('Comentario:');
                    if (comment) handleReview(symptom.id, comment);
                  }}>
                    Revisar
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## ✅ Checklist de Implementación

### Backend (Ya listo ✅)
- ✅ Endpoint `/api/symptom-reports/pending-count/`
- ✅ Endpoint `/api/symptom-reports/pending/`
- ✅ Endpoint `/api/symptom-reports/{id}/review/`
- ✅ Auto-aprobación de síntomas severos
- ✅ Notificaciones automáticas

### Frontend (Pendiente)
- [ ] `MainLayout.tsx` - Estado `pendingSymptomsCount`
- [ ] `MainLayout.tsx` - useEffect con polling (30s)
- [ ] `MainLayout.tsx` - Event listener `symptoms-updated`
- [ ] `MainLayout.tsx` - Badge dinámico en navigationItem
- [ ] `TeamSymptomsPage.tsx` - Emitir evento después de revisar
- [ ] `symptomService.ts` - Implementar servicio completo
- [ ] `Sidebar.tsx` - Componente de badge condicional
- [ ] CSS - Estilos para badges (rojo pulsante)
- [ ] (Opcional) Badge amarillo para empleados

---

## 🎯 Resultado Final

**Antes (Hardcodeado):**
```tsx
<NavigationItem 
  label="Síntomas del Equipo"
  badge="red" // ❌ Siempre rojo
/>
```

**Después (Dinámico):**
```tsx
<NavigationItem 
  label="Síntomas del Equipo"
  badge={pendingSymptomsCount > 0 ? {
    color: 'red',
    count: pendingSymptomsCount // ✅ Número real
  } : undefined}
/>
```

**Comportamiento:**
- ✅ Badge aparece solo si hay síntomas pendientes
- ✅ Muestra el número exacto (ej: "5")
- ✅ Se actualiza automáticamente cada 30s
- ✅ Se actualiza inmediatamente al revisar un síntoma
- ✅ Badge rojo pulsante para llamar la atención
- ✅ Tooltip opcional con breakdown por severidad

---

**Fecha:** 30/11/2025  
**Backend:** ✅ Listo  
**Frontend:** 📋 Implementar según esta guía  
**Endpoint clave:** `/api/symptom-reports/pending-count/`
