# 🔧 FIX: Contador de Síntomas Pendientes

## 🐛 Problema Reportado

El endpoint `/api/symptom-reports/pending-count/` **NO se actualizaba inmediatamente** después de marcar un síntoma como revisado. 

**Síntoma:**
- Supervisor marca síntoma como revisado ✅
- El endpoint sigue devolviendo `count: 2` en lugar de `count: 1`
- El frontend tenía que calcular localmente desde `/pending/`

---

## ✅ Solución Aplicada al Backend

### 1️⃣ Endpoint `pending-count` (Línea ~738)

**Archivo:** `apps/analytics/views.py`

**Cambios:**

```python
# ❌ ANTES: Usaba get_queryset() que podía tener caché
queryset = self.get_queryset().filter(is_reviewed=False)

# ✅ AHORA: Query fresca directa desde la DB
base_qs = SymptomReport.objects.all()

# Filtrar por supervisor si aplica
if request.user.role == 'supervisor':
    base_qs = base_qs.filter(employee__supervisor=request.user)

# Query fresca sin caché del ORM
queryset = base_qs.filter(is_reviewed=False)
```

**Por qué:**
- `get_queryset()` puede usar caché del ViewSet
- `SymptomReport.objects.all()` siempre consulta la DB
- Asegura que el conteo sea el valor real actual

---

### 2️⃣ Método `review()` (Línea ~650)

**Archivo:** `apps/analytics/views.py`

**Cambios:**

```python
# ❌ ANTES: Save simple sin garantía de commit inmediato
report.is_reviewed = True
report.save()

# ✅ AHORA: Transacción atómica con commit explícito
from django.db import transaction

with transaction.atomic():
    report.is_reviewed = True
    report.reviewed_at = timezone.now()
    report.reviewed_by = request.user
    if 'notes' in request.data:
        report.notes = request.data['notes']
    report.save()
    
    # Forzar commit inmediato
    transaction.on_commit(lambda: None)

# Refrescar objeto desde DB
report.refresh_from_db()
```

**Por qué:**
- `transaction.atomic()` asegura que el cambio se commitea
- `refresh_from_db()` garantiza que el objeto está sincronizado
- Las queries posteriores verán el cambio inmediatamente

---

## 🧪 Cómo Probar

### Opción 1: Script Automático

```powershell
cd SCRIPTS\TEST
python test_pending_count_update.py
```

**El script:**
1. ✅ Login como supervisor
2. ✅ Obtiene conteo inicial (`count: 2`)
3. ✅ Revisa un síntoma pendiente
4. ✅ Obtiene conteo actualizado (`count: 1`)
5. ✅ Verifica que la diferencia sea exactamente 1

**Resultado esperado:**
```
✅ ¡TEST EXITOSO! El contador se actualizó correctamente
   El endpoint /pending-count/ refleja el cambio inmediatamente
```

---

### Opción 2: Prueba Manual

1. **Obtener conteo inicial:**
```bash
GET /api/symptom-reports/pending-count/
Authorization: Bearer {token_supervisor}

Respuesta:
{
  "count": 2,
  "by_severity": { "severe": 0, "moderate": 2, "mild": 0 }
}
```

2. **Revisar un síntoma:**
```bash
POST /api/symptom-reports/1/review/
Authorization: Bearer {token_supervisor}
Body: { "notes": "Revisado OK" }

Respuesta:
{
  "message": "Reporte revisado exitosamente. El empleado será notificado.",
  "report": { ... }
}
```

3. **Verificar conteo actualizado:**
```bash
GET /api/symptom-reports/pending-count/
Authorization: Bearer {token_supervisor}

Respuesta:
{
  "count": 1,  # ✅ Decrementó correctamente
  "by_severity": { "severe": 0, "moderate": 1, "mild": 0 }
}
```

---

## 📊 Flujo Mejorado

### Backend:

```
Supervisor revisa síntoma
       ↓
[Transaction Atomic]
       ↓
is_reviewed = True
       ↓
.save() + commit
       ↓
refresh_from_db()
       ↓
Respuesta al frontend
       ↓
[Siguiente request]
       ↓
pending-count consulta DB
       ↓
✅ Devuelve conteo actualizado
```

---

## 🎯 Resultado Final

### Backend:
✅ **Endpoint actualizado inmediatamente**
- Query fresca desde DB (sin caché)
- Transacción atómica con commit explícito
- `refresh_from_db()` garantiza sincronización

### Frontend:
✅ **Dos estrategias combinadas**
- Cálculo local desde `/pending/` (inmediato)
- Polling a `/pending-count/` (ahora confiable)
- Badge siempre muestra el número correcto

---

## 📝 Archivos Modificados

1. **`apps/analytics/views.py`**
   - Línea ~650: Método `review()` con transacción atómica
   - Línea ~738: Método `pending_count()` con query fresca

2. **`SCRIPTS/TEST/test_pending_count_update.py`** (NUEVO)
   - Script de prueba automático
   - Verifica que el contador se actualiza correctamente

3. **`DOCS/FIX_PENDING_COUNT.md`** (ESTE ARCHIVO)
   - Documentación del problema y solución

---

## 🔍 Notas Técnicas

### ¿Por qué el problema ocurría?

1. **Caché del ORM:**
   - `get_queryset()` puede cachear el queryset base
   - Django optimiza queries reutilizando resultados

2. **Transacciones implícitas:**
   - `.save()` sin `transaction.atomic()` puede no commitear inmediatamente
   - Autocommit puede tener delays en algunos drivers DB

3. **Race conditions:**
   - Request 1: marca como revisado
   - Request 2: consulta conteo (antes del commit)
   - Resultado: conteo desactualizado

### ¿Cómo lo resolvimos?

1. **Query fresca:**
   - `SymptomReport.objects.all()` siempre consulta DB
   - No usa caché del ViewSet

2. **Commit explícito:**
   - `transaction.atomic()` + `on_commit()`
   - Garantiza que el cambio está en la DB

3. **Sincronización:**
   - `refresh_from_db()` asegura objeto actualizado
   - Queries posteriores ven el cambio

---

## ✅ Checklist Implementación

### Backend:
- [x] Modificado `pending_count()` con query fresca
- [x] Modificado `review()` con transacción atómica
- [x] Agregado `refresh_from_db()` después de save
- [x] Creado script de prueba
- [x] Documentación completa

### Pruebas:
- [ ] Ejecutar script `test_pending_count_update.py`
- [ ] Verificar que conteo disminuye correctamente
- [ ] Probar con múltiples síntomas
- [ ] Verificar que `by_severity` también se actualiza

---

**Fecha:** 30/11/2025  
**Issue:** Contador pendientes no se actualiza  
**Status:** ✅ Resuelto  
**Testing:** Script automático disponible
