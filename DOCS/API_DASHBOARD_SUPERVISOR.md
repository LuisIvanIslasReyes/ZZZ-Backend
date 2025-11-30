# 📊 API - Dashboard del Supervisor

## 🚀 Nuevos Endpoints para Gráficas

### 1️⃣ Estadísticas Generales del Equipo
```http
GET /api/supervisor/team-stats/
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "total_employees": 5,
  "employees_with_device": 4,
  "active_alerts": 10,
  "avg_fatigue": 51.42,
  "employees_at_risk": 0,
  "team_status": "stable"
}
```

**Uso:** Cards superiores del dashboard (Empleados, Alertas, Fatiga Promedio, Riesgo)

---

### 2️⃣ Tendencia de Fatiga del Equipo
```http
GET /api/supervisor/fatigue-trends/?days=7
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "period": "7 días",
  "start_date": "2025-11-23",
  "end_date": "2025-11-30",
  "data": [
    {
      "date": "2025-11-23",
      "avg_fatigue": 48.5,
      "max_fatigue": 68.2,
      "min_fatigue": 35.1
    },
    {
      "date": "2025-11-24",
      "avg_fatigue": 50.8,
      "max_fatigue": 72.5,
      "min_fatigue": 38.3
    }
  ]
}
```

**Uso:** Gráfica "Tendencia de Fatiga del Equipo" (línea)

---

### 3️⃣ Distribución de Empleados por Riesgo
```http
GET /api/supervisor/risk-distribution/
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "total_employees": 5,
  "employees_monitored": 4,
  "distribution": {
    "normal": {
      "count": 3,
      "percentage": 60.0,
      "employees": [
        {
          "id": 5,
          "name": "Juan Pérez",
          "email": "juan@example.com",
          "fatigue": 42.5,
          "timestamp": "2025-11-30T14:30:00Z"
        }
      ]
    },
    "attention": {
      "count": 1,
      "percentage": 20.0,
      "employees": [...]
    },
    "high_risk": {
      "count": 0,
      "percentage": 0.0,
      "employees": []
    }
  }
}
```

**Uso:** Gráfica "Estado del Equipo" (pie chart o donut)

---

### 4️⃣ Actividad vs Fatiga
```http
GET /api/supervisor/activity-vs-fatigue/?days=7
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "period": "7 días",
  "data": [
    {
      "date": "2025-11-23",
      "activity_level": 51.2,
      "fatigue_level": 48.5
    },
    {
      "date": "2025-11-24",
      "activity_level": 52.0,
      "fatigue_level": 50.8
    }
  ]
}
```

**Uso:** Gráfica "Actividad vs Fatiga" (líneas dobles)

---

### 5️⃣ Horas de Trabajo del Equipo
```http
GET /api/supervisor/working-hours/?days=7
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "period": "7 días",
  "data": [
    {
      "date": "2025-11-23",
      "active_hours": 7.5,
      "recommended_hours": 8.0,
      "difference": -0.5
    },
    {
      "date": "2025-11-24",
      "active_hours": 8.2,
      "recommended_hours": 8.0,
      "difference": 0.2
    }
  ]
}
```

**Uso:** Gráfica "Horas de Actividad del Equipo" (barras comparativas)

---

### 6️⃣ Resumen de Descansos
```http
GET /api/supervisor/breaks-summary/
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "total": {
    "pending": 5,
    "approved": 12,
    "rejected": 2,
    "completed": 10
  },
  "today": {
    "approved": 3,
    "completed": 1
  },
  "pending_requires_action": true
}
```

**Uso:** Card de descansos + badge de notificación

---

### 7️⃣ Línea de Tiempo de Alertas
```http
GET /api/supervisor/alerts-timeline/?days=7
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "period": "7 días",
  "data": [
    {
      "date": "2025-11-23",
      "total_alerts": 8,
      "high_priority": 2,
      "medium_priority": 4,
      "low_priority": 2
    }
  ]
}
```

**Uso:** Gráfica "Alertas Generadas" (barras apiladas)

---

## 🎨 Nuevas Gráficas Sugeridas

### Gráfica 1: Tendencia de Fatiga (Reemplaza la actual)
```javascript
// Endpoint: /api/supervisor/fatigue-trends/?days=7
{
  type: 'line',
  data: {
    labels: data.map(d => d.date),
    datasets: [
      {
        label: 'Promedio del Equipo',
        data: data.map(d => d.avg_fatigue),
        borderColor: '#3b82f6',
        fill: false
      },
      {
        label: 'Nivel Crítico (80%)',
        data: Array(7).fill(80),
        borderColor: '#ef4444',
        borderDash: [5, 5],
        fill: false
      }
    ]
  }
}
```

---

### Gráfica 2: Estado del Equipo (Nueva - Reemplaza distribución vacía)
```javascript
// Endpoint: /api/supervisor/risk-distribution/
{
  type: 'doughnut',
  data: {
    labels: ['Normal', 'Atención', 'Alto Riesgo'],
    datasets: [{
      data: [
        distribution.normal.count,
        distribution.attention.count,
        distribution.high_risk.count
      ],
      backgroundColor: ['#10b981', '#f59e0b', '#ef4444']
    }]
  }
}
```

---

### Gráfica 3: Actividad vs Fatiga (Nueva)
```javascript
// Endpoint: /api/supervisor/activity-vs-fatigue/?days=7
{
  type: 'line',
  data: {
    labels: data.map(d => d.date),
    datasets: [
      {
        label: 'Nivel de Actividad (%)',
        data: data.map(d => d.activity_level),
        borderColor: '#10b981',
        yAxisID: 'y'
      },
      {
        label: 'Fatiga Promedio (%)',
        data: data.map(d => d.fatigue_level),
        borderColor: '#ef4444',
        yAxisID: 'y'
      }
    ]
  }
}
```

---

### Gráfica 4: Horas de Trabajo (Reemplaza horas vacía)
```javascript
// Endpoint: /api/supervisor/working-hours/?days=7
{
  type: 'bar',
  data: {
    labels: data.map(d => d.date),
    datasets: [
      {
        label: 'Horas Activas',
        data: data.map(d => d.active_hours),
        backgroundColor: '#3b82f6'
      },
      {
        label: 'Horas Recomendadas',
        data: data.map(d => d.recommended_hours),
        backgroundColor: '#a855f7'
      }
    ]
  }
}
```

---

### Gráfica 5: Alertas por Día (Nueva)
```javascript
// Endpoint: /api/supervisor/alerts-timeline/?days=7
{
  type: 'bar',
  data: {
    labels: data.map(d => d.date),
    datasets: [
      {
        label: 'Alta Prioridad',
        data: data.map(d => d.high_priority),
        backgroundColor: '#ef4444'
      },
      {
        label: 'Media Prioridad',
        data: data.map(d => d.medium_priority),
        backgroundColor: '#f59e0b'
      },
      {
        label: 'Baja Prioridad',
        data: data.map(d => d.low_priority),
        backgroundColor: '#3b82f6'
      }
    ]
  },
  options: {
    scales: {
      x: { stacked: true },
      y: { stacked: true }
    }
  }
}
```

---

## 📦 Servicio API para Frontend

```javascript
// services/supervisorDashboardApi.js
import axios from 'axios';

const API_URL = 'http://localhost:8000';
const getToken = () => localStorage.getItem('token');

export const supervisorDashboardApi = {
  // Estadísticas generales
  getTeamStats: async () => {
    const { data } = await axios.get(`${API_URL}/api/supervisor/team-stats/`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return data;
  },

  // Tendencia de fatiga
  getFatigueTrends: async (days = 7) => {
    const { data } = await axios.get(
      `${API_URL}/api/supervisor/fatigue-trends/?days=${days}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Distribución de riesgo
  getRiskDistribution: async () => {
    const { data } = await axios.get(
      `${API_URL}/api/supervisor/risk-distribution/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Actividad vs Fatiga
  getActivityVsFatigue: async (days = 7) => {
    const { data } = await axios.get(
      `${API_URL}/api/supervisor/activity-vs-fatigue/?days=${days}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Horas de trabajo
  getWorkingHours: async (days = 7) => {
    const { data } = await axios.get(
      `${API_URL}/api/supervisor/working-hours/?days=${days}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Resumen de descansos
  getBreaksSummary: async () => {
    const { data } = await axios.get(
      `${API_URL}/api/supervisor/breaks-summary/`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  },

  // Línea de tiempo de alertas
  getAlertsTimeline: async (days = 7) => {
    const { data } = await axios.get(
      `${API_URL}/api/supervisor/alerts-timeline/?days=${days}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    return data;
  }
};
```

---

## 🎯 Layout del Dashboard Actualizado

```
┌─────────────────────────────────────────────────────────────┐
│  CARDS SUPERIORES (4 cards en fila)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Empleados │ │ Alertas  │ │  Fatiga  │ │  Riesgo  │      │
│  │    5     │ │    10    │ │  51.42%  │ │    0     │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────────┐ ┌────────────────────────────┐
│ Tendencia de Fatiga        │ │ Estado del Equipo          │
│ (línea con promedio)       │ │ (donut con distribución)   │
│                            │ │                            │
│ [Gráfica de línea]         │ │ [Gráfica donut]           │
│                            │ │ • Normal: 60%              │
│                            │ │ • Atención: 20%            │
│                            │ │ • Alto Riesgo: 0%          │
└────────────────────────────┘ └────────────────────────────┘

┌────────────────────────────┐ ┌────────────────────────────┐
│ Actividad vs Fatiga        │ │ Horas de Trabajo           │
│ (líneas dobles)            │ │ (barras comparativas)      │
│                            │ │                            │
│ [Gráfica línea dual]       │ │ [Gráfica barras]          │
│                            │ │                            │
└────────────────────────────┘ └────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Alertas Generadas (barras apiladas por prioridad)          │
│                                                              │
│ [Gráfica barras apiladas: Alta/Media/Baja]                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Ventajas de estos Endpoints

1. **Resuelven los errores 404** actuales
2. **Datos reales del equipo del supervisor** (no de un solo empleado)
3. **Filtra automáticamente** por `employee__supervisor=user`
4. **Gráficas útiles** para tomar decisiones
5. **Optimizados** con agregaciones en base de datos
6. **Preparados para auto-refresh** (agregar `setInterval`)

---

## 🔧 Implementación en el Frontend

```javascript
// Dashboard.jsx
useEffect(() => {
  loadDashboardData();
  
  // Auto-refresh cada 2 minutos
  const interval = setInterval(loadDashboardData, 120000);
  return () => clearInterval(interval);
}, []);

const loadDashboardData = async () => {
  try {
    const [stats, trends, risk, activity, hours, breaks, alerts] = await Promise.all([
      supervisorDashboardApi.getTeamStats(),
      supervisorDashboardApi.getFatigueTrends(7),
      supervisorDashboardApi.getRiskDistribution(),
      supervisorDashboardApi.getActivityVsFatigue(7),
      supervisorDashboardApi.getWorkingHours(7),
      supervisorDashboardApi.getBreaksSummary(),
      supervisorDashboardApi.getAlertsTimeline(7)
    ]);
    
    // Actualizar state con los datos
    setTeamStats(stats);
    setFatigueTrends(trends);
    // ... etc
  } catch (error) {
    console.error('Error loading dashboard:', error);
  }
};
```

---

**Fecha:** 30/11/2025  
**Backend:** ✅ Listo y probado  
**Resuelve:** Errores 404 actuales  
**Reemplaza:** Gráficas vacías con datos reales del equipo
