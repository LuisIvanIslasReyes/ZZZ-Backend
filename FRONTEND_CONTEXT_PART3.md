# Frontend Context - Parte 3: Componentes y Contexto

## 🔐 CONTEXTO DE AUTENTICACIÓN

### src/context/AuthContext.tsx

```typescript
import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { authService } from '@services/authService';
import { User } from '@types/user.types';
import { useNavigate } from 'react-router-dom';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isSupervisor: boolean;
  isEmployee: boolean;
  loading: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Verificar si hay usuario en localStorage al montar
    const savedUser = authService.getCurrentUser();
    if (savedUser) {
      setUser(savedUser);
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authService.login(email, password);
    setUser(response.user);
    
    // Redirigir según rol
    switch (response.user.role) {
      case 'admin':
        navigate('/admin/dashboard');
        break;
      case 'supervisor':
        navigate('/supervisor/dashboard');
        break;
      case 'employee':
        navigate('/employee/dashboard');
        break;
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    navigate('/login');
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isSupervisor: user?.role === 'supervisor',
    isEmployee: user?.role === 'employee',
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
```

---

## 🧩 COMPONENTES COMUNES

### src/components/common/Card.tsx

```typescript
import React, { ReactNode } from 'react';
import clsx from 'clsx';

interface CardProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
  compact?: boolean;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  children,
  className,
  actions,
  compact = false,
}) => {
  return (
    <div className={clsx('card bg-base-100 shadow-xl', className)}>
      <div className={clsx('card-body', compact && 'p-4')}>
        {(title || subtitle || actions) && (
          <div className="flex justify-between items-start mb-4">
            <div>
              {title && <h2 className="card-title">{title}</h2>}
              {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
            </div>
            {actions && <div className="card-actions">{actions}</div>}
          </div>
        )}
        {children}
      </div>
    </div>
  );
};
```

### src/components/common/Badge.tsx

```typescript
import React from 'react';
import clsx from 'clsx';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  outline?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  outline = false,
  className,
}) => {
  return (
    <span
      className={clsx(
        'badge',
        `badge-${variant}`,
        `badge-${size}`,
        outline && 'badge-outline',
        className
      )}
    >
      {children}
    </span>
  );
};
```

### src/components/common/Button.tsx

```typescript
import React from 'react';
import clsx from 'clsx';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  outline?: boolean;
  wide?: boolean;
  block?: boolean;
  loading?: boolean;
  disabled?: boolean;
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  size = 'md',
  outline = false,
  wide = false,
  block = false,
  loading = false,
  disabled = false,
  className,
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={clsx(
        'btn',
        `btn-${variant}`,
        `btn-${size}`,
        outline && 'btn-outline',
        wide && 'btn-wide',
        block && 'btn-block',
        loading && 'loading',
        className
      )}
    >
      {children}
    </button>
  );
};
```

### src/components/common/Modal.tsx

```typescript
import React, { ReactNode } from 'react';
import clsx from 'clsx';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  actions?: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  actions,
  size = 'md',
}) => {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="modal modal-open">
        <div
          className={clsx(
            'modal-box',
            size === 'sm' && 'max-w-sm',
            size === 'md' && 'max-w-2xl',
            size === 'lg' && 'max-w-4xl',
            size === 'xl' && 'max-w-6xl'
          )}
        >
          {title && (
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-lg">{title}</h3>
              <button onClick={onClose} className="btn btn-sm btn-circle btn-ghost">
                ✕
              </button>
            </div>
          )}
          
          <div className="py-4">{children}</div>
          
          {actions && <div className="modal-action">{actions}</div>}
        </div>
      </div>
    </>
  );
};
```

### src/components/common/LoadingSpinner.tsx

```typescript
import React from 'react';
import clsx from 'clsx';

interface LoadingSpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
}) => {
  return (
    <div className={clsx('flex justify-center items-center', className)}>
      <span
        className={clsx(
          'loading loading-spinner',
          size === 'xs' && 'loading-xs',
          size === 'sm' && 'loading-sm',
          size === 'md' && 'loading-md',
          size === 'lg' && 'loading-lg'
        )}
      ></span>
    </div>
  );
};
```

### src/components/common/ErrorMessage.tsx

```typescript
import React from 'react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div className="alert alert-error shadow-lg">
      <div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="stroke-current flex-shrink-0 h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span>{message}</span>
      </div>
      {onRetry && (
        <div className="flex-none">
          <button onClick={onRetry} className="btn btn-sm btn-ghost">
            Reintentar
          </button>
        </div>
      )}
    </div>
  );
};
```

### src/components/common/EmptyState.tsx

```typescript
import React from 'react';

interface EmptyStateProps {
  title?: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, message, action }) => {
  return (
    <div className="text-center py-12">
      <svg
        className="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          vectorEffect="non-scaling-stroke"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
        />
      </svg>
      {title && <h3 className="mt-2 text-sm font-medium text-gray-900">{title}</h3>}
      <p className="mt-1 text-sm text-gray-500">{message}</p>
      {action && (
        <div className="mt-6">
          <button onClick={action.onClick} className="btn btn-primary">
            {action.label}
          </button>
        </div>
      )}
    </div>
  );
};
```

### src/components/common/Table.tsx

```typescript
import React, { ReactNode } from 'react';
import clsx from 'clsx';

interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => ReactNode;
  width?: string;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (item: T) => void;
  className?: string;
  compact?: boolean;
  zebra?: boolean;
}

export function Table<T extends Record<string, any>>({
  data,
  columns,
  onRowClick,
  className,
  compact = false,
  zebra = true,
}: TableProps<T>) {
  return (
    <div className={clsx('overflow-x-auto', className)}>
      <table className={clsx('table w-full', compact && 'table-compact', zebra && 'table-zebra')}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} style={{ width: column.width }}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => (
            <tr
              key={index}
              onClick={() => onRowClick?.(item)}
              className={clsx(onRowClick && 'hover:bg-base-200 cursor-pointer')}
            >
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render ? column.render(item) : item[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### src/components/common/Pagination.tsx

```typescript
import React from 'react';
import clsx from 'clsx';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  className,
}) => {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className={clsx('btn-group', className)}>
      <button
        className="btn btn-sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        «
      </button>
      
      {pages.map((page) => (
        <button
          key={page}
          className={clsx('btn btn-sm', page === currentPage && 'btn-active')}
          onClick={() => onPageChange(page)}
        >
          {page}
        </button>
      ))}
      
      <button
        className="btn btn-sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        »
      </button>
    </div>
  );
};
```

---

## 📊 COMPONENTES DE GRÁFICAS

### src/components/charts/ChartWrapper.tsx

```typescript
import React, { ReactNode } from 'react';
import { Card } from '@components/common/Card';
import { LoadingSpinner } from '@components/common/LoadingSpinner';
import { ErrorMessage } from '@components/common/ErrorMessage';

interface ChartWrapperProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  loading?: boolean;
  error?: string;
  actions?: ReactNode;
  className?: string;
}

export const ChartWrapper: React.FC<ChartWrapperProps> = ({
  title,
  subtitle,
  children,
  loading,
  error,
  actions,
  className,
}) => {
  return (
    <Card title={title} subtitle={subtitle} actions={actions} className={className}>
      {loading ? (
        <LoadingSpinner size="lg" className="py-12" />
      ) : error ? (
        <ErrorMessage message={error} />
      ) : (
        <div className="h-64">{children}</div>
      )}
    </Card>
  );
};
```

### src/components/charts/FatigueLineChart.tsx

```typescript
import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { ProcessedMetrics } from '@types/metrics.types';
import { getFatigueColor } from '@utils/colorUtils';
import { formatDate } from '@utils/formatters';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface FatigueLineChartProps {
  data: ProcessedMetrics[];
}

export const FatigueLineChart: React.FC<FatigueLineChartProps> = ({ data }) => {
  const chartData = {
    labels: data.map((m) => formatDate(m.window_end)),
    datasets: [
      {
        label: 'Índice de Fatiga',
        data: data.map((m) => m.fatigue_index),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: data.map((m) => getFatigueColor(m.fatigue_index)),
        pointBorderColor: data.map((m) => getFatigueColor(m.fatigue_index)),
        pointRadius: 5,
        pointHoverRadius: 7,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const value = context.parsed.y;
            const severity = value < 40 ? 'Bajo' : value < 70 ? 'Moderado' : value < 90 ? 'Alto' : 'Crítico';
            return `Fatiga: ${value.toFixed(1)} (${severity})`;
          },
        },
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 20,
        },
        grid: {
          color: (context: any) => {
            if (context.tick.value === 40) return 'rgba(245, 158, 11, 0.3)';
            if (context.tick.value === 70) return 'rgba(249, 115, 22, 0.3)';
            if (context.tick.value === 90) return 'rgba(239, 68, 68, 0.3)';
            return 'rgba(0, 0, 0, 0.1)';
          },
        },
      },
    },
  };

  return <Line data={chartData} options={options} />;
};
```

### src/components/charts/HeartRateChart.tsx

```typescript
import React from 'react';
import { Line } from 'react-chartjs-2';
import { ProcessedMetrics } from '@types/metrics.types';
import { formatDate } from '@utils/formatters';

interface HeartRateChartProps {
  data: ProcessedMetrics[];
}

export const HeartRateChart: React.FC<HeartRateChartProps> = ({ data }) => {
  const chartData = {
    labels: data.map((m) => formatDate(m.window_end)),
    datasets: [
      {
        label: 'HR Promedio',
        data: data.map((m) => m.hr_avg),
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
      },
      {
        label: 'HR Máximo',
        data: data.map((m) => m.hr_max),
        borderColor: '#f97316',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.4,
      },
      {
        label: 'HR Mínimo',
        data: data.map((m) => m.hr_min),
        borderColor: '#10b981',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)} BPM`;
          },
        },
      },
    },
    scales: {
      y: {
        min: 40,
        max: 180,
        title: {
          display: true,
          text: 'BPM',
        },
      },
    },
  };

  return <Line data={chartData} options={options} />;
};
```

### src/components/charts/SpO2Chart.tsx

```typescript
import React from 'react';
import { Line } from 'react-chartjs-2';
import { ProcessedMetrics } from '@types/metrics.types';
import { formatDate } from '@utils/formatters';

interface SpO2ChartProps {
  data: ProcessedMetrics[];
}

export const SpO2Chart: React.FC<SpO2ChartProps> = ({ data }) => {
  const chartData = {
    labels: data.map((m) => formatDate(m.window_end)),
    datasets: [
      {
        label: 'SpO2 Promedio',
        data: data.map((m) => m.spo2_avg),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `SpO2: ${context.parsed.y.toFixed(1)}%`;
          },
        },
      },
    },
    scales: {
      y: {
        min: 85,
        max: 100,
        ticks: {
          stepSize: 5,
        },
        title: {
          display: true,
          text: '%',
        },
        grid: {
          color: (context: any) => {
            // Línea roja en 90% (umbral crítico)
            if (context.tick.value === 90) return 'rgba(239, 68, 68, 0.5)';
            return 'rgba(0, 0, 0, 0.1)';
          },
        },
      },
    },
  };

  return <Line data={chartData} options={options} />;
};
```

### src/components/charts/ActivityChart.tsx

```typescript
import React from 'react';
import { Line } from 'react-chartjs-2';
import { ProcessedMetrics } from '@types/metrics.types';
import { formatDate } from '@utils/formatters';

interface ActivityChartProps {
  data: ProcessedMetrics[];
}

export const ActivityChart: React.FC<ActivityChartProps> = ({ data }) => {
  const chartData = {
    labels: data.map((m) => formatDate(m.window_end)),
    datasets: [
      {
        label: 'Nivel de Actividad',
        data: data.map((m) => m.activity_level),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.2)',
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        title: {
          display: true,
          text: 'Nivel (0-100)',
        },
      },
    },
  };

  return <Line data={chartData} options={options} />;
};
```

### src/components/charts/GaugeChart.tsx

```typescript
import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement } from 'chart.js';
import { getFatigueColor, getFatigueSeverity } from '@utils/colorUtils';

ChartJS.register(ArcElement);

interface GaugeChartProps {
  value: number;
  max?: number;
  label?: string;
}

export const GaugeChart: React.FC<GaugeChartProps> = ({
  value,
  max = 100,
  label = 'Fatiga',
}) => {
  const data = {
    datasets: [
      {
        data: [value, max - value],
        backgroundColor: [getFatigueColor(value), '#e5e7eb'],
        borderWidth: 0,
        circumference: 180,
        rotation: 270,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      tooltip: { enabled: false },
      legend: { display: false },
    },
  };

  return (
    <div className="relative">
      <Doughnut data={data} options={options} />
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-4xl font-bold" style={{ color: getFatigueColor(value) }}>
          {value.toFixed(0)}
        </div>
        <div className="text-sm text-gray-500">{getFatigueSeverity(value)}</div>
        <div className="text-xs text-gray-400">{label}</div>
      </div>
    </div>
  );
};
```

---

*Continuará en FRONTEND_CONTEXT_PART4.md con componentes de alertas, dashboard widgets y páginas...*
