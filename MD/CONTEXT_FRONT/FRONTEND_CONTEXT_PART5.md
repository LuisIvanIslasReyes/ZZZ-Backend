# Frontend Context - Parte 5: Páginas, Routing y Layout

## 🚀 SETUP DE ROUTING

### src/router/index.tsx

```typescript
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@hooks/useAuth';
import { MainLayout } from '@layouts/MainLayout';
import { AuthLayout } from '@layouts/AuthLayout';
import { ProtectedRoute } from '@components/auth/ProtectedRoute';

// Pages
import { LoginPage } from '@pages/LoginPage';
import { AdminDashboard } from '@pages/admin/Dashboard';
import { AdminEmployees } from '@pages/admin/Employees';
import { AdminSupervisors } from '@pages/admin/Supervisors';
import { AdminDevices } from '@pages/admin/Devices';
import { SupervisorDashboard } from '@pages/supervisor/Dashboard';
import { SupervisorAlerts } from '@pages/supervisor/Alerts';
import { SupervisorEmployees } from '@pages/supervisor/Employees';
import { EmployeeDashboard } from '@pages/employee/Dashboard';
import { EmployeeRecommendations } from '@pages/employee/Recommendations';
import { NotFound } from '@pages/NotFound';

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
        </Route>

        {/* Protected Routes - Admin */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="employees" element={<AdminEmployees />} />
          <Route path="supervisors" element={<AdminSupervisors />} />
          <Route path="devices" element={<AdminDevices />} />
        </Route>

        {/* Protected Routes - Supervisor */}
        <Route
          path="/supervisor"
          element={
            <ProtectedRoute allowedRoles={['supervisor']}>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/supervisor/dashboard" replace />} />
          <Route path="dashboard" element={<SupervisorDashboard />} />
          <Route path="alerts" element={<SupervisorAlerts />} />
          <Route path="employees" element={<SupervisorEmployees />} />
        </Route>

        {/* Protected Routes - Employee */}
        <Route
          path="/employee"
          element={
            <ProtectedRoute allowedRoles={['employee']}>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/employee/dashboard" replace />} />
          <Route path="dashboard" element={<EmployeeDashboard />} />
          <Route path="recommendations" element={<EmployeeRecommendations />} />
        </Route>

        {/* Redirect root based on role */}
        <Route path="/" element={<RoleBasedRedirect />} />

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
};

// Helper component to redirect based on user role
const RoleBasedRedirect: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.is_admin) {
    return <Navigate to="/admin/dashboard" replace />;
  }

  if (user.is_supervisor) {
    return <Navigate to="/supervisor/dashboard" replace />;
  }

  return <Navigate to="/employee/dashboard" replace />;
};
```

### src/components/auth/ProtectedRoute.tsx

```typescript
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@hooks/useAuth';
import { LoadingSpinner } from '@components/common/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: ('admin' | 'supervisor' | 'employee')[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
}) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles) {
    const hasPermission = allowedRoles.some((role) => {
      if (role === 'admin') return user.is_admin;
      if (role === 'supervisor') return user.is_supervisor;
      if (role === 'employee') return !user.is_admin && !user.is_supervisor;
      return false;
    });

    if (!hasPermission) {
      return <Navigate to="/" replace />;
    }
  }

  return <>{children}</>;
};
```

---

## 🎨 LAYOUTS

### src/layouts/AuthLayout.tsx

```typescript
import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '@hooks/useAuth';

export const AuthLayout: React.FC = () => {
  const { user } = useAuth();

  // Si ya está autenticado, redirigir al dashboard
  if (user) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-base-200 flex items-center justify-center">
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </div>
  );
};
```

### src/layouts/MainLayout.tsx

```typescript
import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@hooks/useAuth';

export const MainLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Navigation items basadas en rol
  const getNavItems = () => {
    if (user?.is_admin) {
      return [
        { path: '/admin/dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/admin/employees', label: 'Empleados', icon: '👥' },
        { path: '/admin/supervisors', label: 'Supervisores', icon: '👔' },
        { path: '/admin/devices', label: 'Dispositivos', icon: '📱' },
      ];
    }

    if (user?.is_supervisor) {
      return [
        { path: '/supervisor/dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/supervisor/alerts', label: 'Alertas', icon: '🚨' },
        { path: '/supervisor/employees', label: 'Mis Empleados', icon: '👥' },
      ];
    }

    return [
      { path: '/employee/dashboard', label: 'Mi Dashboard', icon: '📊' },
      { path: '/employee/recommendations', label: 'Recomendaciones', icon: '💡' },
    ];
  };

  const navItems = getNavItems();

  return (
    <div className="drawer lg:drawer-open">
      <input
        id="sidebar-drawer"
        type="checkbox"
        className="drawer-toggle"
        checked={sidebarOpen}
        onChange={() => setSidebarOpen(!sidebarOpen)}
      />
      
      <div className="drawer-content flex flex-col">
        {/* Navbar */}
        <div className="w-full navbar bg-base-300 shadow-lg">
          <div className="flex-none lg:hidden">
            <label htmlFor="sidebar-drawer" className="btn btn-square btn-ghost">
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </label>
          </div>
          
          <div className="flex-1">
            <h1 className="text-xl font-bold ml-2">Sistema Fatiga Laboral</h1>
          </div>
          
          <div className="flex-none">
            <div className="dropdown dropdown-end">
              <label tabIndex={0} className="btn btn-ghost btn-circle avatar placeholder">
                <div className="bg-neutral-focus text-neutral-content rounded-full w-10">
                  <span className="text-xs">
                    {user?.first_name[0]}
                    {user?.last_name[0]}
                  </span>
                </div>
              </label>
              <ul
                tabIndex={0}
                className="menu menu-compact dropdown-content mt-3 p-2 shadow bg-base-100 rounded-box w-52"
              >
                <li className="menu-title">
                  <span>
                    {user?.first_name} {user?.last_name}
                  </span>
                </li>
                <li>
                  <a>{user?.email}</a>
                </li>
                <li>
                  <a onClick={handleLogout} className="text-error">
                    Cerrar Sesión
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Page Content */}
        <main className="flex-1 p-6 bg-base-200">
          <Outlet />
        </main>
      </div>

      {/* Sidebar */}
      <div className="drawer-side">
        <label htmlFor="sidebar-drawer" className="drawer-overlay"></label>
        <aside className="bg-base-100 w-64 h-full">
          <div className="sticky top-0 flex flex-col h-full">
            {/* Logo */}
            <div className="p-4 border-b border-base-300">
              <h2 className="text-2xl font-bold text-primary">SFL</h2>
              <p className="text-xs text-gray-500">
                {user?.is_admin ? 'Administrador' : user?.is_supervisor ? 'Supervisor' : 'Empleado'}
              </p>
            </div>

            {/* Navigation */}
            <ul className="menu p-4 flex-1">
              {navItems.map((item) => (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      isActive ? 'active' : ''
                    }
                  >
                    <span className="text-xl">{item.icon}</span>
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>

            {/* Footer */}
            <div className="p-4 border-t border-base-300">
              <p className="text-xs text-center text-gray-500">
                v1.0.0 © 2024
              </p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};
```

---

## 📄 PÁGINAS

### src/pages/LoginPage.tsx

```typescript
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@hooks/useAuth';
import { Button } from '@components/common/Button';
import { ErrorMessage } from '@components/common/ErrorMessage';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      // El redirect se maneja en AuthContext después del login
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card bg-base-100 shadow-xl">
      <div className="card-body">
        <h2 className="card-title text-2xl font-bold text-center mb-4">
          Sistema Fatiga Laboral
        </h2>
        <p className="text-center text-gray-500 mb-6">
          Inicia sesión para continuar
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <ErrorMessage message={error} />}

          <div className="form-control">
            <label className="label">
              <span className="label-text">Email</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input input-bordered"
              required
              autoFocus
            />
          </div>

          <div className="form-control">
            <label className="label">
              <span className="label-text">Contraseña</span>
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input input-bordered"
              required
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            fullWidth
            loading={loading}
          >
            Iniciar Sesión
          </Button>
        </form>
      </div>
    </div>
  );
};
```

### src/pages/admin/Dashboard.tsx

```typescript
import React, { useState, useEffect } from 'react';
import { QuickStats } from '@components/dashboard/QuickStats';
import { AlertList } from '@components/alerts/AlertList';
import { Card } from '@components/common/Card';
import { useRealtime } from '@hooks/useRealtime';
import { useFetch } from '@hooks/useFetch';
import { userService } from '@services/userService';
import { alertService } from '@services/alertService';
import { deviceService } from '@services/deviceService';
import { Alert } from '@types/alert.types';

export const AdminDashboard: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  // Fetch initial data
  const { data: employees } = useFetch(() => userService.getEmployees());
  const { data: devices } = useFetch(() => deviceService.getDevices());
  const { data: alertsData } = useFetch(() => alertService.getAlerts({ is_resolved: false }));

  // Realtime polling para alertas
  useRealtime(
    async () => {
      const response = await alertService.getAlerts({ is_resolved: false });
      setAlerts(response.results);
    },
    { interval: 10000 } // 10 segundos
  );

  useEffect(() => {
    if (alertsData) {
      setAlerts(alertsData.results);
    }
  }, [alertsData]);

  const handleResolveAlert = async (id: number) => {
    await alertService.resolveAlert(id);
    setAlerts(alerts.filter((a) => a.id !== id));
  };

  const activeDevices = devices?.results.filter((d) => d.is_active).length || 0;
  const avgFatigue = alerts.length > 0
    ? alerts.reduce((sum, a) => sum + a.fatigue_index, 0) / alerts.length
    : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard de Administrador</h1>

      {/* Stats */}
      <QuickStats
        totalEmployees={employees?.count || 0}
        activeAlerts={alerts.length}
        avgFatigue={avgFatigue}
        devicesActive={activeDevices}
      />

      {/* Alertas Activas */}
      <Card title="Alertas Activas" subtitle={`${alerts.length} sin resolver`}>
        <AlertList
          alerts={alerts}
          onResolve={handleResolveAlert}
          showResolved={false}
        />
      </Card>
    </div>
  );
};
```

### src/pages/admin/Employees.tsx

```typescript
import React, { useState } from 'react';
import { useFetch } from '@hooks/useFetch';
import { userService } from '@services/userService';
import { EmployeeCard } from '@components/employees/EmployeeCard';
import { EmployeeForm } from '@components/employees/EmployeeForm';
import { Modal } from '@components/common/Modal';
import { Button } from '@components/common/Button';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import { Employee } from '@types/user.types';

export const AdminEmployees: React.FC = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);

  const { data, loading, refetch } = useFetch(() => userService.getEmployees());

  const handleCreate = async (formData: any) => {
    await userService.createEmployee(formData);
    setShowCreateModal(false);
    refetch();
  };

  const handleDelete = async (id: number) => {
    if (confirm('¿Estás seguro de eliminar este empleado?')) {
      await userService.deleteEmployee(id);
      refetch();
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" className="py-12" />;
  }

  const employees = data?.results || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Empleados</h1>
        <Button variant="primary" onClick={() => setShowCreateModal(true)}>
          + Nuevo Empleado
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {employees.map((employee) => (
          <EmployeeCard
            key={employee.id}
            employee={employee}
            onClick={() => setSelectedEmployee(employee)}
            showActions
            onDelete={() => handleDelete(employee.id)}
          />
        ))}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Crear Empleado"
      >
        <EmployeeForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
        />
      </Modal>

      {/* Detail Modal */}
      {selectedEmployee && (
        <Modal
          isOpen={!!selectedEmployee}
          onClose={() => setSelectedEmployee(null)}
          title="Detalle de Empleado"
        >
          <div className="space-y-4">
            <p><strong>Nombre:</strong> {selectedEmployee.first_name} {selectedEmployee.last_name}</p>
            <p><strong>Email:</strong> {selectedEmployee.email}</p>
            <p><strong>Estado:</strong> {selectedEmployee.is_active ? 'Activo' : 'Inactivo'}</p>
            {selectedEmployee.device && (
              <p><strong>Dispositivo:</strong> {selectedEmployee.device.device_identifier}</p>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
```

### src/pages/supervisor/Dashboard.tsx

```typescript
import React, { useState, useEffect } from 'react';
import { QuickStats } from '@components/dashboard/QuickStats';
import { AlertList } from '@components/alerts/AlertList';
import { Card } from '@components/common/Card';
import { useRealtime } from '@hooks/useRealtime';
import { useFetch } from '@hooks/useFetch';
import { userService } from '@services/userService';
import { alertService } from '@services/alertService';
import { Alert } from '@types/alert.types';

export const SupervisorDashboard: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  // Fetch mis empleados
  const { data: myEmployees } = useFetch(() => userService.getMyEmployees());

  // Realtime alerts
  useRealtime(
    async () => {
      const response = await alertService.getAlerts({ is_resolved: false });
      setAlerts(response.results);
    },
    { interval: 5000 }
  );

  const handleResolveAlert = async (id: number) => {
    await alertService.resolveAlert(id);
    setAlerts(alerts.filter((a) => a.id !== id));
  };

  const avgFatigue = alerts.length > 0
    ? alerts.reduce((sum, a) => sum + a.fatigue_index, 0) / alerts.length
    : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard de Supervisor</h1>

      {/* Stats */}
      <QuickStats
        totalEmployees={myEmployees?.count || 0}
        activeAlerts={alerts.length}
        avgFatigue={avgFatigue}
      />

      {/* Recent Alerts */}
      <Card title="Alertas Recientes" subtitle="Empleados bajo tu supervisión">
        <AlertList
          alerts={alerts.slice(0, 10)}
          onResolve={handleResolveAlert}
        />
      </Card>
    </div>
  );
};
```

### src/pages/employee/Dashboard.tsx

```typescript
import React from 'react';
import { RealtimeMetrics } from '@components/dashboard/RealtimeMetrics';
import { FatigueLineChart } from '@components/charts/FatigueLineChart';
import { Card } from '@components/common/Card';
import { useRealtime } from '@hooks/useRealtime';
import { useFetch } from '@hooks/useFetch';
import { metricsService } from '@services/metricsService';
import { recommendationService } from '@services/recommendationService';
import { useAuth } from '@hooks/useAuth';
import { Badge } from '@components/common/Badge';

export const EmployeeDashboard: React.FC = () => {
  const { user } = useAuth();

  // Latest metrics con polling
  const { data: latestMetrics } = useRealtime(
    () => metricsService.getMyLatestMetrics(),
    { interval: 5000 }
  );

  // Historical data para gráfico
  const { data: historicalData } = useFetch(() =>
    metricsService.getMyMetrics({
      page_size: 100,
      ordering: '-window_end',
    })
  );

  // Recommendations
  const { data: recommendations } = useFetch(() =>
    recommendationService.getRecommendations({ is_applied: false })
  );

  const pendingRecommendations = recommendations?.results.filter(
    (r) => !r.is_applied
  ) || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Mi Dashboard</h1>
        {latestMetrics && (
          <Badge
            variant={
              latestMetrics.fatigue_index < 40
                ? 'success'
                : latestMetrics.fatigue_index < 70
                ? 'warning'
                : 'error'
            }
            size="lg"
          >
            Fatiga: {latestMetrics.fatigue_index.toFixed(0)}
          </Badge>
        )}
      </div>

      {/* Métricas en tiempo real */}
      <RealtimeMetrics
        metrics={latestMetrics || null}
        employeeName={`${user?.first_name} ${user?.last_name}`}
      />

      {/* Gráfico de tendencia */}
      <Card title="Tendencia de Fatiga" subtitle="Últimas 24 horas">
        {historicalData && <FatigueLineChart data={historicalData.results} />}
      </Card>

      {/* Recommendations */}
      {pendingRecommendations.length > 0 && (
        <Card title="Recomendaciones Pendientes" variant="warning">
          <div className="space-y-2">
            {pendingRecommendations.slice(0, 3).map((rec) => (
              <div key={rec.id} className="alert alert-warning">
                <svg
                  className="w-6 h-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>{rec.message}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
```

### src/pages/NotFound.tsx

```typescript
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@components/common/Button';

export const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-200">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-primary">404</h1>
        <p className="text-2xl font-semibold mt-4">Página no encontrada</p>
        <p className="text-gray-500 mt-2">
          La página que buscas no existe o no tienes permisos para acceder.
        </p>
        <Button
          variant="primary"
          onClick={() => navigate('/')}
          className="mt-6"
        >
          Volver al inicio
        </Button>
      </div>
    </div>
  );
};
```

---

## 🚀 CONFIGURACIÓN PRINCIPAL

### src/App.tsx

```typescript
import React from 'react';
import { AppRouter } from './router';
import { AuthProvider } from './contexts/AuthContext';

function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}

export default App;
```

### src/main.tsx

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  @apply bg-base-200;
}

::-webkit-scrollbar-thumb {
  @apply bg-base-300 rounded-lg;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-base-content/30;
}

/* Transitions suaves */
* {
  @apply transition-colors duration-200;
}

/* Link styles */
a {
  @apply no-underline;
}
```

---

## 📦 SCRIPTS DE PACKAGE.JSON

```json
{
  "name": "fatigue-monitoring-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0",
    "clsx": "^2.0.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "daisyui": "^4.4.19",
    "eslint": "^8.55.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.32",
    "prettier": "^3.1.1",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.2.2",
    "vite": "^5.0.8"
  }
}
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### 1. Setup Inicial
- [ ] Crear proyecto Vite: `npm create vite@latest fatigue-frontend -- --template react-ts`
- [ ] Instalar dependencias: `npm install`
- [ ] Configurar TailwindCSS + DaisyUI (ver FRONTEND_CONTEXT_PART2.md)
- [ ] Configurar variables de entorno `.env`

### 2. Estructura Base
- [ ] Crear carpeta `src/types` con todos los tipos TypeScript
- [ ] Crear carpeta `src/services` con servicios API
- [ ] Crear carpeta `src/hooks` con custom hooks
- [ ] Crear carpeta `src/utils` con utilidades
- [ ] Crear carpeta `src/contexts` con AuthContext

### 3. Componentes
- [ ] Crear todos los componentes comunes (`Card`, `Button`, `Modal`, etc.)
- [ ] Crear componentes de alertas (`AlertCard`, `AlertList`, `AlertModal`)
- [ ] Crear componentes de dashboard (`StatCard`, `QuickStats`, `RealtimeMetrics`)
- [ ] Crear componentes de gráficos (`FatigueLineChart`, `GaugeChart`, etc.)

### 4. Páginas
- [ ] Implementar `LoginPage`
- [ ] Implementar páginas de Admin (Dashboard, Employees, Supervisors, Devices)
- [ ] Implementar páginas de Supervisor (Dashboard, Alerts, Employees)
- [ ] Implementar páginas de Employee (Dashboard, Recommendations)

### 5. Routing y Auth
- [ ] Configurar React Router con rutas protegidas
- [ ] Implementar `ProtectedRoute` component
- [ ] Implementar layouts (`MainLayout`, `AuthLayout`)
- [ ] Configurar redirección basada en roles

### 6. Testing y Deployment
- [ ] Probar autenticación y flujo de login
- [ ] Probar navegación entre páginas
- [ ] Verificar permisos por rol
- [ ] Probar polling en tiempo real
- [ ] Build de producción: `npm run build`

---

## 🎯 PRÓXIMOS PASOS SUGERIDOS

1. **Optimizaciones de Performance**
   - Implementar React.memo en componentes pesados
   - Lazy loading de rutas con React.lazy
   - Virtualización de listas largas (react-window)

2. **Mejoras UX/UI**
   - Agregar toasts para notificaciones (react-hot-toast)
   - Implementar skeleton loaders
   - Añadir animaciones con framer-motion

3. **Features Adicionales**
   - Exportación de reportes a PDF
   - Modo oscuro/claro
   - Notificaciones push (Web Push API)
   - Filtros avanzados en tablas
   - Búsqueda global

4. **Testing**
   - Unit tests con Vitest
   - Integration tests con React Testing Library
   - E2E tests con Playwright

---

**¡Documentación frontend completa!** 🚀

Estos 5 documentos contienen todo lo necesario para que un copilot implemente el frontend completo del Sistema de Fatiga Laboral con React + TypeScript + Vite + DaisyUI.
