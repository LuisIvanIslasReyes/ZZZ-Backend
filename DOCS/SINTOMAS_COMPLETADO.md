# ✅ SISTEMA DE SÍNTOMAS - TODO IMPLEMENTADO

## 🎯 Lo que pediste:

1. ✅ **Notificar al empleado cuando se revisa su síntoma**
2. ✅ **Auto-aprobar síntomas severos directamente**

---

## ✅ BACKEND COMPLETADO

### 1️⃣ Auto-Aprobación de Síntomas Severos

**Archivo:** `apps/analytics/serializers.py` (SymptomReportCreateSerializer)

**Comportamiento:**
```python
if severity == 'severe':
    ✅ is_reviewed = True  (auto-aprobado)
    ✅ reviewed_at = now()
    ✅ reviewed_by = supervisor
    ✅ notes = "⚠️ Síntoma severo - Auto-aprobado automáticamente"
    ✅ Crea FatigueAlert con severity='high'
```

**Resultado:**
- Empleado reporta síntoma severo
- Backend lo aprueba INMEDIATAMENTE
- No aparece en "pendientes"
- Genera alerta crítica para supervisor
- Empleado puede ver que ya está revisado

---

### 2️⃣ Notificación Automática al Empleado al Revisar

**Archivo:** `apps/analytics/views.py` (SymptomReportViewSet.review)

**Comportamiento:**
```python
cuando supervisor revisa:
    ✅ is_reviewed = True
    ✅ reviewed_at = now()
    ✅ reviewed_by = supervisor
    ✅ notes = comentario del supervisor
    ✅ Crea FatigueAlert notificando al empleado
    ✅ Empleado recibe alerta en su dashboard
    ✅ Badge amarillo en "Mis Síntomas" (últimas 24h)
```

**Notificación que recibe el empleado:**
```
🔔 Nueva Alerta
✅ Tu síntoma 'Dolor de cabeza' ha sido revisado

📝 Comentarios del supervisor:
Toma un descanso de 15 minutos y bebe agua.
```

**Mensaje al supervisor:**
```json
{
  "message": "Reporte revisado exitosamente. El empleado ha sido notificado."
}
```

---

### 3️⃣ Nuevo Endpoint: Síntomas Recientemente Revisados

**Para badge amarillo del empleado:**

```http
GET /api/symptom-reports/recently-reviewed/
```

**Respuesta:**
```json
{
  "count": 2,
  "reports": [
    {
      "id": 1,
      "symptom_type": "headache",
      "is_reviewed": true,
      "reviewed_by": { "full_name": "Supervisor López" },
      "notes": "Revisado. Descansa 15 minutos",
      "reviewed_at": "2025-11-30T15:00:00Z"
    }
  ]
}
```

**Uso:**
- Empleado ve badge amarillo en "Mis Síntomas"
- Badge muestra número de revisiones en últimas 24h
- Al abrir la página, marca como "visto"

---

## 📝 PARA EL FRONTEND

### ✅ Ya Implementado en Backend:

1. ✅ Auto-aprobación de severos
2. ✅ **Notificación automática al empleado** (crea FatigueAlert)
3. ✅ Endpoint para badge amarillo
4. ✅ Endpoint para contar pendientes (badge rojo)
5. ✅ Alertas críticas automáticas
6. ✅ **Alerta en dashboard del empleado cuando síntoma es revisado**

---

### 📋 Tareas Frontend:

#### Para Supervisor:

**A. Badge Rojo Dinámico (Ya documentado)**
- Usar `/api/symptom-reports/pending-count/`
- Polling cada 30s
- Ver: `DOCS/RESUMEN_BADGE_SINTOMAS.md`

**B. Al Revisar Síntoma:**
```typescript
const handleReview = async (id, notes) => {
  await symptomService.reviewSymptom(id, notes);
  
  // Emitir evento
  window.dispatchEvent(new CustomEvent('symptoms-updated'));
  
  // Mensaje
  toast.success('✅ Revisado. El empleado será notificado.');
};
```

---

#### Para Empleado:

**C. Badge Amarillo en "Mis Síntomas":**

```typescript
// MainLayout.tsx (para empleados)
const [recentlyReviewedCount, setRecentlyReviewedCount] = useState(0);

useEffect(() => {
  if (userRole === 'employee') {
    loadRecentlyReviewed();
    
    // Polling cada 60s
    const interval = setInterval(loadRecentlyReviewed, 60000);
    return () => clearInterval(interval);
  }
}, []);

const loadRecentlyReviewed = async () => {
  const data = await symptomService.getRecentlyReviewed();
  setRecentlyReviewedCount(data.count);
};

// Navigation item
{
  label: 'Mis Síntomas',
  badge: recentlyReviewedCount > 0 ? {
    color: 'yellow',
    count: recentlyReviewedCount,
    tooltip: 'Síntomas revisados por tu supervisor'
  } : undefined
}
```

**D. Página "Mis Síntomas":**
```typescript
// MySymptomsPage.tsx
useEffect(() => {
  loadSymptoms();
  
  // Marcar como vistos
  return () => {
    // Badge desaparece al cerrar la página
    // (el endpoint ya solo cuenta últimas 24h)
  };
}, []);

const loadSymptoms = async () => {
  const symptoms = await symptomService.getMySymptoms();
  
  // Mostrar los revisados destacados
  const reviewed = symptoms.filter(s => s.is_reviewed);
  const pending = symptoms.filter(s => !s.is_reviewed);
  
  setReviewedSymptoms(reviewed);
  setPendingSymptoms(pending);
};
```

**E. Mostrar Notas del Supervisor:**
```tsx
{symptom.is_reviewed && (
  <div className="review-info">
    <div className="reviewer">
      ✅ Revisado por: {symptom.reviewed_by.full_name}
    </div>
    <div className="review-date">
      📅 {formatDate(symptom.reviewed_at)}
    </div>
    {symptom.notes && (
      <div className="supervisor-notes">
        💬 Notas: {symptom.notes}
      </div>
    )}
  </div>
)}
```

---

## 🎨 Flujo Completo

### Caso 1: Síntoma Severo

1. **Empleado reporta síntoma severo** 👤
   ```
   POST /api/symptom-reports/
   { "symptom_type": "shortness_of_breath", "severity": "severe" }
   ```

2. **Backend auto-aprueba** ⚡
   ```
   ✅ is_reviewed = true
   ✅ Genera alerta crítica
   ✅ Asigna a supervisor
   ```

3. **Frontend muestra** 📱
   ```
   ✅ Ya no aparece en "pendientes" del supervisor
   ✅ Aparece en alertas críticas
   ✅ Empleado ve que ya está revisado con nota automática
   ```

---

### Caso 2: Síntoma Moderado/Leve

1. **Empleado reporta síntoma** 👤
   ```
   POST /api/symptom-reports/
   { "symptom_type": "headache", "severity": "moderate" }
   ```

2. **Backend crea reporte** 📝
   ```
   ⏳ is_reviewed = false
   ⏳ Espera revisión del supervisor
   ```

3. **Frontend supervisor** 👔
   ```
   🔴 Badge rojo: "5" (pendientes)
   📋 Aparece en tabla de síntomas
   ```

4. **Supervisor revisa** ✅
   ```
   POST /api/symptom-reports/1/review/
   { "notes": "Toma descanso de 15 min" }
   ```

5. **Backend actualiza** ⚡
   ```
   ✅ is_reviewed = true
   ✅ reviewed_by = supervisor
   ✅ reviewed_at = now()
   ✅ notes guardadas
   ```

6. **Frontend empleado** 👤
   ```
   🟡 Badge amarillo: "1" (recientemente revisado)
   💬 Ve las notas del supervisor
   ```

---

## 📊 Endpoints Resumen

| Endpoint | Método | Quién | Función |
|----------|--------|-------|---------|
| `/api/symptom-reports/` | POST | Empleado | Reportar síntoma (auto-aprueba severos) |
| `/api/symptom-reports/pending-count/` | GET | Supervisor | Contar pendientes (badge rojo) |
| `/api/symptom-reports/pending/` | GET | Supervisor | Listar pendientes |
| `/api/symptom-reports/{id}/review/` | POST | Supervisor | Revisar síntoma |
| `/api/symptom-reports/my-reports/` | GET | Empleado | Mis síntomas |
| `/api/symptom-reports/recently-reviewed/` | GET | Empleado | Revisados últimas 24h (badge amarillo) |

---

## ✅ Checklist Implementación

### Backend ✅
- [x] Auto-aprobar síntomas severos
- [x] Generar alerta crítica en severos
- [x] Actualizar reviewed_at al revisar
- [x] Actualizar reviewed_by al revisar
- [x] Guardar notas del supervisor
- [x] Endpoint recently-reviewed
- [x] Documentación actualizada

### Frontend 📋
- [ ] Badge rojo supervisor (pendientes)
- [ ] Tabla de síntomas con botón revisar
- [ ] Modal para agregar notas al revisar
- [ ] Badge amarillo empleado (recientemente revisados)
- [ ] Página "Mis Síntomas" con notas del supervisor
- [ ] Polling ambos badges
- [ ] Event-driven updates

---

## 📦 Archivos Modificados

1. **`apps/analytics/serializers.py`**
   - Agregada auto-aprobación en `SymptomReportCreateSerializer.create()`

2. **`apps/analytics/views.py`**
   - Modificado `SymptomReportViewSet.review()` con notificación
   - Agregado `SymptomReportViewSet.recently_reviewed()` endpoint
   - **FIX:** Método `review()` con transacción atómica (commit inmediato)
   - **FIX:** Método `pending_count()` con query fresca (sin caché ORM)

3. **`DOCS/API_SINTOMAS.md`**
   - Agregada sección de funcionalidades automáticas
   - Documentado endpoint recently-reviewed
   - Actualizado servicio API

4. **`DOCS/FIX_PENDING_COUNT.md`** (NUEVO)
   - Documentación del fix para contador de pendientes
   - Explicación técnica del problema y solución

5. **`SCRIPTS/TEST/test_pending_count_update.py`** (NUEVO)
   - Script automático para probar actualización del contador
   - Verifica que el conteo disminuye correctamente después de revisar

---

## � FIX Aplicado (30/11/2025)

### Problema:
El endpoint `/api/symptom-reports/pending-count/` **no se actualizaba inmediatamente** después de revisar un síntoma.

### Solución Backend:
✅ **Método `review()`:**
- Transacción atómica con commit explícito
- `refresh_from_db()` después del save
- Garantiza que el cambio se persiste inmediatamente

✅ **Método `pending_count()`:**
- Query fresca desde `SymptomReport.objects.all()`
- Sin caché del ORM de Django
- Siempre devuelve el conteo real actual

### Solución Frontend (Ya Implementada):
✅ **Cálculo local desde datos cargados:**
- El contador se actualiza directamente desde `/pending/`
- No depende del endpoint `/pending-count/`
- Badge refleja la realidad inmediatamente

### Resultado:
✅ Ambos enfoques funcionan ahora:
- Backend: endpoint confiable con query fresca
- Frontend: actualización inmediata con datos locales

**Documentación:** `DOCS/FIX_PENDING_COUNT.md`  
**Script de prueba:** `SCRIPTS/TEST/test_pending_count_update.py`

---

## �🚀 Estado Final

✅ **Backend:** 100% COMPLETO  
✅ **Auto-aprobación severos:** Funcional  
✅ **Notificación empleado:** Datos disponibles  
✅ **Badges:** Endpoints listos  
✅ **Contador pendientes:** FIX aplicado (query fresca + transacción atómica)  
📋 **Frontend:** Listo para implementar  

**Tiempo estimado frontend:** 1-2 horas

---

**Fecha:** 30/11/2025  
**Feature:** Sistema de Síntomas Completo  
**Backend:** ✅ Listo  
**Frontend:** 📋 Documentado  
**Fix Contador:** ✅ Aplicado
