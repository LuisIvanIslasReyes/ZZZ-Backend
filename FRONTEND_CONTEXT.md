# Contexto Completo para Frontend - Sistema de Detección de Fatiga Laboral

## 📋 INFORMACIÓN GENERAL DEL PROYECTO

**Nombre:** Sistema de Detección de Fatiga en Empleados  
**Stack Frontend:** React + TypeScript + Vite + DaisyUI (TailwindCSS)  
**Backend:** Django REST Framework (ya implementado)  
**API Base URL:** `http://127.0.0.1:8000/api/`  
**Autenticación:** JWT (JSON Web Tokens)

---

## 🎯 OBJETIVOS DEL FRONTEND

1. **Dashboard Interactivo** para visualizar métricas de fatiga en tiempo real
2. **Gestión de Usuarios** (Admin → Supervisores, Supervisor → Empleados)
3. **Sistema de Alertas** visual y funcional
4. **Gráficas en Tiempo Real** para monitoreo de sensores
5. **Panel de Recomendaciones** para optimización de rutinas
6. **Diseño Responsivo** y accesible
7. **Arquitectura Modular** y escalable

---

## 👥 ROLES Y PERMISOS DEL SISTEMA

### 1. Administrador (Admin)
**Acceso:**
- Panel de gestión de supervisores (CRUD completo)
- Estadísticas globales del sistema
- Vista general de todos los empleados
- Logs de actividad del sistema

**Navegación:**
```
/admin/dashboard
/admin/supervisors (lista, crear, editar, eliminar)
/admin/supervisors/:id (detalle)
/admin/stats (estadísticas generales)
/admin/logs (actividad del sistema)
```

### 2. Supervisor
**Acceso:**
- Gestión de sus empleados (CRUD)
- Gestión de dispositivos de sus empleados
- Dashboard con métricas agregadas de su equipo
- Panel de alertas de sus empleados
- Sistema de recomendaciones
- Vista detallada de cada empleado

**Navegación:**
```
/supervisor/dashboard (vista general del equipo)
/supervisor/employees (lista de empleados)
/supervisor/employees/:id (detalle de empleado con métricas)
/supervisor/devices (gestión de dispositivos)
/supervisor/alerts (alertas activas y resueltas)
/supervisor/recommendations (sugerencias de optimización)
```

### 3. Empleado (Employee)
**Acceso:**
- Dashboard personal con sus métricas
- Historial de fatiga
- Alertas personales
- Estadísticas individuales

**Navegación:**
```
/employee/dashboard (métricas en tiempo real)
/employee/history (histórico de métricas)
/employee/alerts (mis alertas)
/employee/stats (mis estadísticas)
```

---

## 🔐 SISTEMA DE AUTENTICACIÓN

### Flujo de Autenticación

1. **Login:**
   - Endpoint: `POST /api/auth/login/`
   - Body: `{ "email": "user@example.com", "password": "password123" }`
   - Respuesta exitosa:
   ```json
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "user": {
       "id": 1,
       "email": "user@example.com",
       "first_name": "Juan",
       "last_name": "Pérez",
       "role": "supervisor"
     }
   }
   ```

2. **Tokens:**
   - **Access Token:** Válido por 1 hora (usar en header Authorization)
   - **Refresh Token:** Válido por 24 horas (para renovar access)

3. **Refresh:**
   - Endpoint: `POST /api/auth/refresh/`
   - Body: `{ "refresh": "token_aqui" }`
   - Respuesta: `{ "access": "nuevo_token" }`

4. **Logout:**
   - Endpoint: `POST /api/auth/logout/`
   - Limpiar tokens del localStorage
   - Redirigir a /login

### Almacenamiento de Tokens

```typescript
// LocalStorage
localStorage.setItem('access_token', accessToken);
localStorage.setItem('refresh_token', refreshToken);
localStorage.setItem('user', JSON.stringify(userData));

// Headers para requests
headers: {
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json'
}
```

### Protección de Rutas

```typescript
// Middleware para rutas protegidas
- Verificar existencia de token
- Verificar rol del usuario
- Redirigir según permisos:
  * Sin token → /login
  * Admin intentando acceder a /supervisor → /admin/dashboard
  * Employee intentando acceder a /admin → /employee/dashboard
```

---

## 📡 ENDPOINTS DE LA API (Backend Completo)

### 🔑 Autenticación

```typescript
// Login
POST /api/auth/login/
Body: { email: string, password: string }
Response: { access: string, refresh: string, user: User }

// Refresh Token
POST /api/auth/refresh/
Body: { refresh: string }
Response: { access: string }

// Logout
POST /api/auth/logout/
Headers: { Authorization: Bearer <token> }
Response: 200 OK
```

### 👤 Usuarios (General)

```typescript
// Obtener perfil actual
GET /api/users/me/
Response: User

// Actualizar perfil
PATCH /api/users/me/
Body: { first_name?: string, last_name?: string }
Response: User
```

### 👔 Admin Endpoints

```typescript
// Listar supervisores
GET /api/admin/supervisors/
Response: { count: number, results: Supervisor[] }

// Crear supervisor
POST /api/admin/supervisors/
Body: {
  email: string,
  password: string,
  first_name: string,
  last_name: string
}
Response: Supervisor

// Obtener supervisor por ID
GET /api/admin/supervisors/:id/
Response: Supervisor

// Actualizar supervisor
PUT /api/admin/supervisors/:id/
PATCH /api/admin/supervisors/:id/
Body: { first_name?: string, last_name?: string, is_active?: boolean }
Response: Supervisor

// Eliminar supervisor
DELETE /api/admin/supervisors/:id/
Response: 204 No Content

// Estadísticas generales
GET /api/admin/stats/
Response: {
  total_supervisors: number,
  total_employees: number,
  total_devices: number,
  active_alerts: number,
  avg_fatigue_index: number,
  system_health: string
}
```

### 👨‍💼 Supervisor Endpoints

```typescript
// === EMPLEADOS ===

// Listar empleados del supervisor
GET /api/supervisor/employees/
Response: { count: number, results: Employee[] }

// Crear empleado
POST /api/supervisor/employees/
Body: {
  email: string,
  password: string,
  first_name: string,
  last_name: string
}
Response: Employee

// Obtener empleado por ID
GET /api/supervisor/employees/:id/
Response: Employee

// Actualizar empleado
PUT /api/supervisor/employees/:id/
PATCH /api/supervisor/employees/:id/
Body: { first_name?: string, last_name?: string, is_active?: boolean }
Response: Employee

// Eliminar empleado
DELETE /api/supervisor/employees/:id/
Response: 204 No Content

// === DISPOSITIVOS ===

// Listar dispositivos
GET /api/devices/
Response: { count: number, results: Device[] }

// Crear/asignar dispositivo
POST /api/devices/
Body: {
  device_identifier: string,
  employee: number,
  supervisor: number,
  is_active: boolean
}
Response: Device

// Actualizar dispositivo
PATCH /api/devices/:id/
Body: { is_active?: boolean, employee?: number }
Response: Device

// === MÉTRICAS DE EMPLEADOS ===

// Dashboard general del supervisor
GET /api/supervisor/dashboard/
Response: {
  employees_summary: {
    total: number,
    active: number,
    in_alert: number
  },
  current_metrics: EmployeeMetric[],
  team_avg_fatigue: number,
  alerts_summary: {
    total: number,
    by_severity: { low: number, medium: number, high: number, critical: number }
  }
}

// Métricas actuales de un empleado
GET /api/metrics/employee/:id/current/
Response: ProcessedMetrics

// Histórico de métricas
GET /api/metrics/employee/:id/history/
Query params: ?start_date=2025-11-10&end_date=2025-11-11&interval=hour
Response: { results: ProcessedMetrics[] }

// === ALERTAS ===

// Listar alertas del supervisor
GET /api/alerts/
Query params: ?is_resolved=false&severity=high&employee=1
Response: { count: number, results: Alert[] }

// Detalle de alerta
GET /api/alerts/:id/
Response: Alert

// Resolver alerta
POST /api/alerts/:id/resolve/
Response: { message: string, alert: Alert }

// Reabrir alerta
POST /api/alerts/:id/unresolve/
Response: { message: string, alert: Alert }

// Estadísticas de alertas
GET /api/alerts/stats/
Query params: ?days=7
Response: {
  total: number,
  resolved: number,
  unresolved: number,
  by_severity: { low: number, medium: number, high: number, critical: number },
  avg_resolution_time_minutes: number
}

// === RECOMENDACIONES ===

// Listar recomendaciones
GET /api/recommendations/
Query params: ?is_applied=false&priority=1
Response: { count: number, results: Recommendation[] }

// Detalle de recomendación
GET /api/recommendations/:id/
Response: Recommendation

// Aplicar recomendación
POST /api/recommendations/:id/apply/
Response: { message: string, recommendation: Recommendation }

// Estadísticas de recomendaciones
GET /api/recommendations/stats/
Query params: ?days=30
Response: {
  total: number,
  applied: number,
  pending: number,
  by_type: { break: number, task_redistribution: number, shift_rotation: number },
  avg_application_time_hours: number
}
```

### 👷 Employee Endpoints

```typescript
// Dashboard personal
GET /api/employee/me/
Response: Employee

// Métricas actuales
GET /api/employee/me/metrics/
Response: ProcessedMetrics

// Histórico personal
GET /api/employee/me/metrics/history/
Query params: ?start_date=2025-11-10&end_date=2025-11-11
Response: { results: ProcessedMetrics[] }

// Índice de fatiga actual
GET /api/employee/me/fatigue/
Response: {
  current_fatigue: number,
  timestamp: string,
  severity: string,
  trend: string
}

// Mis alertas
GET /api/employee/me/alerts/
Response: { count: number, results: Alert[] }

// Mis estadísticas
GET /api/employee/me/stats/
Response: {
  avg_fatigue_today: number,
  avg_hr_today: number,
  min_spo2_today: number,
  total_alerts_today: number,
  time_in_high_fatigue: number
}
```

---

## 📊 MODELOS DE DATOS (TypeScript Types)

### User Types

```typescript
// Usuario base
interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'supervisor' | 'employee';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Administrador
interface Admin extends User {
  role: 'admin';
}

// Supervisor
interface Supervisor extends User {
  role: 'supervisor';
  employee_count?: number; // Calculado
}

// Empleado
interface Employee extends User {
  role: 'employee';
  supervisor: number; // ID del supervisor
  supervisor_name?: string; // Poblado en responses
  supervisor_email?: string;
  device?: Device; // Si tiene dispositivo asignado
}

// Login Response
interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

// Auth Context
interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isSupervisor: boolean;
  isEmployee: boolean;
}
```

### Device Types

```typescript
interface Device {
  id: number;
  device_identifier: string; // "ESP32-001"
  employee: number; // ID del empleado
  employee_name?: string;
  employee_email?: string;
  supervisor: number; // ID del supervisor
  supervisor_name?: string;
  is_active: boolean;
  last_connection: string | null;
  created_at: string;
  updated_at?: string;
  // Stats (en detalle)
  total_sensor_data?: number;
  total_processed_metrics?: number;
  latest_fatigue_index?: {
    value: number;
    timestamp: string;
    severity: 'low' | 'medium' | 'high';
  };
}
```

### Metrics Types

```typescript
// Datos crudos de sensores (raramente usado en frontend)
interface SensorData {
  id: number;
  device: number;
  timestamp: string;
  heart_rate: number; // BPM
  spo2: number; // %
  accel_x: number; // g
  accel_y: number;
  accel_z: number;
  created_at: string;
}

// Métricas procesadas (PRINCIPAL para gráficas)
interface ProcessedMetrics {
  id: number;
  device: number;
  employee: number;
  employee_name?: string;
  window_start: string;
  window_end: string;
  
  // Heart Rate
  hr_avg: number;
  hr_max: number;
  hr_min: number;
  hrv_rmssd: number | null;
  hrv_sdnn: number | null;
  hr_trend: 'stable' | 'increasing' | 'decreasing' | null;
  
  // SpO2
  spo2_avg: number;
  spo2_min: number;
  spo2_variance: number | null;
  desaturation_count: number;
  
  // Movement
  activity_level: number; // 0-100
  movement_variance: number | null;
  movement_entropy: number | null;
  posture_angle: number | null;
  
  // ML & Combined
  fatigue_index: number; // 0-100 (PRINCIPAL)
  hr_activity_ratio: number | null;
  recovery_time: number | null;
  
  created_at: string;
}

// Respuesta de endpoints de histórico
interface MetricsHistory {
  count: number;
  next: string | null;
  previous: string | null;
  results: ProcessedMetrics[];
}

// Para tiempo real (polling cada 10-30s)
interface RealtimeMetrics {
  employee_id: number;
  employee_name: string;
  current_fatigue: number;
  current_hr: number;
  current_spo2: number;
  current_activity: number;
  timestamp: string;
  status: 'normal' | 'warning' | 'danger';
}
```

### Alert Types

```typescript
interface Alert {
  id: number;
  employee: number;
  employee_name?: string;
  employee_email?: string;
  supervisor: number;
  supervisor_name?: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  severity_display?: string; // "Baja", "Media", etc.
  alert_type: string; // "high_fatigue", "low_spo2", "high_hr"
  message: string;
  fatigue_index: number;
  is_resolved: boolean;
  resolved_at: string | null;
  resolved_by: number | null;
  resolved_by_name?: string;
  created_at: string;
  // Calculados
  time_since_created?: string; // "2 horas", "30 minutos"
  time_to_resolve?: string | null;
}

interface AlertStats {
  total: number;
  resolved: number;
  unresolved: number;
  by_severity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  avg_resolution_time_minutes: number | null;
}
```

### Recommendation Types

```typescript
interface Recommendation {
  id: number;
  employee: number;
  employee_name?: string;
  employee_email?: string;
  supervisor: number;
  supervisor_name?: string;
  recommendation_type: 'break' | 'task_redistribution' | 'shift_rotation';
  recommendation_type_display?: string;
  description: string;
  priority: number; // 1-5 (1 más urgente)
  based_on_data: Record<string, any>; // JSON con métricas
  is_applied: boolean;
  applied_at: string | null;
  created_at: string;
  updated_at?: string;
  // Calculados
  time_since_created?: string;
  time_to_apply?: string | null;
}

interface RecommendationStats {
  total: number;
  applied: number;
  pending: number;
  by_type: {
    break: number;
    task_redistribution: number;
    shift_rotation: number;
  };
  avg_application_time_hours: number | null;
}
```

---

## 🎨 DISEÑO Y COMPONENTES CON DAISYUI

### Paleta de Colores (DaisyUI Theme)

```typescript
// Usar tema por defecto de DaisyUI o personalizar
// En tailwind.config.js:
module.exports = {
  daisyui: {
    themes: [
      {
        mytheme: {
          "primary": "#3b82f6",      // Azul para acciones principales
          "secondary": "#8b5cf6",    // Púrpura para elementos secundarios
          "accent": "#10b981",       // Verde para éxito
          "neutral": "#1f2937",      // Gris oscuro
          "base-100": "#ffffff",     // Fondo blanco
          "info": "#3b82f6",         // Info (azul)
          "success": "#10b981",      // Éxito (verde)
          "warning": "#f59e0b",      // Advertencia (amarillo)
          "error": "#ef4444",        // Error (rojo)
        },
      },
    ],
  },
}

// Colores de fatiga (personalizado)
const fatigueColors = {
  low: '#10b981',      // Verde (0-39)
  medium: '#f59e0b',   // Amarillo (40-69)
  high: '#f97316',     // Naranja (70-89)
  critical: '#ef4444'  // Rojo (90-100)
};

// Función helper
function getFatigueColor(index: number): string {
  if (index < 40) return fatigueColors.low;
  if (index < 70) return fatigueColors.medium;
  if (index < 90) return fatigueColors.high;
  return fatigueColors.critical;
}

function getFatigueSeverity(index: number): string {
  if (index < 40) return 'Bajo';
  if (index < 70) return 'Moderado';
  if (index < 90) return 'Alto';
  return 'Crítico';
}
```

---

## 📁 ESTRUCTURA DE ARCHIVOS DETALLADA

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/
│   │   ├── icons/
│   │   └── images/
│   │
│   ├── components/
│   │   ├── common/              # Componentes reutilizables
│   │   │   ├── Navbar.tsx       # Barra de navegación superior
│   │   │   ├── Sidebar.tsx      # Menú lateral
│   │   │   ├── Card.tsx         # Card genérica
│   │   │   ├── Badge.tsx        # Badges para estados
│   │   │   ├── Button.tsx       # Botón personalizado
│   │   │   ├── Modal.tsx        # Modal genérico
│   │   │   ├── Table.tsx        # Tabla reutilizable
│   │   │   ├── Pagination.tsx   # Paginación
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorMessage.tsx
│   │   │   └── EmptyState.tsx
│   │   │
│   │   ├── charts/              # Componentes de gráficas
│   │   │   ├── FatigueLineChart.tsx      # Línea de fatiga
│   │   │   ├── HeartRateChart.tsx        # Línea de HR
│   │   │   ├── SpO2Chart.tsx             # Línea de SpO2
│   │   │   ├── ActivityChart.tsx         # Área de actividad
│   │   │   ├── HRVChart.tsx              # HRV (área)
│   │   │   ├── MultiEmployeeChart.tsx    # Múltiples empleados
│   │   │   ├── FatigueHeatmap.tsx        # Heatmap empleados x horas
│   │   │   ├── GaugeChart.tsx            # Medidor circular
│   │   │   └── ChartWrapper.tsx          # Wrapper genérico
│   │   │
│   │   ├── alerts/              # Sistema de alertas
│   │   │   ├── AlertList.tsx    # Lista de alertas
│   │   │   ├── AlertCard.tsx    # Card individual
│   │   │   ├── AlertBadge.tsx   # Badge de severidad
│   │   │   ├── AlertModal.tsx   # Modal de detalle
│   │   │   └── AlertStats.tsx   # Estadísticas
│   │   │
│   │   ├── employees/           # Gestión de empleados
│   │   │   ├── EmployeeList.tsx
│   │   │   ├── EmployeeCard.tsx
│   │   │   ├── EmployeeForm.tsx
│   │   │   ├── EmployeeModal.tsx
│   │   │   └── EmployeeMetricsCard.tsx
│   │   │
│   │   ├── devices/             # Gestión de dispositivos
│   │   │   ├── DeviceList.tsx
│   │   │   ├── DeviceCard.tsx
│   │   │   ├── DeviceForm.tsx
│   │   │   └── DeviceStatusBadge.tsx
│   │   │
│   │   ├── recommendations/     # Recomendaciones
│   │   │   ├── RecommendationList.tsx
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── RecommendationModal.tsx
│   │   │   └── RecommendationBadge.tsx
│   │   │
│   │   ├── dashboard/           # Widgets de dashboard
│   │   │   ├── StatCard.tsx     # Card de estadística
│   │   │   ├── QuickStats.tsx   # Stats rápidas
│   │   │   ├── RealtimeMetrics.tsx
│   │   │   └── TrendIndicator.tsx
│   │   │
│   │   └── layout/              # Layout components
│   │       ├── MainLayout.tsx   # Layout principal
│   │       ├── AuthLayout.tsx   # Layout para login
│   │       └── ProtectedRoute.tsx
│   │
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── ForgotPasswordPage.tsx (opcional)
│   │   │
│   │   ├── admin/
│   │   │   ├── AdminDashboard.tsx
│   │   │   ├── SupervisorManagement.tsx
│   │   │   ├── SystemStats.tsx
│   │   │   └── SystemLogs.tsx
│   │   │
│   │   ├── supervisor/
│   │   │   ├── SupervisorDashboard.tsx
│   │   │   ├── EmployeeManagement.tsx
│   │   │   ├── EmployeeDetail.tsx
│   │   │   ├── DeviceManagement.tsx
│   │   │   ├── AlertsPage.tsx
│   │   │   └── RecommendationsPage.tsx
│   │   │
│   │   └── employee/
│   │       ├── EmployeeDashboard.tsx
│   │       ├── HistoryPage.tsx
│   │       ├── AlertsPage.tsx
│   │       └── StatsPage.tsx
│   │
│   ├── services/
│   │   ├── api.ts               # Configuración de Axios
│   │   ├── authService.ts       # Login, logout, refresh
│   │   ├── userService.ts       # CRUD usuarios
│   │   ├── deviceService.ts     # CRUD dispositivos
│   │   ├── metricsService.ts    # Obtener métricas
│   │   ├── alertService.ts      # Gestión de alertas
│   │   └── recommendationService.ts
│   │
│   ├── hooks/
│   │   ├── useAuth.ts           # Hook de autenticación
│   │   ├── useRealtime.ts       # Polling para tiempo real
│   │   ├── useFetch.ts          # Hook genérico para fetch
│   │   ├── useDebounce.ts       # Debounce para búsquedas
│   │   ├── usePagination.ts     # Manejo de paginación
│   │   └── useLocalStorage.ts   # Persistencia local
│   │
│   ├── context/
│   │   ├── AuthContext.tsx      # Contexto de autenticación
│   │   └── ThemeContext.tsx     # Tema (opcional)
│   │
│   ├── types/
│   │   ├── user.types.ts
│   │   ├── device.types.ts
│   │   ├── metrics.types.ts
│   │   ├── alert.types.ts
│   │   ├── recommendation.types.ts
│   │   └── api.types.ts
│   │
│   ├── utils/
│   │   ├── formatters.ts        # Formateo de datos
│   │   ├── validators.ts        # Validaciones
│   │   ├── constants.ts         # Constantes globales
│   │   ├── chartHelpers.ts      # Helpers para gráficas
│   │   ├── dateUtils.ts         # Manejo de fechas
│   │   └── colorUtils.ts        # Colores de fatiga, etc.
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
│
├── .env                         # Variables de entorno
├── .env.example
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── README.md
```

---

*Continuará en FRONTEND_CONTEXT_PART2.md...*
