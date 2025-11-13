# Frontend Context - Parte 4: Componentes de Alertas y Dashboard

## 🚨 COMPONENTES DE ALERTAS

### src/components/alerts/AlertBadge.tsx

```typescript
import React from 'react';
import { Badge } from '@components/common/Badge';
import { getAlertBadgeClass } from '@utils/colorUtils';

interface AlertBadgeProps {
  severity: 'low' | 'medium' | 'high' | 'critical';
  className?: string;
}

const SEVERITY_LABELS = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
  critical: 'Crítica',
};

export const AlertBadge: React.FC<AlertBadgeProps> = ({ severity, className }) => {
  const variant = {
    low: 'info' as const,
    medium: 'warning' as const,
    high: 'error' as const,
    critical: 'error' as const,
  };

  return (
    <Badge variant={variant[severity]} className={className}>
      {SEVERITY_LABELS[severity]}
    </Badge>
  );
};
```

### src/components/alerts/AlertCard.tsx

```typescript
import React from 'react';
import { Alert } from '@types/alert.types';
import { AlertBadge } from './AlertBadge';
import { formatRelativeTime } from '@utils/formatters';
import clsx from 'clsx';

interface AlertCardProps {
  alert: Alert;
  onClick?: () => void;
  onResolve?: (id: number) => void;
  showActions?: boolean;
}

export const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onClick,
  onResolve,
  showActions = true,
}) => {
  return (
    <div
      className={clsx(
        'card bg-base-100 shadow-md border-l-4',
        alert.severity === 'low' && 'border-info',
        alert.severity === 'medium' && 'border-warning',
        (alert.severity === 'high' || alert.severity === 'critical') && 'border-error',
        alert.is_resolved && 'opacity-60',
        onClick && 'cursor-pointer hover:shadow-lg transition-shadow'
      )}
      onClick={onClick}
    >
      <div className="card-body p-4">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <AlertBadge severity={alert.severity} />
              {alert.is_resolved && (
                <Badge variant="success" size="sm">
                  Resuelta
                </Badge>
              )}
            </div>
            
            <h3 className="font-semibold text-lg mb-1">{alert.employee_name}</h3>
            <p className="text-sm text-gray-600 mb-2">{alert.message}</p>
            
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>Fatiga: {alert.fatigue_index.toFixed(1)}</span>
              <span>{formatRelativeTime(alert.timestamp)}</span>
            </div>
          </div>

          {showActions && !alert.is_resolved && onResolve && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onResolve(alert.id);
              }}
              className="btn btn-success btn-sm"
            >
              Resolver
            </button>
          )}
        </div>

        {alert.is_resolved && alert.resolved_at && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Resuelta {formatRelativeTime(alert.resolved_at)}
              {alert.resolved_by_name && ` por ${alert.resolved_by_name}`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
```

### src/components/alerts/AlertList.tsx

```typescript
import React, { useState } from 'react';
import { Alert } from '@types/alert.types';
import { AlertCard } from './AlertCard';
import { AlertModal } from './AlertModal';
import { EmptyState } from '@components/common/EmptyState';
import { LoadingSpinner } from '@components/common/LoadingSpinner';

interface AlertListProps {
  alerts: Alert[];
  loading?: boolean;
  onResolve?: (id: number) => Promise<void>;
  showResolved?: boolean;
}

export const AlertList: React.FC<AlertListProps> = ({
  alerts,
  loading,
  onResolve,
  showResolved = false,
}) => {
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  const filteredAlerts = showResolved
    ? alerts
    : alerts.filter((a) => !a.is_resolved);

  if (loading) {
    return <LoadingSpinner size="lg" className="py-12" />;
  }

  if (filteredAlerts.length === 0) {
    return (
      <EmptyState
        title="No hay alertas"
        message={showResolved ? "No hay alertas en el sistema" : "No hay alertas activas"}
      />
    );
  }

  return (
    <>
      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onClick={() => setSelectedAlert(alert)}
            onResolve={onResolve}
          />
        ))}
      </div>

      {selectedAlert && (
        <AlertModal
          alert={selectedAlert}
          isOpen={!!selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onResolve={onResolve}
        />
      )}
    </>
  );
};
```

### src/components/alerts/AlertModal.tsx

```typescript
import React from 'react';
import { Alert } from '@types/alert.types';
import { Modal } from '@components/common/Modal';
import { AlertBadge } from './AlertBadge';
import { Button } from '@components/common/Button';
import { formatDate, formatRelativeTime } from '@utils/formatters';

interface AlertModalProps {
  alert: Alert;
  isOpen: boolean;
  onClose: () => void;
  onResolve?: (id: number) => Promise<void>;
}

export const AlertModal: React.FC<AlertModalProps> = ({
  alert,
  isOpen,
  onClose,
  onResolve,
}) => {
  const handleResolve = async () => {
    if (onResolve) {
      await onResolve(alert.id);
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Detalle de Alerta"
      size="lg"
      actions={
        <>
          {!alert.is_resolved && onResolve && (
            <Button variant="success" onClick={handleResolve}>
              Marcar como Resuelta
            </Button>
          )}
          <Button variant="ghost" onClick={onClose}>
            Cerrar
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <AlertBadge severity={alert.severity} size="lg" />
          {alert.is_resolved && (
            <span className="badge badge-success">Resuelta</span>
          )}
        </div>

        {/* Información del empleado */}
        <div>
          <h4 className="font-semibold mb-2">Empleado</h4>
          <p className="text-lg">{alert.employee_name}</p>
          {alert.employee_email && (
            <p className="text-sm text-gray-500">{alert.employee_email}</p>
          )}
        </div>

        {/* Mensaje */}
        <div>
          <h4 className="font-semibold mb-2">Descripción</h4>
          <p className="text-gray-700">{alert.message}</p>
        </div>

        {/* Métricas */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold mb-1">Tipo de Alerta</h4>
            <p className="text-gray-600">{alert.alert_type}</p>
          </div>
          <div>
            <h4 className="font-semibold mb-1">Índice de Fatiga</h4>
            <p className="text-2xl font-bold text-error">
              {alert.fatigue_index.toFixed(1)}
            </p>
          </div>
        </div>

        {/* Fechas */}
        <div className="border-t pt-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Creada:</span>
              <p>{formatDate(alert.timestamp)}</p>
              <p className="text-xs text-gray-400">
                {formatRelativeTime(alert.timestamp)}
              </p>
            </div>
            {alert.is_resolved && alert.resolved_at && (
              <div>
                <span className="text-gray-500">Resuelta:</span>
                <p>{formatDate(alert.resolved_at)}</p>
                <p className="text-xs text-gray-400">
                  {formatRelativeTime(alert.resolved_at)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Supervisor que resolvió */}
        {alert.resolved_by_name && (
          <div className="bg-success bg-opacity-10 p-3 rounded">
            <p className="text-sm">
              Resuelta por: <strong>{alert.resolved_by_name}</strong>
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
};
```

### src/components/alerts/AlertStats.tsx

```typescript
import React from 'react';
import { AlertStats as AlertStatsType } from '@types/alert.types';
import { Card } from '@components/common/Card';

interface AlertStatsProps {
  stats: AlertStatsType;
}

export const AlertStats: React.FC<AlertStatsProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card compact>
        <div className="stat">
          <div className="stat-title">Total</div>
          <div className="stat-value text-primary">{stats.total}</div>
        </div>
      </Card>

      <Card compact>
        <div className="stat">
          <div className="stat-title">Resueltas</div>
          <div className="stat-value text-success">{stats.resolved}</div>
        </div>
      </Card>

      <Card compact>
        <div className="stat">
          <div className="stat-title">Activas</div>
          <div className="stat-value text-error">{stats.unresolved}</div>
        </div>
      </Card>

      <Card compact>
        <div className="stat">
          <div className="stat-title">Tiempo Prom. Resolución</div>
          <div className="stat-value text-sm">
            {stats.avg_resolution_time_minutes
              ? `${stats.avg_resolution_time_minutes.toFixed(0)} min`
              : 'N/A'}
          </div>
        </div>
      </Card>
    </div>
  );
};
```

---

## 📊 COMPONENTES DE DASHBOARD

### src/components/dashboard/StatCard.tsx

```typescript
import React from 'react';
import clsx from 'clsx';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant,
  className,
}) => {
  return (
    <div className={clsx('card bg-base-100 shadow-xl', className)}>
      <div className="card-body">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-gray-500 uppercase">{title}</h3>
            <p
              className={clsx(
                'text-3xl font-bold mt-2',
                variant === 'primary' && 'text-primary',
                variant === 'secondary' && 'text-secondary',
                variant === 'success' && 'text-success',
                variant === 'warning' && 'text-warning',
                variant === 'error' && 'text-error',
                variant === 'info' && 'text-info'
              )}
            >
              {value}
            </p>
            {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
          </div>
          
          {icon && (
            <div
              className={clsx(
                'p-3 rounded-full',
                variant === 'primary' && 'bg-primary bg-opacity-10 text-primary',
                variant === 'success' && 'bg-success bg-opacity-10 text-success',
                variant === 'warning' && 'bg-warning bg-opacity-10 text-warning',
                variant === 'error' && 'bg-error bg-opacity-10 text-error',
                !variant && 'bg-gray-100 text-gray-600'
              )}
            >
              {icon}
            </div>
          )}
        </div>

        {trend && (
          <div className="flex items-center gap-1 mt-2">
            <span
              className={clsx(
                'text-sm font-medium',
                trend.isPositive ? 'text-success' : 'text-error'
              )}
            >
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </span>
            <span className="text-xs text-gray-500">vs. período anterior</span>
          </div>
        )}
      </div>
    </div>
  );
};
```

### src/components/dashboard/QuickStats.tsx

```typescript
import React from 'react';
import { StatCard } from './StatCard';

interface QuickStatsProps {
  totalEmployees?: number;
  activeAlerts?: number;
  avgFatigue?: number;
  devicesActive?: number;
}

export const QuickStats: React.FC<QuickStatsProps> = ({
  totalEmployees = 0,
  activeAlerts = 0,
  avgFatigue = 0,
  devicesActive = 0,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Empleados"
        value={totalEmployees}
        variant="primary"
        icon={
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
        }
      />

      <StatCard
        title="Alertas Activas"
        value={activeAlerts}
        variant={activeAlerts > 5 ? 'error' : activeAlerts > 2 ? 'warning' : 'success'}
        icon={
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
        }
      />

      <StatCard
        title="Fatiga Promedio"
        value={`${avgFatigue.toFixed(1)}`}
        subtitle="/100"
        variant={avgFatigue > 70 ? 'error' : avgFatigue > 40 ? 'warning' : 'success'}
        icon={
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        }
      />

      <StatCard
        title="Dispositivos Activos"
        value={devicesActive}
        subtitle={`de ${totalEmployees}`}
        variant="info"
        icon={
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
            />
          </svg>
        }
      />
    </div>
  );
};
```

### src/components/dashboard/RealtimeMetrics.tsx

```typescript
import React from 'react';
import { ProcessedMetrics } from '@types/metrics.types';
import { GaugeChart } from '@components/charts/GaugeChart';
import { Card } from '@components/common/Card';
import { formatDate } from '@utils/formatters';

interface RealtimeMetricsProps {
  metrics: ProcessedMetrics | null;
  employeeName?: string;
}

export const RealtimeMetrics: React.FC<RealtimeMetricsProps> = ({
  metrics,
  employeeName,
}) => {
  if (!metrics) {
    return (
      <Card title="Métricas en Tiempo Real">
        <p className="text-center text-gray-500 py-12">No hay datos disponibles</p>
      </Card>
    );
  }

  return (
    <Card
      title="Métricas en Tiempo Real"
      subtitle={employeeName}
      actions={
        <span className="text-xs text-gray-500">
          Última actualización: {formatDate(metrics.window_end)}
        </span>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Fatiga */}
        <div className="text-center">
          <GaugeChart value={metrics.fatigue_index} label="Fatiga" />
        </div>

        {/* Heart Rate */}
        <div className="text-center">
          <div className="mb-2">
            <div className="text-3xl font-bold text-error">
              {metrics.hr_avg.toFixed(0)}
            </div>
            <div className="text-xs text-gray-500">BPM Promedio</div>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-500">
              Min: {metrics.hr_min.toFixed(0)}
            </span>
            <span className="text-gray-500">
              Max: {metrics.hr_max.toFixed(0)}
            </span>
          </div>
        </div>

        {/* SpO2 */}
        <div className="text-center">
          <div className="mb-2">
            <div className="text-3xl font-bold text-info">
              {metrics.spo2_avg.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-500">SpO2 Promedio</div>
          </div>
          <div className="text-xs text-gray-500">
            Mínimo: {metrics.spo2_min.toFixed(1)}%
          </div>
        </div>

        {/* Activity */}
        <div className="text-center">
          <div className="mb-2">
            <div className="text-3xl font-bold text-success">
              {metrics.activity_level.toFixed(0)}
            </div>
            <div className="text-xs text-gray-500">Nivel de Actividad</div>
          </div>
          <div className="text-xs text-gray-500">Escala 0-100</div>
        </div>
      </div>
    </Card>
  );
};
```

### src/components/dashboard/TrendIndicator.tsx

```typescript
import React from 'react';
import clsx from 'clsx';

interface TrendIndicatorProps {
  value: number;
  label?: string;
  showPercentage?: boolean;
}

export const TrendIndicator: React.FC<TrendIndicatorProps> = ({
  value,
  label,
  showPercentage = true,
}) => {
  const isPositive = value > 0;
  const isNeutral = value === 0;

  return (
    <div className="flex items-center gap-2">
      {!isNeutral && (
        <span
          className={clsx(
            'text-lg font-bold',
            isPositive ? 'text-success' : 'text-error'
          )}
        >
          {isPositive ? '↑' : '↓'}
        </span>
      )}
      <span
        className={clsx(
          'font-semibold',
          isPositive && 'text-success',
          !isPositive && !isNeutral && 'text-error',
          isNeutral && 'text-gray-500'
        )}
      >
        {Math.abs(value).toFixed(1)}
        {showPercentage && '%'}
      </span>
      {label && <span className="text-sm text-gray-500">{label}</span>}
    </div>
  );
};
```

---

## 👥 COMPONENTES DE EMPLEADOS

### src/components/employees/EmployeeCard.tsx

```typescript
import React from 'react';
import { Employee } from '@types/user.types';
import { Card } from '@components/common/Card';
import { Badge } from '@components/common/Badge';
import { formatFullName } from '@utils/formatters';

interface EmployeeCardProps {
  employee: Employee;
  onClick?: () => void;
  currentFatigue?: number;
  showActions?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
}

export const EmployeeCard: React.FC<EmployeeCardProps> = ({
  employee,
  onClick,
  currentFatigue,
  showActions = false,
  onEdit,
  onDelete,
}) => {
  const fatigueColor =
    currentFatigue === undefined
      ? 'gray'
      : currentFatigue < 40
      ? 'success'
      : currentFatigue < 70
      ? 'warning'
      : 'error';

  return (
    <Card
      className="cursor-pointer hover:shadow-2xl transition-shadow"
      onClick={onClick}
      compact
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Avatar */}
          <div className="avatar placeholder">
            <div className="bg-neutral-focus text-neutral-content rounded-full w-12">
              <span className="text-xl">
                {employee.first_name[0]}
                {employee.last_name[0]}
              </span>
            </div>
          </div>

          {/* Info */}
          <div>
            <h3 className="font-semibold text-lg">
              {formatFullName(employee.first_name, employee.last_name)}
            </h3>
            <p className="text-sm text-gray-500">{employee.email}</p>
            {employee.device && (
              <p className="text-xs text-gray-400 mt-1">
                Dispositivo: {employee.device.device_identifier}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Fatigue indicator */}
          {currentFatigue !== undefined && (
            <div className="text-center">
              <div
                className={`text-2xl font-bold ${
                  fatigueColor === 'success'
                    ? 'text-success'
                    : fatigueColor === 'warning'
                    ? 'text-warning'
                    : 'text-error'
                }`}
              >
                {currentFatigue.toFixed(0)}
              </div>
              <div className="text-xs text-gray-500">Fatiga</div>
            </div>
          )}

          {/* Status badge */}
          <Badge variant={employee.is_active ? 'success' : 'error'} size="sm">
            {employee.is_active ? 'Activo' : 'Inactivo'}
          </Badge>

          {/* Actions */}
          {showActions && (
            <div className="dropdown dropdown-end">
              <label tabIndex={0} className="btn btn-ghost btn-sm btn-circle">
                ⋮
              </label>
              <ul
                tabIndex={0}
                className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52"
              >
                {onEdit && (
                  <li>
                    <a onClick={(e) => {
                      e.stopPropagation();
                      onEdit();
                    }}>
                      Editar
                    </a>
                  </li>
                )}
                {onDelete && (
                  <li>
                    <a
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete();
                      }}
                      className="text-error"
                    >
                      Eliminar
                    </a>
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
```

### src/components/employees/EmployeeForm.tsx

```typescript
import React, { useState } from 'react';
import { Button } from '@components/common/Button';
import { isValidEmail, isValidPassword } from '@utils/validators';

interface EmployeeFormData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

interface EmployeeFormProps {
  onSubmit: (data: EmployeeFormData) => Promise<void>;
  onCancel: () => void;
  initialData?: Partial<EmployeeFormData>;
  isEdit?: boolean;
}

export const EmployeeForm: React.FC<EmployeeFormProps> = ({
  onSubmit,
  onCancel,
  initialData,
  isEdit = false,
}) => {
  const [formData, setFormData] = useState<EmployeeFormData>({
    email: initialData?.email || '',
    password: '',
    first_name: initialData?.first_name || '',
    last_name: initialData?.last_name || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'El email es requerido';
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!isEdit && !formData.password) {
      newErrors.password = 'La contraseña es requerida';
    } else if (!isEdit && !isValidPassword(formData.password)) {
      newErrors.password = 'La contraseña debe tener al menos 8 caracteres';
    }

    if (!formData.first_name) {
      newErrors.first_name = 'El nombre es requerido';
    }

    if (!formData.last_name) {
      newErrors.last_name = 'El apellido es requerido';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setLoading(true);
    try {
      await onSubmit(formData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Email */}
      <div className="form-control">
        <label className="label">
          <span className="label-text">Email</span>
        </label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="input input-bordered"
          disabled={isEdit}
        />
        {errors.email && (
          <label className="label">
            <span className="label-text-alt text-error">{errors.email}</span>
          </label>
        )}
      </div>

      {/* Password (solo en create) */}
      {!isEdit && (
        <div className="form-control">
          <label className="label">
            <span className="label-text">Contraseña</span>
          </label>
          <input
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="input input-bordered"
          />
          {errors.password && (
            <label className="label">
              <span className="label-text-alt text-error">{errors.password}</span>
            </label>
          )}
        </div>
      )}

      {/* First Name */}
      <div className="form-control">
        <label className="label">
          <span className="label-text">Nombre</span>
        </label>
        <input
          type="text"
          value={formData.first_name}
          onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
          className="input input-bordered"
        />
        {errors.first_name && (
          <label className="label">
            <span className="label-text-alt text-error">{errors.first_name}</span>
          </label>
        )}
      </div>

      {/* Last Name */}
      <div className="form-control">
        <label className="label">
          <span className="label-text">Apellido</span>
        </label>
        <input
          type="text"
          value={formData.last_name}
          onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
          className="input input-bordered"
        />
        {errors.last_name && (
          <label className="label">
            <span className="label-text-alt text-error">{errors.last_name}</span>
          </label>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 justify-end">
        <Button variant="ghost" onClick={onCancel} type="button">
          Cancelar
        </Button>
        <Button variant="primary" type="submit" loading={loading}>
          {isEdit ? 'Actualizar' : 'Crear'}
        </Button>
      </div>
    </form>
  );
};
```

---

*Continuará en FRONTEND_CONTEXT_PART5.md con páginas y navegación completa...*
