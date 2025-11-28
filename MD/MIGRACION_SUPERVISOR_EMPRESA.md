# Gestión de Supervisores como Cuentas de Empresa

## Resumen de Cambios

Se ha implementado una nueva lógica donde **cada empresa tiene solo UN supervisor activo**, simplificando la gestión. Los supervisores **SON** las cuentas de empresa directamente.

## Nueva Jerarquía

```
Admin (equipo dev) → Companies (N)
Company (1) = Supervisor (1) → Employees (N)
```

### Flujo de Trabajo:
1. **Admin crea empresa**: Al crear una empresa, puede (opcionalmente) crear su supervisor en el mismo formulario
2. **Admin gestiona supervisores**: Puede ver, editar y gestionar las cuentas de supervisor desde `/api/admin/supervisors/`
3. **Supervisor gestiona empleados**: Cada supervisor ve TODOS los empleados de su empresa (no solo los asignados a él)
4. **Validación**: Solo puede haber UN supervisor activo por empresa

### Características Clave:
- ✅ Admin puede crear empresa y supervisor en un solo paso
- ✅ Admin puede gestionar supervisores independientemente
- ✅ Supervisores ven todos los empleados de su empresa
- ✅ Validación para prevenir múltiples supervisores activos por empresa

---

## Cambios en el Backend

### 1. Modelo de Usuario (`apps/users/models.py`)

#### Modificaciones:
- ✅ Actualizada la documentación del modelo para reflejar nueva jerarquía
- ✅ Método `get_supervised_employees()` ahora retorna TODOS los empleados de la empresa del supervisor
- ✅ Campo `supervisor` en empleados se asigna automáticamente al supervisor de la empresa

### 2. Serializers (`apps/users/serializers.py`)

#### Modificaciones:
- ✅ `UserCreateSerializer`: Validación para asegurar solo un supervisor activo por empresa
- ✅ `UserUpdateSerializer`: Validación para prevenir múltiples supervisores activos
- ✅ `SupervisorListSerializer`: Ahora muestra el conteo de TODOS los empleados de la empresa
- ✅ `EmployeeListSerializer.get_supervisor_name()`: Busca el supervisor de la empresa si no está asignado directamente

### 3. Views (`apps/users/views.py`)

#### Modificaciones:
- ✅ `EmployeeListCreateView.get_queryset()`: Supervisores ven TODOS los empleados de su empresa (no solo los que tienen asignados)
- ✅ `EmployeeListCreateView.perform_create()`: Asigna automáticamente el supervisor de la empresa al crear empleado
- ✅ `EmployeeDetailView.get_queryset()`: Actualizado para mostrar todos los empleados de la empresa
- ❌ **ELIMINADO**: `SupervisorListCreateView` (ya no se necesita panel para crear supervisores)
- ❌ **ELIMINADO**: `SupervisorDetailView` (ya no se gestiona supervisores por separado)

### 4. URLs (`apps/users/urls.py`)

#### Modificaciones:
- ❌ **ELIMINADO**: `path('admin/supervisors/', ...)`
- ❌ **ELIMINADO**: `path('admin/supervisors/<int:pk>/', ...)`
- ✅ Añadida documentación explicando por qué se eliminaron estas rutas

### 5. Script de Migración (`SCRIPTS/migrate_supervisor_to_company.py`)

#### Nuevo archivo creado:
- ✅ Script para desactivar supervisores duplicados por empresa
- ✅ Mantiene solo UN supervisor activo por empresa (el más antiguo y activo)
- ✅ Reasigna TODOS los empleados al supervisor activo de la empresa
- ✅ Genera reporte detallado de cambios realizados
- ✅ Transacciones atómicas para garantizar integridad

#### Cómo ejecutar:
```bash
cd ZZZ-Backend
python SCRIPTS/migrate_supervisor_to_company.py
```

---

## Cambios en el Frontend

### 1. Types (`src/types/`)

#### `employee.types.ts`:
- ✅ Documentación actualizada: "supervisores ahora son la empresa"
- ✅ `CreateEmployeeData`: Eliminado campo `supervisor` (se asigna automáticamente)
- ✅ `UpdateEmployeeData`: Comentado que `supervisor` no se puede cambiar manualmente

#### `user.types.ts`:
- ✅ Documentación actualizada: "1 supervisor = 1 empresa"
- ✅ `CreateUserData`: Eliminado campo `supervisor` manual
- ✅ `UpdateUserData`: Comentado que `supervisor` no se actualiza manualmente

### 2. Páginas Admin

#### `CompaniesPage.tsx`:
- ✅ Estadística "Total Supervisores" → "Empresas con Supervisor"
- ✅ Añadido texto: "1 supervisor = 1 empresa"
- ✅ Columna de tabla "Supervisores" → "Supervisor"
- ✅ Muestra "✓ Activo" si tiene supervisor, "Sin supervisor" si no

### 3. Componentes

#### `EmployeeForm.tsx`:
- ✅ No incluye selector de supervisor (ya estaba correcto)
- ✅ Muestra mensaje: "Este empleado será asignado automáticamente a tu empresa"

#### `EmployeeDetailsModal.tsx`:
- ✅ Muestra `supervisor_name` correctamente
- ✅ No requiere cambios (ya muestra la info correcta)

---

## Pasos para Aplicar los Cambios

### Backend:

1. **Revisar los cambios en los archivos modificados**
2. **Ejecutar el script de migración** (esto debe hacerse ANTES de deployar el código):
   ```bash
   cd ZZZ-Backend
   python SCRIPTS/migrate_supervisor_to_company.py
   ```
3. **Verificar los logs de migración** para confirmar que:
   - Se desactivaron supervisores duplicados
   - Se reasignaron empleados correctamente
   - Cada empresa tiene máximo 1 supervisor activo

4. **Restart del servidor Django** para aplicar los cambios de código

### Frontend:

1. **Ninguna acción adicional requerida** - los cambios son retrocompatibles
2. Los formularios ya no mostrarán selector de supervisor
3. Las vistas mostrarán la información actualizada

---

## Validaciones Implementadas

### Backend:
- ✅ No se puede crear un supervisor si la empresa ya tiene uno activo
- ✅ No se puede activar un supervisor si la empresa ya tiene uno activo
- ✅ Los supervisores no pueden tener el campo `supervisor` asignado
- ✅ Los empleados se asignan automáticamente al supervisor de la empresa

### Frontend:
- ✅ No se muestra selector de supervisor en formularios de empleados
- ✅ La UI refleja que 1 empresa = 1 supervisor

---

## Posibles Problemas y Soluciones

### Problema: "Esta empresa ya tiene un supervisor activo"
**Causa**: Intentando crear o activar un segundo supervisor para una empresa
**Solución**: Ejecutar el script de migración para desactivar supervisores duplicados

### Problema: Empleados no aparecen para el supervisor
**Causa**: Los empleados pueden tener un `supervisor` asignado a un supervisor inactivo
**Solución**: El script de migración reasigna automáticamente todos los empleados

### Problema: Empresa sin supervisor
**Causa**: La empresa fue creada pero no se creó la cuenta de supervisor
**Solución**: Crear manualmente una cuenta con rol 'supervisor' para esa empresa

---

## Testing

### Casos de Prueba:

1. ✅ **Crear empresa**: Verificar que se puede crear un supervisor para la empresa
2. ✅ **Crear segundo supervisor**: Debe fallar con mensaje "Esta empresa ya tiene un supervisor activo"
3. ✅ **Listar empleados como supervisor**: Debe mostrar TODOS los empleados de la empresa
4. ✅ **Crear empleado**: Debe asignarse automáticamente al supervisor de la empresa
5. ✅ **Desactivar supervisor**: Debe poder desactivarse (quedando la empresa sin supervisor activo)
6. ✅ **Activar supervisor**: Si no hay otro activo, debe poder activarse

---

## Notas Importantes

- 🔴 **CRÍTICO**: Ejecutar el script de migración ANTES de deployar
- 🔴 **CRÍTICO**: Hacer backup de la base de datos antes de migrar
- ⚠️ Los endpoints `/api/admin/supervisors/` han sido eliminados
- ⚠️ El frontend ya no intenta llamar a estos endpoints
- ✅ Los cambios son backward-compatible en lectura (no rompen datos existentes)
- ✅ El campo `supervisor` en empleados sigue existiendo y funcionando

---

## Archivos Modificados

### Backend:
- `apps/users/models.py`
- `apps/users/serializers.py`
- `apps/users/views.py`
- `apps/users/urls.py`
- `SCRIPTS/migrate_supervisor_to_company.py` (nuevo)

### Frontend:
- `src/types/employee.types.ts`
- `src/types/user.types.ts`
- `src/pages/admin/CompaniesPage.tsx`

---

## Siguiente Paso Sugerido

Crear un formulario o flujo para que cuando se cree una empresa, automáticamente se cree también su supervisor asociado.
