# Frontend Context - Parte 2: Implementación Detallada

## 🔧 CONFIGURACIÓN INICIAL DEL PROYECTO

### 1. Crear proyecto con Vite

```bash
npm create vite@latest fatigue-monitor-frontend -- --template react-ts
cd fatigue-monitor-frontend
npm install
```

### 2. Instalar dependencias

```bash
# Dependencias principales
npm install react-router-dom axios
npm install chart.js react-chartjs-2
npm install date-fns

# DaisyUI y TailwindCSS
npm install -D tailwindcss postcss autoprefixer daisyui
npx tailwindcss init -p

# TypeScript types
npm install -D @types/node

# Utilities
npm install clsx
```

### 3. Configurar TailwindCSS (tailwind.config.js)

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        mytheme: {
          "primary": "#3b82f6",
          "secondary": "#8b5cf6",
          "accent": "#10b981",
          "neutral": "#1f2937",
          "base-100": "#ffffff",
          "base-200": "#f3f4f6",
          "base-300": "#e5e7eb",
          "info": "#3b82f6",
          "success": "#10b981",
          "warning": "#f59e0b",
          "error": "#ef4444",
        },
      },
    ],
  },
}
```

### 4. Variables de entorno (.env)

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_POLLING_INTERVAL=15000
VITE_CHART_REFRESH_INTERVAL=30000
```

### 5. Configurar Vite (vite.config.ts)

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@services': path.resolve(__dirname, './src/services'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
```

---

## 📝 IMPLEMENTACIÓN DE SERVICIOS

### src/services/api.ts (Configuración de Axios)

```typescript
import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

// Crear instancia de Axios
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar refresh token
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Si el error es 401 y no hemos reintentado aún
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        // Intentar refrescar el token
        const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('access_token', access);

        // Reintentar request original
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        // Si falla el refresh, logout
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

### src/services/authService.ts

```typescript
import api from './api';
import { LoginResponse, User } from '@types/user.types';

export const authService = {
  // Login
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login/', {
      email,
      password,
    });
    
    const { access, refresh, user } = response.data;
    
    // Guardar en localStorage
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(user));
    
    return response.data;
  },

  // Logout
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout/');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  // Get current user
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  // Check if authenticated
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },

  // Refresh token
  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('/auth/refresh/', {
      refresh: refreshToken,
    });

    const { access } = response.data;
    localStorage.setItem('access_token', access);
    return access;
  },
};
```

### src/services/userService.ts

```typescript
import api from './api';
import { User, Supervisor, Employee } from '@types/user.types';

export const userService = {
  // Admin endpoints
  async getAllSupervisors() {
    const response = await api.get<{ count: number; results: Supervisor[] }>('/admin/supervisors/');
    return response.data;
  },

  async getSupervisor(id: number) {
    const response = await api.get<Supervisor>(`/admin/supervisors/${id}/`);
    return response.data;
  },

  async createSupervisor(data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) {
    const response = await api.post<Supervisor>('/admin/supervisors/', data);
    return response.data;
  },

  async updateSupervisor(id: number, data: Partial<Supervisor>) {
    const response = await api.patch<Supervisor>(`/admin/supervisors/${id}/`, data);
    return response.data;
  },

  async deleteSupervisor(id: number) {
    await api.delete(`/admin/supervisors/${id}/`);
  },

  // Supervisor endpoints
  async getMyEmployees() {
    const response = await api.get<{ count: number; results: Employee[] }>('/supervisor/employees/');
    return response.data;
  },

  async getEmployee(id: number) {
    const response = await api.get<Employee>(`/supervisor/employees/${id}/`);
    return response.data;
  },

  async createEmployee(data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) {
    const response = await api.post<Employee>('/supervisor/employees/', data);
    return response.data;
  },

  async updateEmployee(id: number, data: Partial<Employee>) {
    const response = await api.patch<Employee>(`/supervisor/employees/${id}/`, data);
    return response.data;
  },

  async deleteEmployee(id: number) {
    await api.delete(`/supervisor/employees/${id}/`);
  },

  // General
  async getMe() {
    const response = await api.get<User>('/users/me/');
    return response.data;
  },

  async updateMe(data: Partial<User>) {
    const response = await api.patch<User>('/users/me/', data);
    return response.data;
  },
};
```

### src/services/metricsService.ts

```typescript
import api from './api';
import { ProcessedMetrics, MetricsHistory } from '@types/metrics.types';

export const metricsService = {
  // Supervisor - métricas de empleado
  async getEmployeeCurrentMetrics(employeeId: number) {
    const response = await api.get<ProcessedMetrics>(`/metrics/employee/${employeeId}/current/`);
    return response.data;
  },

  async getEmployeeMetricsHistory(
    employeeId: number,
    params?: {
      start_date?: string;
      end_date?: string;
      interval?: 'minute' | 'hour' | 'day';
    }
  ) {
    const response = await api.get<MetricsHistory>(`/metrics/employee/${employeeId}/history/`, {
      params,
    });
    return response.data;
  },

  // Employee - mis métricas
  async getMyMetrics() {
    const response = await api.get<ProcessedMetrics>('/employee/me/metrics/');
    return response.data;
  },

  async getMyMetricsHistory(params?: {
    start_date?: string;
    end_date?: string;
  }) {
    const response = await api.get<MetricsHistory>('/employee/me/metrics/history/', {
      params,
    });
    return response.data;
  },

  async getMyFatigue() {
    const response = await api.get<{
      current_fatigue: number;
      timestamp: string;
      severity: string;
      trend: string;
    }>('/employee/me/fatigue/');
    return response.data;
  },

  async getMyStats() {
    const response = await api.get<{
      avg_fatigue_today: number;
      avg_hr_today: number;
      min_spo2_today: number;
      total_alerts_today: number;
      time_in_high_fatigue: number;
    }>('/employee/me/stats/');
    return response.data;
  },

  // Dashboard supervisor
  async getSupervisorDashboard() {
    const response = await api.get('/supervisor/dashboard/');
    return response.data;
  },
};
```

### src/services/alertService.ts

```typescript
import api from './api';
import { Alert, AlertStats } from '@types/alert.types';

export const alertService = {
  // Listar alertas
  async getAlerts(params?: {
    is_resolved?: boolean;
    severity?: string;
    employee?: number;
  }) {
    const response = await api.get<{ count: number; results: Alert[] }>('/alerts/', {
      params,
    });
    return response.data;
  },

  // Detalle
  async getAlert(id: number) {
    const response = await api.get<Alert>(`/alerts/${id}/`);
    return response.data;
  },

  // Resolver
  async resolveAlert(id: number) {
    const response = await api.post<{ message: string; alert: Alert }>(`/alerts/${id}/resolve/`);
    return response.data;
  },

  // Reabrir
  async unresolveAlert(id: number) {
    const response = await api.post<{ message: string; alert: Alert }>(`/alerts/${id}/unresolve/`);
    return response.data;
  },

  // Estadísticas
  async getAlertStats(days: number = 7) {
    const response = await api.get<AlertStats>('/alerts/stats/', {
      params: { days },
    });
    return response.data;
  },

  // Mis alertas (empleado)
  async getMyAlerts() {
    const response = await api.get<{ count: number; results: Alert[] }>('/employee/me/alerts/');
    return response.data;
  },
};
```

### src/services/recommendationService.ts

```typescript
import api from './api';
import { Recommendation, RecommendationStats } from '@types/recommendation.types';

export const recommendationService = {
  // Listar
  async getRecommendations(params?: {
    is_applied?: boolean;
    priority?: number;
  }) {
    const response = await api.get<{ count: number; results: Recommendation[] }>('/recommendations/', {
      params,
    });
    return response.data;
  },

  // Detalle
  async getRecommendation(id: number) {
    const response = await api.get<Recommendation>(`/recommendations/${id}/`);
    return response.data;
  },

  // Aplicar
  async applyRecommendation(id: number) {
    const response = await api.post<{ message: string; recommendation: Recommendation }>(
      `/recommendations/${id}/apply/`
    );
    return response.data;
  },

  // Estadísticas
  async getRecommendationStats(days: number = 30) {
    const response = await api.get<RecommendationStats>('/recommendations/stats/', {
      params: { days },
    });
    return response.data;
  },
};
```

### src/services/deviceService.ts

```typescript
import api from './api';
import { Device } from '@types/device.types';

export const deviceService = {
  // Listar dispositivos
  async getDevices() {
    const response = await api.get<{ count: number; results: Device[] }>('/devices/');
    return response.data;
  },

  // Detalle
  async getDevice(id: number) {
    const response = await api.get<Device>(`/devices/${id}/`);
    return response.data;
  },

  // Crear/asignar
  async createDevice(data: {
    device_identifier: string;
    employee: number;
    supervisor: number;
    is_active?: boolean;
  }) {
    const response = await api.post<Device>('/devices/', data);
    return response.data;
  },

  // Actualizar
  async updateDevice(id: number, data: Partial<Device>) {
    const response = await api.patch<Device>(`/devices/${id}/`, data);
    return response.data;
  },

  // Eliminar
  async deleteDevice(id: number) {
    await api.delete(`/devices/${id}/`);
  },
};
```

---

## 🎣 HOOKS PERSONALIZADOS

### src/hooks/useAuth.ts

```typescript
import { useContext } from 'react';
import { AuthContext } from '@/context/AuthContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  
  return context;
};
```

### src/hooks/useRealtime.ts

```typescript
import { useState, useEffect, useCallback } from 'react';

interface UseRealtimeOptions {
  interval?: number;
  enabled?: boolean;
}

export function useRealtime<T>(
  fetchFunction: () => Promise<T>,
  options: UseRealtimeOptions = {}
) {
  const { interval = 15000, enabled = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const result = await fetchFunction();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [fetchFunction]);

  useEffect(() => {
    if (!enabled) return;

    // Fetch inicial
    fetchData();

    // Polling
    const intervalId = setInterval(fetchData, interval);

    return () => clearInterval(intervalId);
  }, [fetchData, interval, enabled]);

  return { data, loading, error, refetch: fetchData };
}
```

### src/hooks/useFetch.ts

```typescript
import { useState, useEffect } from 'react';

interface UseFetchOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useFetch<T>(
  fetchFunction: () => Promise<T>,
  deps: any[] = [],
  options: UseFetchOptions<T> = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchFunction();
        
        if (isMounted) {
          setData(result);
          options.onSuccess?.(result);
        }
      } catch (err) {
        if (isMounted) {
          const error = err as Error;
          setError(error);
          options.onError?.(error);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, deps);

  return { data, loading, error };
}
```

### src/hooks/useDebounce.ts

```typescript
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

### src/hooks/usePagination.ts

```typescript
import { useState } from 'react';

interface UsePaginationReturn {
  currentPage: number;
  pageSize: number;
  setCurrentPage: (page: number) => void;
  setPageSize: (size: number) => void;
  resetPagination: () => void;
}

export function usePagination(
  initialPage: number = 1,
  initialPageSize: number = 10
): UsePaginationReturn {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const resetPagination = () => {
    setCurrentPage(initialPage);
  };

  return {
    currentPage,
    pageSize,
    setCurrentPage,
    setPageSize,
    resetPagination,
  };
}
```

---

## 🎨 UTILIDADES

### src/utils/formatters.ts

```typescript
import { format, formatDistanceToNow, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

// Formatear fecha
export const formatDate = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'dd/MM/yyyy HH:mm', { locale: es });
};

// Formatear fecha corta
export const formatDateShort = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'dd/MM/yyyy', { locale: es });
};

// Tiempo relativo
export const formatRelativeTime = (date: string | Date): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true, locale: es });
};

// Formatear número con decimales
export const formatNumber = (num: number, decimals: number = 2): string => {
  return num.toFixed(decimals);
};

// Formatear porcentaje
export const formatPercent = (num: number): string => {
  return `${num.toFixed(1)}%`;
};

// Formatear nombre completo
export const formatFullName = (firstName: string, lastName: string): string => {
  return `${firstName} ${lastName}`;
};

// Capitalizar primera letra
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};
```

### src/utils/colorUtils.ts

```typescript
// Colores de fatiga
export const FATIGUE_COLORS = {
  low: '#10b981',      // Verde
  medium: '#f59e0b',   // Amarillo
  high: '#f97316',     // Naranja
  critical: '#ef4444', // Rojo
};

// Obtener color según índice de fatiga
export const getFatigueColor = (index: number): string => {
  if (index < 40) return FATIGUE_COLORS.low;
  if (index < 70) return FATIGUE_COLORS.medium;
  if (index < 90) return FATIGUE_COLORS.high;
  return FATIGUE_COLORS.critical;
};

// Obtener severidad como texto
export const getFatigueSeverity = (index: number): string => {
  if (index < 40) return 'Bajo';
  if (index < 70) return 'Moderado';
  if (index < 90) return 'Alto';
  return 'Crítico';
};

// Colores de alertas según severidad
export const ALERT_COLORS = {
  low: 'badge-info',
  medium: 'badge-warning',
  high: 'badge-error',
  critical: 'badge-error',
};

export const getAlertBadgeClass = (severity: string): string => {
  return ALERT_COLORS[severity as keyof typeof ALERT_COLORS] || 'badge-neutral';
};

// Color según estado del dispositivo
export const getDeviceStatusColor = (isActive: boolean): string => {
  return isActive ? '#10b981' : '#6b7280';
};
```

### src/utils/validators.ts

```typescript
// Validar email
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Validar contraseña (mínimo 8 caracteres)
export const isValidPassword = (password: string): boolean => {
  return password.length >= 8;
};

// Validar rango de fatiga
export const isValidFatigueIndex = (index: number): boolean => {
  return index >= 0 && index <= 100;
};

// Validar HR
export const isValidHeartRate = (hr: number): boolean => {
  return hr >= 40 && hr <= 220;
};

// Validar SpO2
export const isValidSpO2 = (spo2: number): boolean => {
  return spo2 >= 0 && spo2 <= 100;
};
```

### src/utils/constants.ts

```typescript
// Rutas
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  
  // Admin
  ADMIN_DASHBOARD: '/admin/dashboard',
  ADMIN_SUPERVISORS: '/admin/supervisors',
  ADMIN_STATS: '/admin/stats',
  
  // Supervisor
  SUPERVISOR_DASHBOARD: '/supervisor/dashboard',
  SUPERVISOR_EMPLOYEES: '/supervisor/employees',
  SUPERVISOR_DEVICES: '/supervisor/devices',
  SUPERVISOR_ALERTS: '/supervisor/alerts',
  SUPERVISOR_RECOMMENDATIONS: '/supervisor/recommendations',
  
  // Employee
  EMPLOYEE_DASHBOARD: '/employee/dashboard',
  EMPLOYEE_HISTORY: '/employee/history',
  EMPLOYEE_ALERTS: '/employee/alerts',
  EMPLOYEE_STATS: '/employee/stats',
};

// Roles
export const ROLES = {
  ADMIN: 'admin',
  SUPERVISOR: 'supervisor',
  EMPLOYEE: 'employee',
};

// Intervalos de polling
export const POLLING_INTERVALS = {
  REALTIME_METRICS: 15000,  // 15 segundos
  ALERTS: 30000,            // 30 segundos
  DASHBOARD: 20000,         // 20 segundos
};

// Severidades
export const SEVERITIES = ['low', 'medium', 'high', 'critical'] as const;

// Tipos de recomendaciones
export const RECOMMENDATION_TYPES = {
  break: 'Descanso',
  task_redistribution: 'Redistribución de Tareas',
  shift_rotation: 'Rotación de Turnos',
};

// Rangos de fatiga
export const FATIGUE_RANGES = {
  LOW: { min: 0, max: 39, label: 'Bajo' },
  MEDIUM: { min: 40, max: 69, label: 'Moderado' },
  HIGH: { min: 70, max: 89, label: 'Alto' },
  CRITICAL: { min: 90, max: 100, label: 'Crítico' },
};
```

---

*Continuará en FRONTEND_CONTEXT_PART3.md...*
